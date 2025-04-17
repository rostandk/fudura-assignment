# Time-Series Data Modeling assignment

This repository contains an assignment for candidates applying for a Data Platform Engineering role in the Monitoring &
Control team at Fudura. The repository should only contain data samples and a README file to instruct the candidate.

## Background

The Monitoring & Control team at Fudura is responsible for the data platform that collects, stores, and facilitates
visualization of data from various energy assets, such as solar panels, batteries, and EV charging stations.

This assignment does not focus on data collection from real APIs. Realistic data mimicking an actual battery vendor of Fudura is provided in the `data` folder.
Focus your efforts on the tranfsormation and modeling of the data. 

## Objective

Design and implement a schema to store battery sensor data into a time-series database structure. 
Implement the transformation to your target schema.
Assume that a well-known time-series database is used for storage, such as TimescaleDB or InfluxDB.

## Requirements

Write your code in Python, and come up with a data model that optimizes for:

* Quick alerting on battery metrics; i.e. state of charge < 20% (via an external alerting system that executes queries
  periodically)
* Storage efficiency
* Historical analyses, such as battery degradation

## Implementation

Set up a repository that:

* Contains a file that defines code dependencies
* Shows how you would structure the code
* Contains a README file, concerning what you think is relevant

Implement the following features:

* Load the provided JSON
    * As actual API interaction is out of scope for this assignment, imagine that the directory structure mimics a
      REST API. The JSON files are the response of a GET request to the API.
    * All available assets can be found under `data/assets/`
    * Telemetry for each asset can be found under `data/telemetry/`
* Transform it to your proposed model
* Write the data to a table called `battery_telemetry` in TimescaleDB

When writing code, write if you would be working in a production environment, so think of relevant aspects that should be part of every codebase. (If you run out of time, document remaining tasks in your readme).
It's not necessary to set up CI/CD or write IaC.

## Evaluation

In total, you have 2 hours to complete this assignment. After the 2 hours, we will discuss your implementation and
design.
