# Humanitarian Risk Forecasting Workflow (AOTS)

## 1) Objective
This project extends ensemble cyclone trajectory forecasts into **humanitarian impact forecasting** by estimating:
- uncertainty-aware storm influence area (cone)
- exposed population
- horizon-wise expected exposure
- region-level risk scores
- frame-by-frame visual evidence (GIF/MP4)

---

## 2) Data Used
### Core input
- AOTS ensemble track data: `AOTS_DATA_SHARE (5).csv`

Main fields used:
- `TRACK_ID`, `FORECAST_TIME`, `LEAD_TIME`, `ENSEMBLE_MEMBER`
- `LATITUDE`, `LONGITUDE`

### External vulnerability data (intended)
Pipeline supports:
- population grid (`lat`, `lon`, `population`)
- coastal exposure grid (`lat`, `lon`, `coastal_exposure`)
- INFORM risk (`iso3`, `inform_risk`)

### Current run mode
No real external files were available in workspace, so pipeline used **proxy external grid generation** from AOTS point density (demo mode).

---

## 3) Implemented Scripts
### Risk pipeline
- `build_humanitarian_risk_metrics.py`

What it does:
1. Loads and cleans AOTS trajectories.
2. Builds uncertainty cones per (`track_id`, `forecast_time`, `lead_time`) using ensemble spread.
3. Integrates external vulnerability grids if provided.
4. If missing, auto-builds proxy external grid (demo fallback).
5. Computes cone-level exposure and risk metrics.
6. Aggregates horizon and regional summaries.
7. Saves CSV outputs.

### Visualization pipeline
- `visualize_humanitarian_risk_video.py`

What it does:
1. Reads cone-level exposure outputs.
2. Renders frame sequence (map + horizon chart + regional impact chart).
3. Exports animated GIF.
4. (Run used) also exported MP4 for a selected storm.

---

## 4) Quantitative Impact Metrics
For a cone at horizon $h$ with grid cells $i$:

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

Composite risk score ($0$ to $100$):
$$
R_h = 100\left(0.50\frac{\log(1+E_h)}{16} + 0.25\frac{CE_h}{E_h+\epsilon} + 0.25\frac{IE_h}{E_h+\epsilon}\right)
$$

Horizon metrics:
- expected exposure: $\mathbb{E}[E_h]$
- p90 exposure: $Q_{0.9}(E_h)$
- expected risk: $\mathbb{E}[R_h]$
- p90 risk: $Q_{0.9}(R_h)$

---

## 5) Produced Outputs
### Main CSV outputs
- `outputs/aots_uncertainty_cones.csv`
- `outputs/proxy_external_grid_from_aots.csv`
- `outputs/aots_population_exposure_by_cone.csv`
- `outputs/aots_expected_exposure_by_horizon.csv`
- `outputs/aots_region_risk_scores.csv`
- `outputs/aots_humanitarian_risk_summary.csv`

### Visualization outputs
- `outputs/humanitarian_risk_animation.gif`
- `outputs/humanitarian_risk_FINA.gif`
- `outputs/humanitarian_risk_FINA.mp4`
- `outputs/video_frames/`
- `outputs/video_frames_FINA/`

---

## 6) Key Run Findings (Current Workspace)
Summary file reports:
- total cones: **1262**
- mean cone radius: **207.61 km**
- max cone radius: **1055.87 km**
- mean exposed population: **2,194,252.90**
- p90 exposed population: **5,522,368.76**
- mean risk score: **67.86/100**
- p90 risk score: **76.14/100**
- `used_proxy_external_data = True`

Top-risk storm in this run:
- `FINA` (highest mean risk among tracks)

Top impacted proxy regions for `FINA`:
- `R_8_31`
- `R_7_31`
- `R_7_30`

---

## 7) How to Reproduce
From workspace root:
1. Run risk metrics pipeline:
   - `/usr/bin/python3 build_humanitarian_risk_metrics.py`
2. Run visualization:
   - `/usr/bin/python3 visualize_humanitarian_risk_video.py`

Optional focused storm rendering:
- set `track_id` in visualization config or run with patched config values.

---

## 8) Research Contribution Framing
Recommended contribution statement:

**Uncertainty-aware humanitarian risk forecasting from ensemble cyclone trajectories.**

This contributes beyond trajectory prediction by linking forecast uncertainty to human exposure and vulnerability for disaster preparedness and response planning.

---

## 9) Important Limitation
Current numeric exposure/risk results are **demonstration-grade** because external vulnerability data were proxied.
For publication/operational validity, replace proxy with real:
- WorldPop or GPW population grid
- coastal exposure dataset
- INFORM risk index

The pipeline is already structured for this substitution via file paths in `RiskCFG`.
