import os
from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle


@dataclass
class VizCFG:
	output_dir: str = "/Users/agd9c/Downloads/UNICEF_DATA/outputs"
	exposure_csv: str = "/Users/agd9c/Downloads/UNICEF_DATA/outputs/aots_population_exposure_by_cone.csv"
	horizon_csv: str = "/Users/agd9c/Downloads/UNICEF_DATA/outputs/aots_expected_exposure_by_horizon.csv"
	region_csv: str = "/Users/agd9c/Downloads/UNICEF_DATA/outputs/aots_region_risk_scores.csv"

	frames_dir: str = "/Users/agd9c/Downloads/UNICEF_DATA/outputs/video_frames"
	gif_path: str = "/Users/agd9c/Downloads/UNICEF_DATA/outputs/humanitarian_risk_animation.gif"

	# Select storm with highest max exposure if empty.
	track_id: str = ""
	max_frames: int = 240
	fps: int = 8

	# Map zoom padding (degrees)
	pad_deg: float = 4.0


cfg = VizCFG()


def _region_id_from_lat_lon(lat: float, lon: float) -> str:
	lat_bin = int(np.floor((lat + 90.0) / 10.0))
	lon_bin = int(np.floor((lon + 180.0) / 10.0))
	return f"R_{lat_bin}_{lon_bin}"


def _downsample_rows(df: pd.DataFrame, max_frames: int) -> pd.DataFrame:
	if len(df) <= max_frames:
		return df
	idx = np.linspace(0, len(df) - 1, max_frames).round().astype(int)
	return df.iloc[np.unique(idx)].reset_index(drop=True)


def _circle_radius_deg(lat: float, radius_km: float) -> tuple:
	# Approx conversion from km to degrees for drawing circles.
	deg_lat = radius_km / 111.32
	cos_lat = np.cos(np.radians(np.clip(lat, -89.0, 89.0)))
	deg_lon = radius_km / (111.32 * max(cos_lat, 0.15))
	return deg_lat, deg_lon


def _load_inputs() -> tuple:
	exposure = pd.read_csv(cfg.exposure_csv)
	exposure["forecast_time"] = pd.to_datetime(exposure["forecast_time"], utc=True, errors="coerce")
	exposure = exposure.dropna(subset=["forecast_time", "center_lat", "center_lon", "lead_time"]).copy()
	exposure["lead_time"] = exposure["lead_time"].astype(int)

	horizon = pd.read_csv(cfg.horizon_csv) if os.path.exists(cfg.horizon_csv) else pd.DataFrame()
	regions = pd.read_csv(cfg.region_csv) if os.path.exists(cfg.region_csv) else pd.DataFrame()
	return exposure, horizon, regions


def _choose_track(exposure: pd.DataFrame) -> str:
	if cfg.track_id and cfg.track_id in set(exposure["track_id"].astype(str)):
		return cfg.track_id
	by_track = exposure.groupby("track_id", as_index=False)["estimated_population_exposed"].max()
	if by_track.empty:
		raise RuntimeError("No data found in exposure CSV.")
	return str(by_track.sort_values("estimated_population_exposed", ascending=False).iloc[0]["track_id"])


def _build_sequence(exposure: pd.DataFrame, track_id: str) -> pd.DataFrame:
	seq = exposure[exposure["track_id"].astype(str) == str(track_id)].copy()
	seq = seq.sort_values(["forecast_time", "lead_time"]).reset_index(drop=True)
	seq = _downsample_rows(seq, cfg.max_frames)
	seq["region_id_proxy"] = [
		_region_id_from_lat_lon(float(a), float(b))
		for a, b in zip(seq["center_lat"].to_numpy(), seq["center_lon"].to_numpy())
	]
	return seq


def _make_frame(
	frame_idx: int,
	row: pd.Series,
	seq: pd.DataFrame,
	horizon: pd.DataFrame,
	regions: pd.DataFrame,
	risk_min: float,
	risk_max: float,
) -> str:
	fig = plt.figure(figsize=(14, 8), dpi=110)
	gs = fig.add_gridspec(2, 2, width_ratios=[1.9, 1.1], height_ratios=[1, 1], wspace=0.22, hspace=0.25)
	ax_map = fig.add_subplot(gs[:, 0])
	ax_h = fig.add_subplot(gs[0, 1])
	ax_r = fig.add_subplot(gs[1, 1])

	# -------- Map panel --------
	ax_map.scatter(seq["center_lon"], seq["center_lat"], s=7, c="#bbbbbb", alpha=0.45, label="Centers")

	current_risk = float(row["risk_score"])
	risk_norm = (current_risk - risk_min) / max(risk_max - risk_min, 1e-6)
	color = plt.cm.plasma(np.clip(risk_norm, 0.0, 1.0))

	# Draw uncertainty cone as ellipse in degree space.
	deg_lat, deg_lon = _circle_radius_deg(float(row["center_lat"]), float(row["cone_radius_km"]))
	# Use lon-based radius for width, lat-based radius for height.
	circle = Circle(
		(float(row["center_lon"]), float(row["center_lat"])),
		radius=deg_lon,
		facecolor=color,
		edgecolor="black",
		alpha=0.20,
		lw=1.2,
	)
	ax_map.add_patch(circle)

	ax_map.scatter([row["center_lon"]], [row["center_lat"]], s=55, c=[color], edgecolors="black", zorder=5)

	# Path history up to current frame.
	hist = seq.iloc[: frame_idx + 1]
	ax_map.plot(hist["center_lon"], hist["center_lat"], color="#333333", lw=1.2, alpha=0.7)

	# Dynamic zoom around selected storm.
	lon_min = float(seq["center_lon"].min() - cfg.pad_deg)
	lon_max = float(seq["center_lon"].max() + cfg.pad_deg)
	lat_min = float(seq["center_lat"].min() - cfg.pad_deg)
	lat_max = float(seq["center_lat"].max() + cfg.pad_deg)
	ax_map.set_xlim(lon_min, lon_max)
	ax_map.set_ylim(lat_min, lat_max)
	ax_map.grid(alpha=0.25, linestyle="--")
	ax_map.set_xlabel("Longitude")
	ax_map.set_ylabel("Latitude")
	ax_map.set_title("Storm Uncertainty Cone + Exposure")

	stamp = pd.to_datetime(row["forecast_time"]).strftime("%Y-%m-%d %H:%M UTC")
	info = (
		f"Track: {row['track_id']}\n"
		f"Forecast: {stamp}\n"
		f"Lead: {int(row['lead_time'])}h\n"
		f"Cone radius: {float(row['cone_radius_km']):.1f} km\n"
		f"Exposed pop: {float(row['estimated_population_exposed']):,.0f}\n"
		f"Risk score: {current_risk:.1f}/100\n"
		f"Region: {row['region_id_proxy']}"
	)
	ax_map.text(
		0.015,
		0.985,
		info,
		transform=ax_map.transAxes,
		va="top",
		ha="left",
		fontsize=9,
		bbox=dict(facecolor="white", alpha=0.8, edgecolor="#cccccc"),
	)

	# -------- Horizon panel --------
	if not horizon.empty:
		h = horizon.sort_values("lead_time")
		ax_h.plot(h["lead_time"], h["expected_exposure"], marker="o", color="#1565c0", lw=1.8)
		ax_h.set_title("Expected Exposure by Forecast Horizon")
		ax_h.set_xlabel("Lead time (hours)")
		ax_h.set_ylabel("Expected exposed population")
		ax_h.grid(alpha=0.25, linestyle="--")

		curr_lead = int(row["lead_time"])
		if curr_lead in set(h["lead_time"].astype(int)):
			y = float(h.loc[h["lead_time"].astype(int) == curr_lead, "expected_exposure"].iloc[0])
			ax_h.scatter([curr_lead], [y], s=80, color="crimson", zorder=6, label="Current frame")
			ax_h.legend(loc="upper left", fontsize=8)
	else:
		ax_h.axis("off")
		ax_h.text(0.1, 0.5, "No horizon summary file found", fontsize=11)

	# -------- Region impact panel --------
	if not regions.empty:
		r = regions.sort_values("mean_risk_score", ascending=False).head(10).copy()
		labels = r["region_id"].astype(str).tolist()
		vals = r["mean_risk_score"].to_numpy(dtype=float)
		colors = ["#90caf9"] * len(r)
		cur_region = str(row["region_id_proxy"])
		if cur_region in labels:
			colors[labels.index(cur_region)] = "#ef5350"

		ax_r.barh(labels[::-1], vals[::-1], color=colors[::-1])
		ax_r.set_xlabel("Mean risk score")
		ax_r.set_title("Most Affected Regions (risk ranking)")
		ax_r.grid(axis="x", alpha=0.25, linestyle="--")
		ax_r.text(
			0.01,
			0.02,
			f"Current cone region: {cur_region}",
			transform=ax_r.transAxes,
			fontsize=9,
			va="bottom",
			ha="left",
		)
	else:
		ax_r.axis("off")
		ax_r.text(0.1, 0.5, "No region summary file found", fontsize=11)

	fig.suptitle("Humanitarian Risk Forecast Visualization", fontsize=14, weight="bold")

	os.makedirs(cfg.frames_dir, exist_ok=True)
	frame_path = os.path.join(cfg.frames_dir, f"frame_{frame_idx:04d}.png")
	fig.savefig(frame_path, bbox_inches="tight")
	plt.close(fig)
	return frame_path


def _export_gif(frame_paths: List[str], gif_path: str, fps: int) -> None:
	try:
		import imageio.v2 as imageio
	except Exception as e:
		raise RuntimeError(
			"imageio is required to create GIF. Install with: pip install imageio pillow"
		) from e

	images = [imageio.imread(p) for p in frame_paths]
	duration = 1.0 / max(fps, 1)
	imageio.mimsave(gif_path, images, duration=duration, loop=0)


def main() -> None:
	exposure, horizon, regions = _load_inputs()
	track_id = _choose_track(exposure)
	seq = _build_sequence(exposure, track_id)

	if seq.empty:
		raise RuntimeError("No rows available for selected track.")

	risk_min = float(seq["risk_score"].min())
	risk_max = float(seq["risk_score"].max())

	print(f"Selected track: {track_id}")
	print(f"Frames to render: {len(seq)}")

	frame_paths: List[str] = []
	for i, row in seq.iterrows():
		frame_paths.append(_make_frame(i, row, seq, horizon, regions, risk_min, risk_max))

	_export_gif(frame_paths, cfg.gif_path, cfg.fps)
	print(f"Saved GIF: {cfg.gif_path}")
	print(f"Saved frames: {cfg.frames_dir}")


if __name__ == "__main__":
	main()
