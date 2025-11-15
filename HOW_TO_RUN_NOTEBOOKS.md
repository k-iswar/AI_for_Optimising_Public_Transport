# 📓 How to Run Jupyter Notebooks

This guide explains how to access and run the Jupyter notebooks for data analysis and visualization.

---

## 🚀 Quick Start

### Step 1: Start Jupyter Service

Make sure Docker is running, then start the Jupyter service:

```powershell
# Start all services (including Jupyter)
docker compose up -d

# Or start only Jupyter (if other services are already running)
docker compose up -d jupyter
```

### Step 2: Access Jupyter Lab

Open your web browser and go to:

```
http://localhost:8888
```

**Note:** The Jupyter service is configured with **no password** for easy access (development only).

### Step 3: Open the Notebook

1. In Jupyter Lab, you'll see the file browser on the left
2. Click on `01_data_analysis.ipynb` to open it
3. The notebook will load with all cells visible

---

## 📝 Running Notebook Cells

### Method 1: Run Individual Cells

1. **Click on a cell** to select it
2. **Press `Shift + Enter`** to run the cell and move to the next one
3. **Press `Ctrl + Enter`** to run the cell without moving to the next

### Method 2: Run All Cells

1. Go to **Run** menu → **Run All Cells**
2. Or use keyboard shortcut: **`Ctrl + Shift + Enter`** (may vary)

### Method 3: Run from Top

1. Go to **Run** menu → **Run All Above** (runs all cells before current)
2. Go to **Run** menu → **Run All Below** (runs all cells after current)

---

## 🔄 Common Notebook Operations

### Restart Kernel

If cells are stuck or you need to reset:

1. Go to **Kernel** menu → **Restart Kernel**
2. Or click the **restart button** (circular arrow) in the toolbar
3. Then re-run cells from the beginning

### Clear Output

1. Go to **Edit** menu → **Clear All Outputs**
2. Or right-click on a cell → **Clear Output**

### Save Notebook

- **Auto-saves** every few seconds
- Or press **`Ctrl + S`** to save manually

---

## 📊 What's in the Notebook?

The `01_data_analysis.ipynb` notebook includes:

1. **Data Loading**
   - Passenger demand data
   - Stop clusters
   - Geographic stop data

2. **Visualizations**
   - Geographic maps of stops
   - Passenger demand heatmaps
   - Cluster visualizations

3. **Forecast Analysis**
   - Prophet model details
   - Forecast plots
   - Component analysis

4. **Simulation Comparison**
   - Baseline vs Dynamic scheduling results
   - Performance metrics
   - Cost analysis

---

## 🐛 Troubleshooting

### Problem: "Connection refused" or can't access http://localhost:8888

**Solution:**
1. Check if Jupyter service is running:
   ```powershell
   docker compose ps
   ```
2. Check Jupyter logs:
   ```powershell
   docker compose logs jupyter
   ```
3. Restart the service:
   ```powershell
   docker compose restart jupyter
   ```

### Problem: "Module not found" errors

**Solution:**
1. Make sure the cell with `sys.path.insert(0, '/app/src')` has been run
2. Restart the kernel and re-run all cells from the beginning
3. Check that the `src` folder is mounted in docker-compose.yml

### Problem: "Database connection error"

**Solution:**
1. Make sure the `db` service is running:
   ```powershell
   docker compose ps db
   ```
2. Check database logs:
   ```powershell
   docker compose logs db
   ```
3. Restart both services:
   ```powershell
   docker compose restart db jupyter
   ```

### Problem: "File not found" errors (e.g., passenger_demand.csv)

**Solution:**
1. Make sure you've generated the data files:
   ```powershell
   docker compose run --rm web python src/data/generate_passengers.py
   docker compose run --rm web python src/models/cluster.py
   docker compose run --rm web python src/models/forecast.py
   ```
2. Check if files exist:
   ```powershell
   Get-ChildItem data/raw/*.csv
   ```

### Problem: Notebook is slow or unresponsive

**Solution:**
1. **Restart the kernel** (Kernel → Restart)
2. **Clear outputs** (Edit → Clear All Outputs)
3. **Run cells one at a time** instead of "Run All"
4. For large visualizations, consider reducing sample sizes

---

## 💡 Tips for Best Experience

1. **Run cells in order** - The notebook is designed to run top-to-bottom
2. **Check outputs** - Make sure each cell completes before running the next
3. **Save frequently** - While auto-save works, manual saves are safer
4. **Use sample mode** - For testing, use `USE_SAMPLE = True` in the comparison section
5. **Restart if stuck** - If something seems wrong, restart the kernel and re-run

---

## 🔗 Related Commands

### Start Jupyter
```powershell
docker compose up -d jupyter
```

### Stop Jupyter
```powershell
docker compose stop jupyter
```

### View Jupyter Logs
```powershell
docker compose logs -f jupyter
```

### Rebuild Jupyter (if code changes)
```powershell
docker compose build jupyter
docker compose up -d jupyter
```

---

## 📚 Additional Resources

- **Jupyter Lab Documentation**: https://jupyterlab.readthedocs.io/
- **Notebook Keyboard Shortcuts**: Press `H` in Jupyter Lab to see all shortcuts
- **Project Setup Guide**: See `COMPLETE_SETUP_GUIDE.md`
- **Simulation Guide**: See `HOW_TO_RUN_SIMULATIONS.md`

---

**Happy analyzing! 📊✨**

