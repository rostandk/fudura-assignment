#  Time‑Series Assignment by Rostand - Fudura Monitoring & Control

This repository contains a reference implementation of a time‑series data pipeline designed for battery telemetry, optimized for quick alerting, storage efficiency, and historical analysis.

<h3>Final Tables</h3>

<div style="display: flex; gap: 10px; align-items: flex-start;">
  <div style="flex: 1; text-align: center;">
    <img src="battery_telemetry.png" alt="Table battery_telemetry" width="600"/>
  </div>
  <div style="flex: 1; text-align: center;">
    <img src="daily_soc_min.png" alt="Table daily_soc_min" width="600"/>
  </div>
</div>


## Getting Started

Follow these steps to get the project up and running:

0. **Dependencies**  
- You must have Python3 and recent version of Docker Desktop.
- You can optionally install a database client like PgAdmin.
- PgAdmin is optional because you can run queries using: docker exec -it timescaledb (see step 8).


1. **Clone the repository**  
   ```bash
   git clone https://github.com/rostandk/fudura_assigment.git
   cd fudura_assigment
   ```

2. **Create a Python virtual environment**  
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Configure environment (optional)**  
   Copy the example environment file and edit as needed:
   ```bash
   cp .env.example .env
   # Then open .env and set:
   # DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fudura_monitoring
   ```

4. **Start TimescaleDB via Docker Compose**  
   ```bash
   docker compose up -d
   ```
   This will launch a TimescaleDB container on port 5432.

5. **Install Python dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

6. **Initialize the database schema**  
   ```bash
   python setup_database.py
   ```
   This script will create the hypertable, enable compression, add the compression policy, and create a continuous aggregate for daily SOC minima.

7. **Load telemetry data**  
   ```bash
   python main.py
   ```
   This will read JSON files from `data/assets` and `data/telemetry`, transform them, and insert into the `battery_telemetry` table.

8. **Verify data in the database**  
   ```bash
   docker exec -it timescaledb \
     psql -U postgres -d fudura_monitoring \
     -c "SELECT * FROM battery_telemetry;"
   ```
   Use this to confirm that telemetry rows have been inserted.


## Database Design

### 1.1 Narrow Table Layout  
We store every metric reading as a separate row in a single table:

```sql
CREATE TABLE battery_telemetry (
  recorded_at   TIMESTAMPTZ      NOT NULL,
  device_id     UUID             NOT NULL,
  metric_name   TEXT             NOT NULL,
  value         DOUBLE PRECISION NOT NULL,
  PRIMARY KEY (recorded_at, device_id, metric_name)
);
```
- **Flexibility**: New metrics don’t require schema changes—just new `metric_name` values.  
- **Efficiency**: Avoids sparsity and leverages columnar compression on the numeric `value` field.

### 1.2 Hypertable Partitioning  
We convert the table into a TimescaleDB hypertable:

```sql
SELECT create_hypertable(
  'battery_telemetry',
  'recorded_at',
  partitioning_column => 'device_id',
  number_partitions   => 4,
  if_not_exists       => TRUE
);
```
- **Time partitioning** improves performance for range queries on `recorded_at`.  
- **Space partitioning** (by `device_id`) shards data for parallelism and smaller chunk sizes.

### 1.3 Compression for Storage Efficiency

```sql
ALTER TABLE battery_telemetry
  SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'device_id, metric_name'
  );

-- Compress chunks older than X days
DO $$
BEGIN
  PERFORM add_compression_policy('battery_telemetry', INTERVAL '7 days');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END
$$;
```
- **Automatic compression** reduces disk usage by up to 90%+ on numeric time‑series data.  
- **Segment‑by policy** groups similar device/metric data for optimal compression ratios.

### 1.4. Quick Alerting

To detect low battery states (e.g., state of charge < 20%), an external alerting system can run:

```sql
SELECT recorded_at, device_id, value
FROM battery_telemetry
WHERE metric_name = 'StateOfChargePercentage'
  AND value < 20
  AND recorded_at > NOW() - INTERVAL '2 seconds';
```
The hypertable’s time and space partitioning ensures this query touches only recent, relevant chunks for sub‑second response times.

### 1.5. Storage Efficiency

- **Chunk compression** automatically handles older data, freeing up storage and I/O.  
- **No manual intervention** needed after initial setup—TimescaleDB’s policy scheduler handles data lifecycle.


### 1.6 Continuous Aggregates for historical analyses
- Raw data at full granularity remains available for detailed queries (e.g., per‑minute SOC trends). 
- To accelerate common reports, we precompute aggregates below.
- Create a materialized view for daily minimum state‑of‑charge to track degradation:

```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_soc_min
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 day', recorded_at) AS day,
  device_id,
  MIN(value) AS min_soc
FROM battery_telemetry
WHERE metric_name = 'StateOfChargePercentage'
GROUP BY day, device_id;
```
- **Automatic refresh**: TimescaleDB keeps the view up to date, enabling fast historical queries on battery degradation.  
- **Extendable**: Additional continuous aggregates (e.g., max power, average export) can be defined similarly.


## Stream Processing vs Near Real-Time Querying for sub-second alerting system:

### Overview

- This document compares two different approaches for alerting when a battery's State of Charge (SoC) drops below 20%. 
- The two approaches are: Stream Processing using frameworks like Kafka Streams or Flink, and Near Real-Time Querying of TimescaleDB.

![Stream Processing vs Near Real-Time Querying](compare.png)


### Approach 1: Stream Processing (e.g., Kafka Streams, Flink, Spark Streaming)

- Data is sent from batteries to a message queue (with a Kafka like API).
- A stream processing application reads messages as they arrive from the queue.
- The application processes each message (or small micro-batches) in memory.
- If a message contains `metric_name = 'StateOfChargePercentage'` and `value < 20`, the stream processor immediately triggers an alert (e.g., calls an alerting API, sends a notification).
- The processed data (or raw data) is then written to the database TimescaleDB for storage and historical analysis.

### Approach 2: Near Real-Time Querying on TimescaleDB

- Data is sent from batteries directly (or via a simple collector) and inserted into the TimescaleDB `battery_telemetry` hypertable.
- An external alerting system (e.g., Grafana Alerting, Prometheus Alertmanager with an exporter, or a custom script/service) is configured to run a specific SQL query against TimescaleDB very frequently (e.g., every second or even slightly faster).
- The query is optimized to check only the most recent data:

```sql
SELECT device_id, recorded_at, value
FROM battery_telemetry
WHERE metric_name = 'StateOfChargePercentage'
  AND value < 20
  AND recorded_at > NOW() - INTERVAL '2 seconds'; -- Check data arrived very recently
```

### Recommendations: Near Real-Time Querying on TimescaleDB vs Stream Processing

- Stream processing will likely offers lower latency (sub-millisecond). 
- It does come with the complexity overhead that is likely not justified solely at an early stage of the project and for this specific, simple, 1-second threshold alert. 
- The near real-time querying approach provides a good balance of performance and simplicity for this use case. 
- If the project evolves in term of scale, more complex logic, or sub-millisecond latency demands, then stream processing would become a stronger contender.