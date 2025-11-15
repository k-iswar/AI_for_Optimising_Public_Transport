# How to Run Simulations and Get Results

## Quick Start Guide

### Prerequisites Check
✅ Make sure you have:
- Docker services running (`docker compose ps`)
- Passenger demand data generated
- Clustering completed
- Forecasting models trained

---

## Step-by-Step Instructions

### Step 1: Run Baseline Simulation

Open your terminal and run:

```bash
docker compose run --rm web python src/simulation/baseline_sim.py
```

**What happens:**
- Simulates 1.56M passengers with static schedule
- Calculates wait times, costs, and efficiency metrics
- **Automatically saves results** to `data/processed/baseline_simulation_results.json`
- Prints summary to terminal

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

**Time:** This may take 10-30 minutes depending on your system.

---

### Step 2: Run Dynamic Simulation

In the same terminal, run:

```bash
docker compose run --rm web python src/simulation/dynamic_sim.py
```

**What happens:**
- Simulates 1.56M passengers with AI-driven dynamic scheduling
- Uses Prophet forecasts to dispatch buses proactively
- **Automatically saves results** to `data/processed/dynamic_simulation_results.json`
- Prints summary to terminal

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

**Time:** This may take 15-45 minutes depending on your system.

---

### Step 3: View Results in Jupyter Notebook

1. **Open Jupyter Lab:**
   - Go to: http://localhost:8888
   - Open `01_data_analysis.ipynb`

2. **Navigate to Cell 18** (Comparison Data Loading)

3. **Run Cell 18:**
   - The notebook will **automatically detect** the JSON files
   - Load results from both simulations
   - Populate the comparison dataframe
   - **No manual copying needed!**

4. **Run Cell 19** (Visualization):
   - See side-by-side comparison charts
   - View improvement percentages
   - Analyze the differences

---

## Alternative: Quick Test with Sample Data

If you want to test quickly without running full simulations:

1. **In Jupyter Notebook, Cell 18:**
   - Set `USE_SAMPLE = True`
   - Set `SAMPLE_SIZE = 1000` (or any number)
   - Run the cell

2. **This will:**
   - Run both simulations with sample data
   - Show results immediately
   - Good for testing, but not for final research

---

## Where Results Are Saved

Results are automatically saved to:

- **Baseline:** `data/processed/baseline_simulation_results.json`
- **Dynamic:** `data/processed/dynamic_simulation_results.json`

These files contain:
- All metrics (wait times, costs, KMs, passengers)
- Timestamp of when simulation ran
- Sample size used
- Full results dictionary

---

## Troubleshooting

### Problem: "Passenger file not found"
**Solution:** Run passenger generation first:
```bash
docker compose run --rm web python src/data/generate_passengers.py
```

### Problem: "Missing model file"
**Solution:** Train forecasting models first:
```bash
docker compose run --rm web python src/models/forecast.py
```

### Problem: Simulations taking too long
**Solution:** Use sample mode in notebook for testing, or run overnight for full results.

### Problem: JSON files not loading in notebook
**Solution:** 
1. Check files exist: `ls data/processed/`
2. Restart Jupyter kernel
3. Re-run cell 18

---

## Expected Results Comparison

After running both simulations, you should see:

| Metric | Baseline (Static) | Dynamic (AI) | Improvement |
|--------|------------------|--------------|-------------|
| Average Wait Time | Higher | Lower | ⬇️ 30-50% |
| Total Cost | Fixed (645K km) | Variable | ⬇️ 10-20% |
| Passengers Failed | Higher | Lower | ⬇️ 40-60% |
| Cost per Passenger | Higher | Lower | ⬇️ 15-25% |

---

## Next Steps After Getting Results

1. **Analyze the comparison** in the notebook
2. **Generate visualizations** (Cell 19)
3. **Export results** for your research paper
4. **Document findings** in your report

---

## Quick Command Reference

```bash
# Check services
docker compose ps

# Run baseline simulation
docker compose run --rm web python src/simulation/baseline_sim.py

# Run dynamic simulation
docker compose run --rm web python src/simulation/dynamic_sim.py

# Check if results were saved (Windows PowerShell)
Get-ChildItem data/processed/*.json

# Or use dir (Windows)
dir data\processed\*.json

# View results file (Windows PowerShell)
Get-Content data/processed/baseline_simulation_results.json

# Or use type (Windows)
type data\processed\baseline_simulation_results.json
```

---

**That's it!** Run the simulations, and the notebook will automatically load and compare the results. 🚀

