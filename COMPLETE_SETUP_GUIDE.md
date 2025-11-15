# Complete Setup Guide - From Zero to Results

This is a **complete step-by-step guide** from the very beginning to running simulations and getting results.

---

## 🎯 Overview

This guide will take you through:
1. Initial setup (Docker, dependencies)
2. Data preparation (GTFS loading, passenger generation)
3. AI model training (clustering, forecasting)
4. Running simulations (baseline & dynamic)
5. Viewing results in notebook

**Total time:** ~2-3 hours (mostly waiting for simulations)

---

## 📋 Prerequisites

Before starting, make sure you have:
- ✅ **Docker Desktop** installed and running
- ✅ **Git** (optional, for cloning)
- ✅ **Terminal/PowerShell** access
- ✅ **Web browser** (for Jupyter/Streamlit)

---

## 🚀 Step-by-Step Setup

### **STEP 1: Start Docker Services**

Open your terminal in the project directory and run:

```bash
docker compose up -d
```

**What this does:**
- Starts PostgreSQL database with PostGIS
- Starts OSRM routing server
- Builds and starts web and Jupyter containers

**Verify it's running:**
```bash
docker compose ps
```

You should see 4 services running:
- `postgis_db` (database)
- `osrm_router` (routing)
- `streamlit_app` (web app)
- `jupyter_notebooks` (notebooks)

**Wait 30-60 seconds** for services to fully start.

---

### **STEP 2: Load GTFS Data into Database**

This loads your bus schedule data:

```bash
docker compose run --rm web python src/data/load_data.py
```

**Expected output:**
```
Database engine created.
Processing stops.txt -> table 'stops'...
Successfully loaded stops.
...
Converting 'stops' table to geospatial table 'stops_geospatial'...
Successfully created 'stops_geospatial' table.
All GTFS data loaded successfully.
```

**Time:** 1-5 minutes

**If you get errors:**
- Make sure `data/raw/delhi-bus.zip` exists
- Check Docker is running: `docker compose ps`

---

### **STEP 3: Generate Passenger Demand Data**

This creates 1.56 million passenger requests:

```bash
docker compose run --rm web python src/data/generate_passengers.py
```

**Expected output:**
```
Saved passenger demand to data/raw/passenger_demand.csv (1560000 rows)
```

**Time:** 1-2 minutes

**File created:** `data/raw/passenger_demand.csv`

---

### **STEP 4: Run Clustering (Find Hotspots)**

This groups bus stops into 10 clusters based on demand:

```bash
docker compose run --rm web python src/models/cluster.py
```

**Expected output:**
```
Clustered 6342 stops into 10 clusters.
   Wrote assignments to data/raw/stop_clusters.csv and model to models_artifacts/kmeans_model.pkl.
```

**Time:** 30 seconds - 2 minutes

**Files created:**
- `data/raw/stop_clusters.csv`
- `models_artifacts/kmeans_model.pkl`

---

### **STEP 5: Train Forecasting Models**

This trains 10 Prophet models (one per cluster) for demand prediction:

```bash
docker compose run --rm web python src/models/forecast.py
```

**Expected output:**
```
Saved model for cluster 0 to models_artifacts/forecast_models/prophet_model_cluster_0.pkl
Saved model for cluster 1 to models_artifacts/forecast_models/prophet_model_cluster_1.pkl
...
Saved model for cluster 9 to models_artifacts/forecast_models/prophet_model_cluster_9.pkl
```

**Time:** 5-15 minutes (Prophet models take time to train)

**Files created:**
- `models_artifacts/forecast_models/prophet_model_cluster_0.pkl` through `prophet_model_cluster_9.pkl`

---

### **STEP 6: Run Baseline Simulation**

This simulates the **current static schedule** (your "before" picture):

```bash
docker compose run --rm web python src/simulation/baseline_sim.py
```

**Expected output:**
```
Loading static GTFS schedule...
...Schedule loaded.
--- Running Baseline (Static Schedule) Simulation for 1,560,000 passengers ---

=== Baseline Simulation Summary ===
Average Wait Time (minutes): XX.XX
Total Cost (₹): XX,XXX,XXX.XX
Total KMs Driven: 645,000
Passengers Served: X,XXX,XXX
Passengers Failed: XX,XXX
Cost per Passenger (₹): XX.XX

💾 Results saved to: data/processed/baseline_simulation_results.json
```

**Time:** 10-30 minutes (depends on your system)

**File created:** `data/processed/baseline_simulation_results.json`

**What it does:**
- Simulates 1.56M passengers using the fixed GTFS schedule
- Calculates wait times, costs, and efficiency
- Saves results automatically

---

### **STEP 7: Run Dynamic Simulation**

This simulates the **AI-driven dynamic schedule** (your "after" picture):

```bash
docker compose run --rm web python src/simulation/dynamic_sim.py
```

**Expected output:**
```
--- Running Dynamic (AI-Driven) Simulation for 1,560,000 passengers ---

=== Dynamic Simulation Summary ===
Average Wait Time (minutes): XX.XX
Total Cost (₹): XX,XXX,XXX.XX
Total KMs Driven: XXX,XXX.XX
Passengers Served: X,XXX,XXX
Passengers Failed: XX,XXX
Cost per Passenger (₹): XX.XX

💾 Results saved to: data/processed/dynamic_simulation_results.json
```

**Time:** 15-45 minutes (longer because it uses AI forecasting)

**File created:** `data/processed/dynamic_simulation_results.json`

**What it does:**
- Uses Prophet models to forecast demand
- Dispatches buses proactively based on forecasts
- Adapts to real-time queue lengths
- Saves results automatically

---

### **STEP 8: View Results in Jupyter Notebook**

1. **Open Jupyter Lab:**
   - Go to: **http://localhost:8888**
   - You should see the Jupyter interface

2. **Open the notebook:**
   - Click on `01_data_analysis.ipynb`

3. **Run all cells up to Cell 17:**
   - This loads data and sets up the environment
   - Use: **Run → Run All Cells** (or run cells one by one)

4. **Run Cell 18 (Load Comparison Data):**
   - This cell will **automatically detect** your JSON result files
   - Loads both baseline and dynamic results
   - Populates the comparison table
   - **No manual copying needed!**

   **Expected output:**
   ```
   ✅ Loading results from saved JSON files...

   📊 Baseline results loaded (from 2024-11-14T...)
      Sample size: 1,560,000 passengers

   📊 Dynamic results loaded (from 2024-11-14T...)
      Sample size: 1,560,000 passengers

   ✅ Results automatically loaded! No manual entry needed.
   ```

5. **Run Cell 19 (Visualization):**
   - Shows side-by-side comparison charts
   - Displays improvement percentages
   - Creates beautiful visualizations

---

## 📊 What You'll See in Results

After running both simulations, the notebook will show:

| Metric | Baseline (Static) | Dynamic (AI) | Improvement |
|--------|------------------|--------------|-------------|
| Average Wait Time | ~15-20 min | ~8-12 min | ⬇️ 30-50% |
| Total Cost | ~₹75M | ~₹65M | ⬇️ 10-20% |
| Passengers Failed | ~60K | ~20K | ⬇️ 40-60% |
| Cost per Passenger | ~₹50 | ~₹42 | ⬇️ 15-25% |

---

## 🔍 Quick Verification Checklist

After each step, verify:

- [ ] **Step 2:** Database has tables (check with `docker compose exec db psql -U user -d gtfs_db -c "\dt"`)
- [ ] **Step 3:** File exists: `data/raw/passenger_demand.csv` (1.56M rows)
- [ ] **Step 4:** Files exist: `data/raw/stop_clusters.csv` and `models_artifacts/kmeans_model.pkl`
- [ ] **Step 5:** 10 files exist: `models_artifacts/forecast_models/prophet_model_cluster_*.pkl`
- [ ] **Step 6:** File exists: `data/processed/baseline_simulation_results.json`
- [ ] **Step 7:** File exists: `data/processed/dynamic_simulation_results.json`
data/
├── raw/
│   ├── delhi-bus.zip (your GTFS data)
│   ├── passenger_demand.csv (1.56M passengers)
│   └── stop_clusters.csv (stop assignments)
└── processed/
   ├── baseline_simulation_results.json ✅
   └── dynamic_simulation_results.json ✅

models_artifacts/
├── kmeans_model.pkl (clustering model)
└── forecast_models/
   ├── prophet_model_cluster_0.pkl
   ├── prophet_model_cluster_1.pkl
   └── ... (10 total models)

## 🐛 Troubleshooting

### Problem: "Docker not running"
**Solution:** Start Docker Desktop, wait for it to fully start, then retry.

### Problem: "Port already in use"
**Solution:** 
- Check what's using the port: `netstat -ano | findstr :8501` (Windows)
- Stop the conflicting service or change ports in `docker-compose.yml`

### Problem: "Passenger file not found"
**Solution:** Make sure you completed Step 3 (generate passengers).

### Problem: "Missing model file"
**Solution:** Make sure you completed Step 5 (train forecasting models).

### Problem: "Simulation taking forever"
**Solution:** 
- This is normal! Full simulations take 10-45 minutes
- Use sample mode for quick testing
- Or run overnight

### Problem: "JSON files not loading in notebook"
**Solution:**
1. Check files exist: 
   - Windows PowerShell: `Get-ChildItem data/processed/*.json`
   - Windows CMD: `dir data\processed\*.json`
   - Linux/Mac: `ls -lh data/processed/*.json`
2. Restart Jupyter kernel: **Kernel → Restart Kernel**
3. Re-run Cell 18

---

## 📁 Files Created During Setup

After completing all steps, you'll have:

```
data/
├── raw/
│   ├── delhi-bus.zip (your GTFS data)
│   ├── passenger_demand.csv (1.56M passengers)
│   └── stop_clusters.csv (stop assignments)
└── processed/
    ├── baseline_simulation_results.json ✅
    └── dynamic_simulation_results.json ✅

models/
├── kmeans_model.pkl (clustering model)
└── forecast_models/
    ├── prophet_model_cluster_0.pkl
    ├── prophet_model_cluster_1.pkl
    └── ... (10 total models)
```

---

## 🎓 Understanding the Results

### Baseline (Static) Simulation:
- Uses the **fixed GTFS schedule** (same every day)
- Passengers wait for the next scheduled bus
- Higher wait times, fixed costs
- Represents **current system**

### Dynamic (AI) Simulation:
- Uses **Prophet forecasts** to predict demand
- Dispatches buses **proactively** before queues form
- Adapts to **real-time** passenger queues
- Lower wait times, optimized costs
- Represents **your AI system**

### The Comparison:
Shows how much better your AI system performs compared to the static schedule.

---

## 🚀 Next Steps After Getting Results

1. **Analyze the comparison** in the notebook
2. **Export visualizations** for your research paper
3. **Document findings** in your report
4. **Run multiple times** to verify consistency
5. **Experiment** with different parameters

---

## 📝 Complete Command Sequence

Here's the complete sequence in one place:

```bash
# 1. Start services
docker compose up -d

# 2. Load GTFS data
docker compose run --rm web python src/data/load_data.py

# 3. Generate passengers
docker compose run --rm web python src/data/generate_passengers.py

# 4. Run clustering
docker compose run --rm web python src/models/cluster.py

# 5. Train forecasting models
docker compose run --rm web python src/models/forecast.py

# 6. Run baseline simulation
docker compose run --rm web python src/simulation/baseline_sim.py

# 7. Run dynamic simulation
docker compose run --rm web python src/simulation/dynamic_sim.py

# 8. Open Jupyter: http://localhost:8888
# 9. Open notebook and run Cell 18 & 19
```

---

## ✅ Success Indicators

You've successfully completed everything when:

1. ✅ Both JSON result files exist in `data/processed/`
2. ✅ Notebook Cell 18 loads results automatically
3. ✅ Notebook Cell 19 shows comparison charts
4. ✅ You can see improvement percentages
5. ✅ All visualizations display correctly

---

**That's the complete guide from zero to results!** 🎉

Follow these steps in order, and you'll have everything working. If you get stuck at any step, check the troubleshooting section or the error messages for guidance.

