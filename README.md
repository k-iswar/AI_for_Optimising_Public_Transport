# AI for Public Transport Optimization System

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
│   │   ├── forecast.py     # Prophet forecasting model
│   │   └── optimize.py     # NetworkX graph optimization
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── baseline_sim.py # Baseline (static) simulation
│   │   └── dynamic_sim.py  # Dynamic (AI-driven) simulation
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
docker compose run --rm web python src/data/load_data.py
```

### Step 6: Generate Passenger Demand Data

```bash
docker compose run --rm web python src/data/generate_passengers.py
```

### Step 7: Run Clustering

```bash
docker compose run --rm web python src/models/cluster.py
```

### Step 8: Train Forecasting Models

```bash
docker compose run --rm web python src/models/forecast.py
```

### Step 9: Run Simulations (Optional)

```bash
# Baseline (static) simulation
docker compose run --rm web python src/simulation/baseline_sim.py

# Dynamic (AI-driven) simulation
docker compose run --rm web python src/simulation/dynamic_sim.py
```

### Step 10: Run the Application

```bash
docker compose up --build
```

This will build and start the database, OSRM router, web application, and Jupyter Lab.

### Step 11: Access the Services

- **Streamlit App**: http://localhost:8501
- **Jupyter Lab**: http://localhost:8888

## Features

1. **Demand Clustering**: K-Means clustering to identify high-demand zones (10 clusters)
2. **Flow Forecasting**: Prophet time-series model for predicting passenger demand with seasonality and holidays
3. **Route Optimization**: NetworkX-based shortest path algorithm using Dijkstra's algorithm
4. **Simulation Framework**: 
   - Baseline simulation (static schedule)
   - Dynamic simulation (AI-driven adaptive scheduling)
   - Performance comparison (wait times, costs, efficiency)
5. **Data Visualization**: Jupyter notebooks for analysis and comparison

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

