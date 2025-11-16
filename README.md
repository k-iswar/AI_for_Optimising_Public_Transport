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

**Example for Delhi:**
- Download from: http://www.delhimetrorail.com/opencms/opencms/en/
- Or use the sample data provided in `data/raw/`

### Step 4: Set Up OSRM Routing Data (Optional)

OSRM (Open Source Routing Machine) is used for route optimization. If using dynamic scheduling features:

1. Download OpenStreetMap data for your region:
   - Visit [Geofabrik](https://www.geofabrik.de/) to download `.osm.pbf` files
   - For Delhi: `delhi-latest.osm.pbf`
   - Place in `osrm-data/` directory

2. Process the data (using Docker):
   ```bash
   docker compose run --rm osrm osrm-extract -p /osrm/profiles/car.lua /osrm/osrm-data/delhi-latest.osm.pbf
   docker compose run --rm osrm osrm-partition /osrm/osrm-data/delhi-latest.osm
   docker compose run --rm osrm osrm-customize /osrm/osrm-data/delhi-latest.osm
   ```

3. The processed files will be in `osrm-data/` and ready to use

**Note:** Generated OSRM files (`*.osm*`) are excluded from Git and regenerated locally as needed to reduce repo size.

### Step 5: Start the Database

```bash
docker compose up -d
```

This will start a PostgreSQL database with PostGIS extension running on port 5432.

### Step 6: Load GTFS Data into Database

```bash
python src/data/load_data.py
```

### Step 7: Run the Application

```bash
docker compose up --build
```

This will build and start both the database and web application containers.

### Step 8: Access the Application

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

## Generated Files (Not in Git)

To keep the repository small and clean, the following generated files are **excluded from Git** and stored locally only:

- `data/processed/`: Processed data and simulation results
- `models_artifacts/forecast_models/`: Trained Prophet forecasting models
- `osrm-data/*.osrm*`: OSRM routing engine data files

**These files are regenerated automatically when you:**
1. Run model training scripts (`src/models/forecast.py`, `src/models/cluster.py`)
2. Run simulations (`src/simulation/baseline_sim.py`, `src/simulation/dynamic_sim.py`)
3. Initialize OSRM data (see Step 4 above)

All these files are in `.gitignore` and won't be pushed to GitHub, keeping the repo size minimal while allowing local development.

## Troubleshooting

- If Docker containers fail to start, ensure Docker is running and ports 5432 and 8501 are not in use
- If the database connection fails, wait a few seconds for the database container to fully initialize
- Check Docker logs: `docker compose logs`
- If OSRM data files are missing, re-run the Step 4 setup commands above

## License

This project is for educational purposes.

