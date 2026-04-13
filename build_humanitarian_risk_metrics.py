import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class RiskCFG:
	# Input AOTS file (ensemble trajectories)
	aots_csv_path: str = "/Users/agd9c/Downloads/UNICEF_DATA/AOTS_DATA_SHARE (5).csv"

	# Optional external datasets (CSV)
	# population_grid_csv must contain: lat, lon, population
	population_grid_csv: Optional[str] = None
	# optional extra columns on same grid: coastal_exposure (0..1), region_id, iso3
	coastal_grid_csv: Optional[str] = None
	# country-level vulnerability: iso3, inform_risk (0..10 or 0..1)
	inform_risk_csv: Optional[str] = None

	# Modeling choices
	cone_quantile: float = 0.90
	base_buffer_km: float = 25.0
	lead_hours: Tuple[int, ...] = (6, 12, 24, 48, 72, 96)

	# Output
	out_dir: str = "/Users/agd9c/Downloads/UNICEF_DATA/outputs"

	# Fallback mode when external datasets are not yet available.
	# This generates proxy data so the full pipeline can still run end-to-end.
	auto_generate_proxy_external_data: bool = True
	proxy_grid_resolution_deg: float = 0.75


cfg = RiskCFG()


def normalize_longitude(lon: pd.Series) -> pd.Series:
	lon = pd.to_numeric(lon, errors="coerce")
	if lon.dropna().empty:
		return lon
	if lon.max() > 180:
		lon = ((lon + 180) % 360) - 180
	return lon


def haversine_km(lat1: np.ndarray, lon1: np.ndarray, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
	r = 6371.0
	phi1 = np.radians(lat1)
	phi2 = np.radians(lat2)
	dphi = np.radians(lat2 - lat1)
	dlambda = np.radians(lon2 - lon1)
	a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
	a = np.clip(a, 0.0, 1.0)
	return 2.0 * r * np.arcsin(np.sqrt(a))


def load_aots(csv_path: str) -> pd.DataFrame:
	required = {
		"FORECAST_TIME",
		"TRACK_ID",
		"ENSEMBLE_MEMBER",
		"VALID_TIME",
		"LEAD_TIME",
		"LATITUDE",
		"LONGITUDE",
	}
	df = pd.read_csv(csv_path)
	missing = required - set(df.columns)
	if missing:
		raise ValueError(f"AOTS is missing columns: {sorted(missing)}")

	df["FORECAST_TIME"] = pd.to_datetime(df["FORECAST_TIME"], errors="coerce", utc=True)
	df["VALID_TIME"] = pd.to_datetime(df["VALID_TIME"], errors="coerce", utc=True)
	df["LONGITUDE"] = normalize_longitude(df["LONGITUDE"])
	for col in ["LEAD_TIME", "LATITUDE", "LONGITUDE", "ENSEMBLE_MEMBER"]:
		df[col] = pd.to_numeric(df[col], errors="coerce")

	keep = ["TRACK_ID", "FORECAST_TIME", "VALID_TIME", "LEAD_TIME", "ENSEMBLE_MEMBER", "LATITUDE", "LONGITUDE"]
	df = df[keep].dropna().copy()
	df["TRACK_ID"] = df["TRACK_ID"].astype(str)
	df["LEAD_TIME"] = df["LEAD_TIME"].astype(int)

	if cfg.lead_hours:
		df = df[df["LEAD_TIME"].isin(cfg.lead_hours)].copy()

	return df


def compute_uncertainty_cones(df: pd.DataFrame, cone_quantile: float, base_buffer_km: float) -> pd.DataFrame:
	rows: List[Dict] = []

	grouped = df.groupby(["TRACK_ID", "FORECAST_TIME", "LEAD_TIME"], sort=False)
	for (track_id, forecast_time, lead_time), g in grouped:
		lat = g["LATITUDE"].to_numpy(dtype=float)
		lon = g["LONGITUDE"].to_numpy(dtype=float)
		center_lat = float(np.mean(lat))
		center_lon = float(np.mean(lon))

		d_km = haversine_km(lat, lon, center_lat * np.ones_like(lat), center_lon * np.ones_like(lon))
		radius_q = float(np.quantile(d_km, cone_quantile)) if len(d_km) else 0.0
		radius_km = max(radius_q + base_buffer_km, base_buffer_km)

		rows.append(
			{
				"track_id": track_id,
				"forecast_time": forecast_time,
				"lead_time": int(lead_time),
				"members": int(len(g)),
				"center_lat": center_lat,
				"center_lon": center_lon,
				"cone_radius_km": radius_km,
				"radius_q_km": radius_q,
			}
		)

	cones = pd.DataFrame(rows)
	cones = cones.sort_values(["track_id", "forecast_time", "lead_time"]).reset_index(drop=True)
	return cones


def load_grid_dataset(path: str, value_col: str) -> pd.DataFrame:
	grid = pd.read_csv(path)
	rename_map = {}
	for c in grid.columns:
		cl = c.lower()
		if cl == "latitude":
			rename_map[c] = "lat"
		elif cl == "longitude":
			rename_map[c] = "lon"
		elif cl == value_col.lower() and c != value_col:
			rename_map[c] = value_col
	if rename_map:
		grid = grid.rename(columns=rename_map)

	required = {"lat", "lon", value_col}
	missing = required - set(grid.columns)
	if missing:
		raise ValueError(f"Grid file {path} missing columns: {sorted(missing)}")

	grid["lat"] = pd.to_numeric(grid["lat"], errors="coerce")
	grid["lon"] = normalize_longitude(grid["lon"])
	grid[value_col] = pd.to_numeric(grid[value_col], errors="coerce")

	keep = ["lat", "lon", value_col]
	for extra in ["iso3", "region_id"]:
		if extra in grid.columns:
			keep.append(extra)
	return grid[keep].dropna(subset=["lat", "lon", value_col]).copy()


def merge_external_grids(
	pop_path: Optional[str],
	coastal_path: Optional[str],
	inform_path: Optional[str],
) -> Optional[pd.DataFrame]:
	if pop_path is None or not os.path.exists(pop_path):
		return None

	pop = load_grid_dataset(pop_path, "population")
	grid = pop.copy()

	if coastal_path and os.path.exists(coastal_path):
		coastal = load_grid_dataset(coastal_path, "coastal_exposure")
		grid = grid.merge(coastal[["lat", "lon", "coastal_exposure"]], on=["lat", "lon"], how="left")
	else:
		grid["coastal_exposure"] = 0.0

	grid["coastal_exposure"] = grid["coastal_exposure"].fillna(0.0).clip(0.0, 1.0)

	if inform_path and os.path.exists(inform_path) and "iso3" in grid.columns:
		inform = pd.read_csv(inform_path)
		cols = {c.lower(): c for c in inform.columns}
		iso_col = cols.get("iso3")
		risk_col = cols.get("inform_risk")
		if iso_col and risk_col:
			inf = inform[[iso_col, risk_col]].copy()
			inf = inf.rename(columns={iso_col: "iso3", risk_col: "inform_risk"})
			inf["inform_risk"] = pd.to_numeric(inf["inform_risk"], errors="coerce")
			grid = grid.merge(inf, on="iso3", how="left")
	if "inform_risk" not in grid.columns:
		grid["inform_risk"] = np.nan

	# Normalize INFORM to 0..1 if it appears to be 0..10 scale
	if pd.notna(grid["inform_risk"]).any() and float(grid["inform_risk"].max()) > 1.5:
		grid["inform_risk"] = grid["inform_risk"] / 10.0

	grid["inform_risk"] = grid["inform_risk"].fillna(grid["inform_risk"].median())
	grid["inform_risk"] = grid["inform_risk"].fillna(0.0).clip(0.0, 1.0)
	return grid


def build_proxy_external_grid_from_aots(aots: pd.DataFrame, resolution_deg: float = 0.75) -> pd.DataFrame:
	"""
	Build a coarse proxy population/vulnerability grid from AOTS points.
	This is ONLY for demonstration when external datasets are unavailable.
	"""
	if resolution_deg <= 0:
		resolution_deg = 0.75

	work = aots[["LATITUDE", "LONGITUDE"]].copy()
	work["lat"] = np.round(work["LATITUDE"] / resolution_deg) * resolution_deg
	work["lon"] = np.round(work["LONGITUDE"] / resolution_deg) * resolution_deg

	agg = work.groupby(["lat", "lon"], as_index=False).size().rename(columns={"size": "samples"})

	# Proxy population from track density (strictly a placeholder until WorldPop/GPW is added).
	# Scale chosen so output magnitudes are human-readable.
	agg["population"] = (agg["samples"].astype(float) ** 1.15) * 800.0

	# Proxy coastal exposure: higher near tropics/subtropics where many cyclone landfalls occur.
	# This is NOT a replacement for a real coastal dataset.
	agg["coastal_exposure"] = np.clip(1.0 - (np.abs(agg["lat"]) / 35.0), 0.0, 1.0)

	# Proxy region id from lat/lon bins.
	agg["region_id"] = (
		"R_"
		+ (np.floor((agg["lat"] + 90.0) / 10.0).astype(int)).astype(str)
		+ "_"
		+ (np.floor((agg["lon"] + 180.0) / 10.0).astype(int)).astype(str)
	)

	# No INFORM available in fallback: assign neutral risk.
	agg["inform_risk"] = 0.5

	return agg[["lat", "lon", "population", "coastal_exposure", "region_id", "inform_risk"]].copy()


def _to_balltree_radians(lat: Iterable[float], lon: Iterable[float]) -> np.ndarray:
	return np.vstack([np.radians(np.asarray(lat, dtype=float)), np.radians(np.asarray(lon, dtype=float))]).T


def _query_radius_haversine(
	ref_lat: np.ndarray,
	ref_lon: np.ndarray,
	query_lat: np.ndarray,
	query_lon: np.ndarray,
	radius_km: np.ndarray,
) -> List[np.ndarray]:
	out: List[np.ndarray] = []
	for i in range(len(query_lat)):
		d = haversine_km(ref_lat, ref_lon, query_lat[i], query_lon[i])
		out.append(np.where(d <= radius_km[i])[0])
	return out


def _nearest_indices_haversine(
	ref_lat: np.ndarray,
	ref_lon: np.ndarray,
	query_lat: np.ndarray,
	query_lon: np.ndarray,
) -> np.ndarray:
	out = np.zeros(len(query_lat), dtype=int)
	for i in range(len(query_lat)):
		d = haversine_km(ref_lat, ref_lon, query_lat[i], query_lon[i])
		out[i] = int(np.argmin(d))
	return out


def compute_exposure_metrics(cones: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
	grid_lat = grid["lat"].to_numpy(dtype=float)
	grid_lon = grid["lon"].to_numpy(dtype=float)
	cone_lat = cones["center_lat"].to_numpy(dtype=float)
	cone_lon = cones["center_lon"].to_numpy(dtype=float)
	cone_r = cones["cone_radius_km"].to_numpy(dtype=float)

	idx_by_cone = _query_radius_haversine(grid_lat, grid_lon, cone_lat, cone_lon, cone_r)

	out_rows: List[Dict] = []
	for i, idxs in enumerate(idx_by_cone):
		c = cones.iloc[i]
		if len(idxs) == 0:
			out_rows.append(
				{
					**c.to_dict(),
					"estimated_population_exposed": 0.0,
					"coastal_exposure_weighted_pop": 0.0,
					"inform_weighted_pop": 0.0,
					"risk_score": 0.0,
					"cells_in_cone": 0,
				}
			)
			continue

		local = grid.iloc[idxs]
		pop = local["population"].to_numpy(dtype=float)
		coastal = local.get("coastal_exposure", pd.Series(np.zeros(len(local)))).to_numpy(dtype=float)
		inform = local.get("inform_risk", pd.Series(np.zeros(len(local)))).to_numpy(dtype=float)

		pop_exposed = float(np.sum(pop))
		coastal_weighted = float(np.sum(pop * coastal))
		inform_weighted = float(np.sum(pop * inform))

		# Clear impact metric (0..100): combines exposure + vulnerability + coastality.
		# The log term stabilizes scale across storms of very different sizes.
		risk_score = 0.0
		if pop_exposed > 0:
			risk_score = float(
				100.0
				* (
					0.50 * np.log1p(pop_exposed) / 16.0
					+ 0.25 * (coastal_weighted / pop_exposed)
					+ 0.25 * (inform_weighted / pop_exposed)
				)
			)
			risk_score = float(np.clip(risk_score, 0.0, 100.0))

		out_rows.append(
			{
				**c.to_dict(),
				"estimated_population_exposed": pop_exposed,
				"coastal_exposure_weighted_pop": coastal_weighted,
				"inform_weighted_pop": inform_weighted,
				"risk_score": risk_score,
				"cells_in_cone": int(len(local)),
			}
		)

	return pd.DataFrame(out_rows)


def aggregate_horizon_metrics(exposure_df: pd.DataFrame) -> pd.DataFrame:
	agg = (
		exposure_df.groupby("lead_time", as_index=False)
		.agg(
			expected_exposure=("estimated_population_exposed", "mean"),
			p90_exposure=("estimated_population_exposed", lambda s: float(np.quantile(s, 0.90))),
			expected_risk_score=("risk_score", "mean"),
			p90_risk_score=("risk_score", lambda s: float(np.quantile(s, 0.90))),
		)
		.sort_values("lead_time")
	)
	return agg


def aggregate_region_metrics(exposure_df: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
	if "region_id" not in grid.columns:
		return pd.DataFrame()

	# Region proxy by nearest center at each cone.
	region_points = grid[["lat", "lon", "region_id"]].drop_duplicates().copy()
	nearest_idx = _nearest_indices_haversine(
		region_points["lat"].to_numpy(dtype=float),
		region_points["lon"].to_numpy(dtype=float),
		exposure_df["center_lat"].to_numpy(dtype=float),
		exposure_df["center_lon"].to_numpy(dtype=float),
	)
	exposure_df = exposure_df.copy()
	exposure_df["region_id"] = region_points.iloc[nearest_idx]["region_id"].to_numpy()

	return (
		exposure_df.groupby("region_id", as_index=False)
		.agg(
			mean_population_exposed=("estimated_population_exposed", "mean"),
			mean_risk_score=("risk_score", "mean"),
			p90_risk_score=("risk_score", lambda s: float(np.quantile(s, 0.90))),
			cones_count=("risk_score", "size"),
		)
		.sort_values("mean_risk_score", ascending=False)
	)


def main() -> None:
	os.makedirs(cfg.out_dir, exist_ok=True)

	print("Loading AOTS...")
	aots = load_aots(cfg.aots_csv_path)
	print(f"Rows: {len(aots):,} | storms: {aots['TRACK_ID'].nunique()} | lead_hours: {sorted(aots['LEAD_TIME'].unique())}")

	print("Computing uncertainty cones from ensembles...")
	cones = compute_uncertainty_cones(aots, cfg.cone_quantile, cfg.base_buffer_km)
	cones_path = os.path.join(cfg.out_dir, "aots_uncertainty_cones.csv")
	cones.to_csv(cones_path, index=False)
	print(f"Saved: {cones_path}")

	grid = merge_external_grids(cfg.population_grid_csv, cfg.coastal_grid_csv, cfg.inform_risk_csv)
	if grid is None:
		if cfg.auto_generate_proxy_external_data:
			print("No external population/coastal/vulnerability datasets configured.")
			print("Generating PROXY external grid from AOTS points (demo mode).")
			grid = build_proxy_external_grid_from_aots(aots, cfg.proxy_grid_resolution_deg)
			proxy_grid_path = os.path.join(cfg.out_dir, "proxy_external_grid_from_aots.csv")
			grid.to_csv(proxy_grid_path, index=False)
			print(f"Saved: {proxy_grid_path}")
		else:
			print("No population grid configured. Stopped after cone export.")
			print("To compute humanitarian exposure, set cfg.population_grid_csv (and optionally coastal/inform files).")
			return

	print("Computing exposure and risk metrics...")
	exposure = compute_exposure_metrics(cones, grid)
	exposure_path = os.path.join(cfg.out_dir, "aots_population_exposure_by_cone.csv")
	exposure.to_csv(exposure_path, index=False)
	print(f"Saved: {exposure_path}")

	horizon = aggregate_horizon_metrics(exposure)
	horizon_path = os.path.join(cfg.out_dir, "aots_expected_exposure_by_horizon.csv")
	horizon.to_csv(horizon_path, index=False)
	print(f"Saved: {horizon_path}")

	region = aggregate_region_metrics(exposure, grid)
	if not region.empty:
		region_path = os.path.join(cfg.out_dir, "aots_region_risk_scores.csv")
		region.to_csv(region_path, index=False)
		print(f"Saved: {region_path}")

	summary = {
		"cones": int(len(cones)),
		"mean_cone_radius_km": float(cones["cone_radius_km"].mean()),
		"max_cone_radius_km": float(cones["cone_radius_km"].max()),
		"mean_population_exposed": float(exposure["estimated_population_exposed"].mean()),
		"p90_population_exposed": float(np.quantile(exposure["estimated_population_exposed"], 0.90)),
		"mean_risk_score": float(exposure["risk_score"].mean()),
		"p90_risk_score": float(np.quantile(exposure["risk_score"], 0.90)),
		"used_proxy_external_data": bool(cfg.population_grid_csv is None),
	}
	summary_path = os.path.join(cfg.out_dir, "aots_humanitarian_risk_summary.csv")
	pd.DataFrame([summary]).to_csv(summary_path, index=False)
	print(f"Saved: {summary_path}")

	print("Done.")


if __name__ == "__main__":
	main()
