# AI-Driven Database Workload Generator & Runner

A system that leverages AI to generate diverse SQL queries for database testing and observability. This project simulates real-world ad hoc and steady-state database workloads by continuously generating and executing SQL queries on a PostgreSQL database. The system is fully containerized using Docker Compose and integrates with the TIG stack (Telegraf, InfluxDB, Grafana) for comprehensive observability and monitoring.

## Project Goals

- **Automated Query Generation:**  
  Use a language model (via OpenAI’s API) to generate a wide variety of SQL queries based on a user-defined goal and a dynamically discovered database schema.

- **Realistic Workload Simulation:**  
  Emulate real-world database usage by combining continuous ad hoc queries with steady-state queries (e.g., for anomaly detection or continuous reporting).

- **Observability:**  
  Integrate with the TIG stack to collect and visualize both container and application metrics, making it easier to monitor performance and debug issues.

- **Containerization & Orchestration:**  
  Deploy the entire application—including the observability stack—using Docker Compose, enabling simple build, deployment, and scaling.

## Components Overview

- **Agent (AI Query Generator):**  
  Uses OpenAI’s API to generate diverse PostgreSQL queries based on the discovered database schema and a specified goal. Each generated query is logged as an individual SQL file and placed onto a shared queue.

- **Workload (Query Runner):**  
  Consumes queries from the shared queue and executes them concurrently against the PostgreSQL database. It also runs a steady-state workload in parallel to simulate continuous reporting or monitoring scenarios.

- **Queue Manager:**  
  Provides a shared queue (a wrapper over a multiprocessing queue) and a query message class to encapsulate SQL queries along with descriptive comments, facilitating inter-process communication between the generator and runner.

- **Utilities:**  
  Contains helper functions for configuration loading and structured logging setup. Logging is configured to output detailed, structured messages to both the console and log files for easy debugging.

- **Observability & Logging:**  
  The project uses Python’s logging module configured with a structured formatter that records timestamps, log levels, module names, process names, and messages. In addition, the TIG stack (Telegraf, InfluxDB, Grafana) collects and visualizes metrics from the application and its Docker containers.

## Building & Running with Docker Compose

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Setup Instructions

1. **Update Configuration:**
   - Edit `config.json` to set your PostgreSQL connection details. (If you’re using a containerized Postgres instance, ensure the host is set accordingly.)
   - Set your OpenAI API key by replacing `YOUR_OPENAI_API_KEY` in the `docker-compose.yml` file (in the environment section for the `app` service) and in your code as needed (ideally through environment variables).

2. **Build & Start the Services:**
   From the project root, run:
   ```bash
   docker-compose up --build
   ```
   This command will:
   - Build the `app` container from the provided Dockerfile.
   - Launch the following services:
     - **app:** Runs the AI-driven query generator and query runner.
     - **influxdb:** Stores metrics from Telegraf.
     - **telegraf:** Collects Docker and application metrics and forwards them to InfluxDB.
     - **grafana:** Provides dashboards for visualizing metrics (accessible at [http://localhost:3000](http://localhost:3000)).
   - (Optionally, you can enable the Postgres container if desired by uncommenting its section in `docker-compose.yml`.)

3. **Access Grafana:**
   - Open your browser and navigate to [http://localhost:3000](http://localhost:3000).
   - Configure an InfluxDB data source with the URL `http://influxdb:8086`.
   - Create dashboards to visualize container and application metrics.

4. **Stopping the Services:**
   To stop and remove all running containers, run:
   ```bash
   docker-compose down
   ```

## Observability & Logging

- **Structured Logging:**  
  The application uses Python’s logging module with a structured formatter that outputs detailed logs—including timestamps, log levels, module names, and process names—to both the console and log files:
  - `logs/app.log` for overall application events.
  - `logs/runner/query_runner.log` for detailed query execution logs.

- **TIG Stack Integration:**  
  - **Telegraf:** Configured via `telegraf.conf` to collect container-level metrics using Docker input plugins and send them to InfluxDB.
  - **InfluxDB:** Stores the collected metrics.
  - **Grafana:** Connects to InfluxDB to visualize performance metrics through customizable dashboards.

