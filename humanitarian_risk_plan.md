# Humanitarian Risk Forecasting Extension (AOTS)

## What is now implemented
A runnable pipeline is added in:
- build_humanitarian_risk_metrics.py

It does the following:
1. Loads AOTS ensemble trajectories.
2. Builds uncertainty cones per (`TRACK_ID`, `FORECAST_TIME`, `LEAD_TIME`) using ensemble spread.
3. Exports cone geometry summary to CSV.
4. If external datasets are provided, computes:
   - estimated population exposed within cone
   - expected exposure by forecast horizon
   - region risk scores

## External datasets to integrate
Provide CSV files with these minimum schemas:

### 1) Population density (WorldPop / GPW converted to point grid)
- `lat`, `lon`, `population`
- Optional: `iso3`, `region_id`

### 2) Coastal exposure grid
- `lat`, `lon`, `coastal_exposure` (0 to 1)

### 3) INFORM risk index
- `iso3`, `inform_risk` (0 to 1 or 0 to 10)

## Impact metrics (clear quantitative definitions)
For each cone at lead time $h$:

- Population exposed:
  $$E_h = \sum_{i \in \text{cone}(h)} P_i$$

- Coastal-weighted exposure:
  $$CE_h = \sum_{i \in \text{cone}(h)} P_i \cdot C_i$$

- INFORM-weighted exposure:
  $$IE_h = \sum_{i \in \text{cone}(h)} P_i \cdot I_i$$

- Composite risk score (0 to 100):
  $$R_h = 100\left(0.5\frac{\log(1+E_h)}{16} + 0.25\frac{CE_h}{E_h+\epsilon} + 0.25\frac{IE_h}{E_h+\epsilon}\right)$$

Horizon-level metrics:
- expected exposure at horizon $h$: $\mathbb{E}[E_h]$
- 90th percentile exposure at horizon $h$: $Q_{0.9}(E_h)$
- expected risk score at horizon $h$: $\mathbb{E}[R_h]$

## Suggested research contribution framing
Recommended primary contribution:

**Uncertainty-aware humanitarian risk forecasting from ensemble cyclone trajectories.**

This combines:
- probabilistic track forecasting,
- uncertainty cones,
- geospatial exposure and vulnerability estimation,
- decision-ready risk scores for preparedness.

This framing is stronger than trajectory-only forecasting because it directly supports humanitarian operations.

## Next action required
Edit `RiskCFG` in `build_humanitarian_risk_metrics.py` with local paths for:
- `population_grid_csv`
- `coastal_grid_csv` (optional)
- `inform_risk_csv` (optional)

Then run the script to generate final exposure/risk outputs.
