# UNICEF Humanitarian Risk Forecasting + Command Dashboard

End-to-end humanitarian-risk workflow built on AOTS tropical-cyclone ensemble trajectories.

This workspace now contains:
- a full uncertainty-to-impact analytics pipeline,
- dashboard delivery in multiple front-end stacks,
- animated evidence products (GIF/MP4/interactive world map),
- and static deployment packages ready for public hosting.

Live demo (static dashboard): https://ag230602.github.io/unicef_data/

---

## 1) What we built (full scope)

### A) Risk analytics pipeline (Python)
Implemented in [build_humanitarian_risk_metrics.py](build_humanitarian_risk_metrics.py):
1. Load and clean AOTS ensemble tracks.
2. Build uncertainty cones per (`track_id`, `forecast_time`, `lead_time`) from ensemble spread.
3. Integrate external vulnerability data (population/coastal/INFORM) when available.
4. Auto-fallback to generated proxy external grid if external files are missing.
5. Compute cone-level exposure and composite risk scores.
6. Aggregate horizon-level and region-level summaries.
7. Export production-ready CSV outputs.

### B) Humanitarian visualization products
Implemented in [visualize_humanitarian_risk_video.py](visualize_humanitarian_risk_video.py):
- Frame-by-frame storyline visualization (map + horizon trend + top affected regions).
- GIF export for communications and quick sharing.
- MP4 export generated in this workspace for storm-specific briefing.

Implemented in [visualize_world_exact_positions.py](visualize_world_exact_positions.py):
- Interactive global animation of exact predicted storm positions over valid times.
- Hover-level lat/lon and risk metadata.
- Offline HTML export for no-internet usage.

### C) Command dashboard experiences
1. Pure static SPA in [index.html](index.html) (no build required).
2. Dash app in [humanitarian_dashboard.py](humanitarian_dashboard.py).
3. Streamlit app in [streamlit_app.py](streamlit_app.py).

All three UIs present the same decision logic:
- Risk Prep,
- Rescue Prep,
- Supply Prep.

### D) Deployment packs
- Public static deploy package in [deploy/index.html](deploy/index.html).
- Alternate static entry in [deploy/humanitarian_dashboard.html](deploy/humanitarian_dashboard.html).
- Drag-and-drop publish bundle in [PUBLISH_DRAG_DROP/index.html](PUBLISH_DRAG_DROP/index.html).

---

## 2) Repository map

### Core data + pipeline
- [AOTS_DATA_SHARE (5).csv](AOTS_DATA_SHARE%20(5).csv): source AOTS ensemble trajectory dataset.
- [build_humanitarian_risk_metrics.py](build_humanitarian_risk_metrics.py): cone + exposure + risk metrics builder.
- [visualize_humanitarian_risk_video.py](visualize_humanitarian_risk_video.py): humanitarian animation renderer.
- [visualize_world_exact_positions.py](visualize_world_exact_positions.py): exact-position world animation exporter.

### Dashboard implementations
- [index.html](index.html): static flagship dashboard.
- [humanitarian_dashboard.py](humanitarian_dashboard.py): Dash runtime dashboard.
- [streamlit_app.py](streamlit_app.py): Streamlit runtime dashboard.
- [plotly.min.js](plotly.min.js): local Plotly bundle for static/offline setup.

### Modeling (trajectory ML)
- [train_gno_dyn_gnn_track_aots_nan_fixed.py](train_gno_dyn_gnn_track_aots_nan_fixed.py): probabilistic trajectory model training (PyTorch; temporal + dynamic GNN).

### Documentation
- [README.md](README.md): this document.
- [humanitarian_risk_plan.md](humanitarian_risk_plan.md): implementation framing and metric definitions.
- [HUMANITARIAN_RISK_WORKFLOW.md](HUMANITARIAN_RISK_WORKFLOW.md): workflow details and quantitative summary.
- [DEPLOY_PUBLIC.md](DEPLOY_PUBLIC.md): publication options (GitHub Pages / Netlify / Cloudflare).

### Generated outputs
Stored in [outputs](outputs):
- [outputs/aots_uncertainty_cones.csv](outputs/aots_uncertainty_cones.csv)
- [outputs/proxy_external_grid_from_aots.csv](outputs/proxy_external_grid_from_aots.csv)
- [outputs/aots_population_exposure_by_cone.csv](outputs/aots_population_exposure_by_cone.csv)
- [outputs/aots_expected_exposure_by_horizon.csv](outputs/aots_expected_exposure_by_horizon.csv)
- [outputs/aots_region_risk_scores.csv](outputs/aots_region_risk_scores.csv)
- [outputs/aots_humanitarian_risk_summary.csv](outputs/aots_humanitarian_risk_summary.csv)
- [outputs/humanitarian_risk_animation.gif](outputs/humanitarian_risk_animation.gif)
- [outputs/humanitarian_risk_FINA.gif](outputs/humanitarian_risk_FINA.gif)
- [outputs/humanitarian_risk_FINA.mp4](outputs/humanitarian_risk_FINA.mp4)
- [outputs/world_exact_positions_animation.html](outputs/world_exact_positions_animation.html)
- [outputs/world_exact_positions_animation_offline.html](outputs/world_exact_positions_animation_offline.html)
- [outputs/world_exact_positions_points.csv](outputs/world_exact_positions_points.csv)

---

## 3) Data coverage used in this run

- Storm systems: 8 (`DITWAH`, `FINA`, `FUNG-WONG`, `KALMAEGI`, `KOTO`, `MELISSA`, `GEZANI`, `DUDZAI`)
- Forecast horizons: 6h, 12h, 24h, 48h, 72h, 96h
- Total cones generated: 1,262
- Region-level outputs include top-risk proxy regions from computed cone centers

Primary AOTS fields consumed:
- `TRACK_ID`, `FORECAST_TIME`, `VALID_TIME`, `LEAD_TIME`, `ENSEMBLE_MEMBER`, `LATITUDE`, `LONGITUDE`

---

## 4) Quantitative method (what the metrics mean)

For each cone at horizon $h$ and grid cells $i$ inside cone:

Population exposure:
$$
E_h = \sum_{i \in \text{cone}(h)} P_i
$$

Coastal-weighted exposure:
$$
CE_h = \sum_{i \in \text{cone}(h)} P_i C_i
$$

INFORM-weighted exposure:
$$
IE_h = \sum_{i \in \text{cone}(h)} P_i I_i
$$

Composite humanitarian risk score ($0\ldots100$):
$$
R_h = 100\left(0.50\frac{\log(1+E_h)}{16} + 0.25\frac{CE_h}{E_h+\epsilon} + 0.25\frac{IE_h}{E_h+\epsilon}\right)
$$

Aggregates exported:
- Expected exposure: $\mathbb{E}[E_h]$
- P90 exposure: $Q_{0.9}(E_h)$
- Expected risk score: $\mathbb{E}[R_h]$
- P90 risk score: $Q_{0.9}(R_h)$

---

## 5) Current run results (from generated CSVs)

From [outputs/aots_humanitarian_risk_summary.csv](outputs/aots_humanitarian_risk_summary.csv):
- Mean cone radius: **207.61 km**
- Max cone radius: **1055.87 km**
- Mean exposed population: **2,194,252.90**
- P90 exposed population: **5,522,368.76**
- Mean risk score: **67.86 / 100**
- P90 risk score: **76.14 / 100**
- `used_proxy_external_data = True`

From [outputs/aots_expected_exposure_by_horizon.csv](outputs/aots_expected_exposure_by_horizon.csv):
- Expected exposure rises from **0.99M (6h)** to **3.83M (96h)**.
- Worst P90 exposure peaks around **9.33M (72h)**.

From [outputs/aots_region_risk_scores.csv](outputs/aots_region_risk_scores.csv):
- Highest mean risk regions include **R_8_31, R_9_26, R_7_30, R_7_31, R_10_29**.

---

## 6) How to run everything

### Environment

Base dependencies are listed in [requirements.txt](requirements.txt):
- `streamlit`
- `plotly`

For full pipeline + media exports, install additional packages as needed:
- `numpy`, `pandas`, `matplotlib`, `imageio`, `pillow`

Optional ML training dependencies:
- `torch`, `scikit-learn`, `tqdm`

### A) Build humanitarian risk metrics
Run:
- `python build_humanitarian_risk_metrics.py`

Output files are written to [outputs](outputs).

### B) Build GIF video storyline
Run:
- `python visualize_humanitarian_risk_video.py`

Outputs:
- GIF + frame folder (and MP4 if configured externally/workflow-side).

### C) Build exact-position world animation
Run:
- `python visualize_world_exact_positions.py`

Outputs:
- interactive web map HTML,
- offline standalone HTML,
- exact-position points CSV.

### D) Launch dashboards

Static dashboard:
- open [index.html](index.html) directly in browser, or serve it as static site.

Dash version:
- `python humanitarian_dashboard.py`
- browse to `http://127.0.0.1:8050`

Streamlit version:
- `streamlit run streamlit_app.py`

### E) Optional model training
Run:
- `python train_gno_dyn_gnn_track_aots_nan_fixed.py`

This saves checkpoints + metrics under configured output directories in the script config.

---

## 7) External-data integration (for production-grade risk)

The pipeline supports real external datasets through `RiskCFG` in [build_humanitarian_risk_metrics.py](build_humanitarian_risk_metrics.py):

1. Population grid CSV with:
	- `lat`, `lon`, `population`
2. Coastal exposure grid CSV (optional) with:
	- `lat`, `lon`, `coastal_exposure` in $[0,1]$
3. INFORM vulnerability CSV (optional) with:
	- `iso3`, `inform_risk` (0..1 or 0..10, auto-normalized)

If no population grid is supplied and fallback is enabled, a proxy grid is auto-generated from AOTS point density.

---

## 8) Deployment options (public)

Prepared docs and assets:
- [DEPLOY_PUBLIC.md](DEPLOY_PUBLIC.md)
- [deploy/index.html](deploy/index.html)
- [PUBLISH_DRAG_DROP/README.txt](PUBLISH_DRAG_DROP/README.txt)

Recommended static hosting:
1. GitHub Pages
2. Netlify Drop
3. Cloudflare Pages

No backend is required for the static dashboard.

---

## 9) Known limitations

1. Current run metrics are demonstration-grade because fallback proxy vulnerability data was used.
2. Region IDs are proxy bins unless replaced by real regional boundaries or authoritative admin-unit joins.
3. Operational deployment should use validated demographic/vulnerability data feeds and periodic refresh.

---

## 10) Recommended next steps

1. Replace proxy grid with real population/coastal/INFORM datasets.
2. Add country/admin boundary joins for policy-ready geography.
3. Add uncertainty calibration and backtesting against historical impact records.
4. Add automated CI job to rebuild outputs and redeploy static dashboard on new forecasts.

---

## 11) One-line contribution framing

**Uncertainty-aware humanitarian risk forecasting from ensemble cyclone trajectories, translated into operational preparedness dashboards and deployable decision products.**

---

## 12) Full report-style write-up (Intro, Method, Data, Architecture, Visualization, Conclusion)

### INTRO

This project converts tropical cyclone ensemble trajectory forecasts into humanitarian decision intelligence.

Instead of stopping at track prediction, the workflow estimates who may be exposed, where risk is concentrated, and how risk changes across lead times (6h to 96h). The outputs are then converted into operational visuals (dashboards, GIF/MP4, and interactive maps) for preparedness planning.

Main objective:
- move from **forecast uncertainty** to **action-ready humanitarian risk insights**.

### METHOD (METHODOLOGY)

The implemented method is a 4-stage pipeline:

1. **Trajectory ingestion and cleaning**
	- Parse AOTS fields (`TRACK_ID`, `FORECAST_TIME`, `VALID_TIME`, `LEAD_TIME`, `ENSEMBLE_MEMBER`, `LATITUDE`, `LONGITUDE`).
	- Normalize longitudes and numeric fields.

2. **Uncertainty cone construction**
	- Group by (`track_id`, `forecast_time`, `lead_time`).
	- Compute ensemble spread radius at quantile (default 0.90) + base buffer.
	- Export per-cone geometry and metadata.

3. **Exposure + vulnerability fusion**
	- Spatially query grid cells inside each cone.
	- Sum population and vulnerability-weighted exposure terms.
	- Compute composite risk score using the equations documented above.

4. **Aggregation + productization**
	- Aggregate by forecast horizon and region.
	- Generate summary CSVs.
	- Render communication products (dashboard charts, GIF/MP4, world position animation).

### DATA

#### A) Primary data used now
- Source: [AOTS_DATA_SHARE (5).csv](AOTS_DATA_SHARE%20(5).csv)
- Nature: multi-member ensemble storm tracks
- Coverage in current run:
  - 8 storms
  - 6 horizons (6, 12, 24, 48, 72, 96h)
  - 1,262 cones generated

#### B) Optional external datasets supported
- Population grid (`lat`, `lon`, `population`)
- Coastal exposure grid (`lat`, `lon`, `coastal_exposure`)
- INFORM vulnerability (`iso3`, `inform_risk`)

#### C) Current run mode
Because external files were not configured, the pipeline used fallback proxy data generation and recorded:
- `used_proxy_external_data = True`
in [outputs/aots_humanitarian_risk_summary.csv](outputs/aots_humanitarian_risk_summary.csv).

### ARCHITECTURE

System architecture is modular and file-oriented:

1. **Compute layer (Python)**
	- [build_humanitarian_risk_metrics.py](build_humanitarian_risk_metrics.py)
	- [visualize_humanitarian_risk_video.py](visualize_humanitarian_risk_video.py)
	- [visualize_world_exact_positions.py](visualize_world_exact_positions.py)

2. **Data products layer (CSV/media)**
	- Cone-level, horizon-level, region-level summaries in [outputs](outputs)
	- GIF/MP4 + interactive HTML maps

3. **Presentation layer (dashboards)**
	- Static web app: [index.html](index.html)
	- Dash app: [humanitarian_dashboard.py](humanitarian_dashboard.py)
	- Streamlit app: [streamlit_app.py](streamlit_app.py)

4. **Deployment layer**
	- Static deployment artifacts in [deploy](deploy)
	- drag-drop publication pack in [PUBLISH_DRAG_DROP](PUBLISH_DRAG_DROP)

#### How Python is used with the dashboard (explicit)

Python is used in two ways:

1. **Backend analytics generation (offline/periodic):**
	- Build all risk datasets that feed dashboard indicators and charts.
	- This is done in [build_humanitarian_risk_metrics.py](build_humanitarian_risk_metrics.py).

2. **Python-native dashboard serving (runtime):**
	- **Dash** app in [humanitarian_dashboard.py](humanitarian_dashboard.py): Python creates Plotly figures and serves interactive web UI.
	- **Streamlit** app in [streamlit_app.py](streamlit_app.py): Python defines layout, cards, tabs, and plots in a fast deployment-friendly app.

In short: Python powers both the **data intelligence** and (for Dash/Streamlit variants) the **interactive dashboard runtime**.

### VISUALIZATION

Visualization strategy is decision-centered and split into three operational tabs:

1. **Risk Prep**
	- Animated storm tracks
	- Portfolio risk gauge
	- Region risk ranking with sorting/filtering
	- Population-vs-risk scatter

2. **Rescue Prep**
	- 3D rotating exposure globe
	- Rescue-priority zone table
	- Max population-at-risk by storm

3. **Supply Prep**
	- Horizon slider with dynamic supply cards
	- Coastal vs inland burden
	- Deployment timeline (Gantt-style)
	- Risk trend across lead times

Additional storytelling products:
- [outputs/humanitarian_risk_animation.gif](outputs/humanitarian_risk_animation.gif)
- [outputs/humanitarian_risk_FINA.mp4](outputs/humanitarian_risk_FINA.mp4)
- [outputs/world_exact_positions_animation.html](outputs/world_exact_positions_animation.html)

### CONCLUSION

This work demonstrates a complete humanitarian forecasting stack:
- from ensemble track uncertainty,
- to quantitative exposure/risk estimation,
- to operational visual decision products,
- to public-ready deployment.

Current outputs are fully functional for demonstration and workflow validation. For operational or publication-grade impact estimates, the next critical upgrade is replacing proxy external vulnerability layers with authoritative real datasets.
