# Citizen Environmental Tracker

The Citizen Environmental Tracker is a platform for collecting, storing, and exploring environmental data from citizen science projects. It provides a complete end-to-end solution for ingesting data from sources like iNaturalist (for biodiversity observations) and OpenAQ (for air quality measurements), and exposing it through a web interface and a REST API.

This project is built with a microservices architecture and is fully containerized with Docker, making it easy to deploy and scale.

![Project Architecture Diagram](https://i.imgur.com/your-architecture-diagram.png) 
*Note: You can create and link to an architecture diagram here.*

## Features

- **Microservices Architecture**: Each component of the system is an independent service, promoting scalability and maintainability.
- **Data Ingestion Pipeline**: Automatically fetches data from external sources (iNaturalist, OpenAQ), processes it, and stores it.
- **REST API**: A robust API built with FastAPI allows for querying the collected environmental data with filtering and pagination.
- **Web Interface**: A simple, static frontend to visualize the data.
- **Asynchronous Processing**: Uses RabbitMQ as a message queue to handle data ingestion and validation without blocking the system.
- **Observability**: Comes with a pre-configured stack for monitoring, including Prometheus for metrics and Grafana for dashboards.
- **CI/CD Ready**: Includes configuration for Jenkins and SonarQube for automated testing and code quality analysis.

## Technology Stack

- **Backend**: Python, FastAPI
- **Frontend**: HTML, JavaScript, CSS
- **Database**: PostgreSQL
- **Message Queue**: RabbitMQ
- **Object Storage**: MinIO (S3-compatible)
- **Reverse Proxy**: Traefik
- **Containerization**: Docker & Docker Compose
- **Observability**: Prometheus, Grafana, Alertmanager
- **CI/CD**: Jenkins, SonarQube

## Architecture Overview

The application is composed of several services that work together:

1.  **Data Ingestor**: Periodically fetches data from iNaturalist and OpenAQ, stores the raw files in the MinIO bucket, and sends a message to the RabbitMQ queue.
2.  **Validation Worker**: Listens for messages on the queue, retrieves the raw data file from MinIO, validates and normalizes the data, and inserts it into the PostgreSQL database.
3.  **Submission API**: Provides REST endpoints (e.g., `/api/measurements`, `/api/observations`) for clients to query the data stored in the database.
4.  **Frontend**: A static web application that provides a user interface for viewing the data.
5.  **Traefik Gateway**: Acts as a reverse proxy, routing incoming traffic to the appropriate service (Frontend or API). It also handles API authentication and rate limiting.
6.  **DB Maint**: A maintenance service that performs periodic tasks on the database, such as refreshing materialized views.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Getting Started

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Shreeya0704/citizen-environmental-tracker.git
    cd citizen-environmental-tracker
    ```

2.  **Configure the environment:**
    Copy the example environment file.
    ```bash
    cp .env.example .env
    ```
    Open the `.env` file in a text editor and modify the variables as needed, especially the passwords and ports.

3.  **Set up API Authentication:**
    The API is protected by Basic Authentication. You need to generate a hashed password for the user.
    
    First, set the `TRAEFIK_BASIC_USER` and `TRAEFIK_BASIC_PASS` variables in your `.env` file. Then, run the following command to generate the hash:
    ```bash
    docker run --rm httpd:2.4-alpine sh -lc 'htpasswd -nbB "$TRAEFIK_BASIC_USER" "$TRAEFIK_BASIC_PASS"'
    ```
    This will output something like `user:$apr1$....`. Copy the entire string and paste it as the value for `TRAEFIK_BASIC_AUTH_USERS` in your `.env` file.

4.  **Build and run the application:**
    The provided `Makefile` simplifies project management. To build and start all the services in the background, run:
    ```bash
    make up
    ```

5.  **Access the application:**
    Once the containers are running, you can access the different parts of the system:
    - **Frontend**: `http://localhost:${GATEWAY_PORT}/`
    - **API** (requires BasicAuth): `http://localhost:${GATEWAY_PORT}/api/healthz`
    - **Traefik Dashboard**: `http://localhost:${TRAEFIK_DASHBOARD_PORT}/`
    - **Prometheus**: `http://127.0.0.1:${PROMETHEUS_PORT}/`
    - **Grafana**: `http://127.0.0.1:${GRAFANA_PORT}/`

    *(Note: Port numbers are configured in your `.env` file.)*

## Makefile Commands

The following commands are available to manage the application stack:

- `make up`: Build and start all services.
- `make down`: Stop all services.
- `make status`: Show the status of running containers.
- `make logs`: Tail the logs from all running services.
- `make refresh`: Manually trigger a database maintenance refresh.
- `make nuke`: **DANGEROUS!** Stop all services and permanently delete all data volumes (database, MinIO storage, etc.).
- `make ci-up`: Start the CI services (Jenkins, SonarQube).
- `make ci-down`: Stop the CI services.