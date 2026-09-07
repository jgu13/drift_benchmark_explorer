# Drift Benchmark Explorer

Build the normalized index and static assets:

```bash
python build_site.py \
  --root ../data/A_drift_benchmark \
  --root ../data/B_drift_benchmark \
  --root ../data/C_drift_benchmark \
  --root ../data/D_drift_benchmark
```

Serve the website:

```bash
python -m http.server 8080 --directory site
```

Open `http://localhost:8080`.

Rerun the build script after adding or editing benchmark siblings, evidence allocations, or execution plans. Task counts, evidence percentages, plan assets, and file manifests are regenerated from disk.
