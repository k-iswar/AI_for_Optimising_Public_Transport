# AI Public Transport Optimization System

This project implements an AI-powered public transport optimization system using GTFS (General Transit Feed Specification) data, featuring demand clustering, flow forecasting, and route optimization.

## Project Structure

```
ai_transport_project/
├── .venv/                  # Virtual environment files (will be created)
├── data/
│   ├── raw/                # Raw GTFS zip files
│   └── processed/          # Cleaned or intermediate data
├── notebooks/              # Jupyter notebooks for exploration and analysis
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   └── load_data.py    # Scripts for data ingestion and preprocessing
│   ├── models/
│   │   ├── __init__.py
│   │   ├── cluster.py      # K-Means clustering model
│   │   ├── forecast.py     # ARIMA forecasting model
│   │   └── optimize.py     # NetworkX graph optimization
│   └── app.py              # The Streamlit web application
├── tests/                  # Unit and integration tests
├── .dockerignore           # Files to ignore in Docker context
├── .gitignore              # Files to ignore for Git
├── docker-compose.yml      # Docker configuration for services
├── Dockerfile              # Docker configuration for the web app
└── requirements.txt        # Python package dependencies
```

## Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose
- A GTFS feed from a transit agency

## Setup Instructions

### Step 1: Create Virtual Environment

**On Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Download GTFS Data

1. Download a GTFS zip file from a transit agency (e.g., from [GTFS Data Exchange](https://www.gtfs-data-exchange.com/))
2. Place the zip file in the `data/raw/` directory
3. Update the `GTFS_ZIP_PATH` in `src/data/load_data.py` with your file name

### Step 4: Start the Database

```bash
docker compose up -d
```

This will start a PostgreSQL database with PostGIS extension running on port 5432.

### Step 5: Load GTFS Data into Database

```bash
python src/data/load_data.py
```

### Step 6: Run the Application

```bash
docker compose up --build
```

This will build and start both the database and web application containers.

### Step 7: Access the Application

Open your web browser and navigate to: http://localhost:8501

## Features

1. **Demand Clustering**: K-Means clustering to identify high-demand zones
2. **Flow Forecasting**: ARIMA model for predicting passenger flow
3. **Route Optimization**: NetworkX-based shortest path algorithm using Dijkstra's algorithm

## Database Configuration

Default database credentials:
- Host: localhost
- Port: 5432
- Database: gtfs_db
- Username: user
- Password: password

**Note**: Change these credentials in production environments!

## Troubleshooting

- If Docker containers fail to start, ensure Docker is running and ports 5432 and 8501 are not in use
- If the database connection fails, wait a few seconds for the database container to fully initialize
- Check Docker logs: `docker compose logs`

## License

This project is for educational purposes.

