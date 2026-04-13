import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go

INPUT_CSV = "/Users/agd9c/Downloads/UNICEF_DATA/outputs/aots_population_exposure_by_cone.csv"
OUT_HTML = "/Users/agd9c/Downloads/UNICEF_DATA/outputs/world_exact_positions_animation.html"
OUT_HTML_OFFLINE = "/Users/agd9c/Downloads/UNICEF_DATA/outputs/world_exact_positions_animation_offline.html"
OUT_POINTS_CSV = "/Users/agd9c/Downloads/UNICEF_DATA/outputs/world_exact_positions_points.csv"


def _region_proxy(lat: float, lon: float) -> str:
    return f"R_{int((lat + 90)//10)}_{int((lon + 180)//10)}"


def main() -> None:
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Missing input: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)
    required = [
        "track_id", "forecast_time", "lead_time", "center_lat", "center_lon",
        "cone_radius_km", "estimated_population_exposed", "risk_score"
    ]
    miss = [c for c in required if c not in df.columns]
    if miss:
        raise ValueError(f"Missing columns: {miss}")

    df["forecast_time"] = pd.to_datetime(df["forecast_time"], utc=True, errors="coerce")
    df = df.dropna(subset=["forecast_time", "center_lat", "center_lon", "lead_time"]).copy()
    df["lead_time"] = pd.to_numeric(df["lead_time"], errors="coerce").astype(int)

    df["valid_time_est"] = df["forecast_time"] + pd.to_timedelta(df["lead_time"], unit="h")
    df["valid_time_key"] = df["valid_time_est"].dt.strftime("%Y-%m-%d %H:%M UTC")
    df["region_proxy"] = [_region_proxy(a, b) for a, b in zip(df["center_lat"], df["center_lon"])]

    # exact point export for audit/use in reports
    points = df[[
        "track_id", "forecast_time", "valid_time_est", "lead_time", "center_lat", "center_lon",
        "cone_radius_km", "estimated_population_exposed", "risk_score", "region_proxy"
    ]].copy()
    points = points.sort_values(["valid_time_est", "track_id", "lead_time"]).reset_index(drop=True)
    points.to_csv(OUT_POINTS_CSV, index=False)

    # Marker size from cone radius (visual proxy)
    radius = pd.to_numeric(df["cone_radius_km"], errors="coerce").fillna(0.0)
    size = np.clip(radius / 22.0, 5.0, 28.0)
    df["marker_size"] = size

    frames = []
    frame_keys = sorted(df["valid_time_key"].unique())

    for k in frame_keys:
        d = df[df["valid_time_key"] == k].copy()
        hover = (
            "Track: " + d["track_id"].astype(str)
            + "<br>Valid time: " + d["valid_time_key"].astype(str)
            + "<br>Lead: " + d["lead_time"].astype(str) + "h"
            + "<br>Lat: " + d["center_lat"].map(lambda x: f"{x:.4f}")
            + "<br>Lon: " + d["center_lon"].map(lambda x: f"{x:.4f}")
            + "<br>Cone radius: " + d["cone_radius_km"].map(lambda x: f"{x:.1f} km")
            + "<br>Exposed pop: " + d["estimated_population_exposed"].map(lambda x: f"{x:,.0f}")
            + "<br>Risk score: " + d["risk_score"].map(lambda x: f"{x:.1f}")
            + "<br>Region: " + d["region_proxy"].astype(str)
        )

        trace = go.Scattergeo(
            lon=d["center_lon"],
            lat=d["center_lat"],
            mode="markers",
            marker=dict(
                size=d["marker_size"],
                color=d["risk_score"],
                colorscale="Turbo",
                cmin=float(df["risk_score"].min()),
                cmax=float(df["risk_score"].max()),
                opacity=0.82,
                line=dict(color="black", width=0.6),
                colorbar=dict(title="Risk score")
            ),
            text=hover,
            hoverinfo="text",
            name="Storm position",
        )

        frames.append(go.Frame(data=[trace], name=k))

    if not frames:
        raise RuntimeError("No frames created from data.")

    fig = go.Figure(data=frames[0].data, frames=frames)
    fig.update_layout(
        title=(
            "Exact Predicted Storm Positions in the World"
            "<br><sup>Hover points for exact latitude/longitude, time, exposure, and risk</sup>"
        ),
        geo=dict(
            projection_type="natural earth",
            showcountries=True,
            countrycolor="rgb(120,120,120)",
            showcoastlines=True,
            coastlinecolor="rgb(80,80,80)",
            showland=True,
            landcolor="rgb(235,235,225)",
            showocean=True,
            oceancolor="rgb(198,220,239)",
            lataxis=dict(showgrid=True, gridcolor="rgba(120,120,120,0.2)"),
            lonaxis=dict(showgrid=True, gridcolor="rgba(120,120,120,0.2)"),
        ),
        width=1320,
        height=760,
        margin=dict(l=10, r=10, t=70, b=20),
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "x": 0.02,
                "y": 1.05,
                "buttons": [
                    {
                        "label": "Play",
                        "method": "animate",
                        "args": [None, {"frame": {"duration": 120, "redraw": True}, "fromcurrent": True}],
                    },
                    {
                        "label": "Pause",
                        "method": "animate",
                        "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}],
                    },
                ],
            }
        ],
        sliders=[
            {
                "x": 0.02,
                "y": 0.01,
                "len": 0.95,
                "currentvalue": {"prefix": "Valid time: "},
                "steps": [
                    {
                        "label": k,
                        "method": "animate",
                        "args": [[k], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
                    }
                    for k in frame_keys
                ],
            }
        ],
    )

    # Web version (smaller file, requires internet for Plotly JS CDN)
    fig.write_html(OUT_HTML, include_plotlyjs="cdn")
    # Offline version (bigger file, opens by double-click with no internet/server)
    fig.write_html(OUT_HTML_OFFLINE, include_plotlyjs=True)
    print(f"Saved interactive map: {OUT_HTML}")
    print(f"Saved offline interactive map: {OUT_HTML_OFFLINE}")
    print(f"Saved exact points CSV: {OUT_POINTS_CSV}")


if __name__ == "__main__":
    main()
