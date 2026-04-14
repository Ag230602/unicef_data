#!/usr/bin/env python3
"""
UNICEF Humanitarian Risk Command Dashboard
══════════════════════════════════════════════
Run:
    pip install dash plotly
    python humanitarian_dashboard.py

Then open:  http://127.0.0.1:8050
"""

import math, sys, subprocess

# ── auto-install ──────────────────────────────────────────────────────────────
for _pkg in ["dash", "plotly"]:
    try:
        __import__(_pkg)
    except ImportError:
        print(f"Installing {_pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", _pkg])

from dash import Dash, dcc, html, Input, Output, State, no_update, Patch
import plotly.graph_objects as go
from datetime import datetime, timezone


# ══════════════════════════════════════════════════════════════════════════════
#  DATA
# ══════════════════════════════════════════════════════════════════════════════

STORMS = [
    dict(name="DITWAH",    color="#ff4757", region="Bay of Bengal",
         lats=[7.37,7.59,8.10,8.53,8.82,9.07,9.41,9.55,9.81,10.12,10.31,10.56,
               10.72,10.96,11.13,11.47,11.69,11.97,12.13,12.25,12.40,12.52],
         lons=[81.05,81.51,81.44,80.95,80.89,81.05,80.54,80.45,80.35,80.62,80.75,80.90,
               81.08,81.17,81.29,81.33,81.28,81.06,81.18,81.10,80.50,80.17],
         maxPop=6490264, maxRisk=77.2),
    dict(name="FINA",      color="#ffa502", region="Timor Sea",
         lats=[-9.78,-9.55,-9.55,-9.80,-9.86,-10.02,-10.04,-10.06,-10.30,-10.52,
                -11.03,-11.40,-11.70,-11.87,-12.11,-12.36,-12.53,-12.93,-13.48,
                -13.61,-14.08,-14.17,-14.29,-14.49],
         lons=[131.95,132.23,132.67,133.06,133.24,133.03,133.19,132.80,132.51,132.37,
               132.12,131.82,131.58,131.16,130.65,130.25,129.79,129.46,129.07,128.66,
               128.08,127.76,127.85,127.40],
         maxPop=3800000, maxRisk=74.0),
    dict(name="FUNG-WONG", color="#2ed573", region="W. Pacific",
         lats=[9.74,9.77,10.24,11.16,11.55,12.02,12.25,12.25,12.49,12.92,12.89,13.35,
               14.01,14.76,15.80,16.56,16.90,17.40,18.12,18.45,19.26,20.04,20.76,21.14,
               21.51,21.66,21.99,23.71,24.92],
         lons=[140.60,140.09,139.94,138.93,138.04,136.84,135.08,133.76,132.35,130.39,
               128.17,126.51,124.84,123.38,122.09,120.04,119.34,119.05,118.73,118.63,
               118.33,118.46,118.75,118.88,119.18,119.74,120.78,121.88,122.94],
         maxPop=5200000, maxRisk=73.5),
    dict(name="KALMAEGI",  color="#1e90ff", region="S. China Sea",
         lats=[10.75,11.50,11.34,11.23,10.81,10.62,10.80,10.66,10.75,10.85,10.97,11.10,
               11.37,11.77,12.31,13.05,13.19,13.25,13.83,14.40,14.82,15.44,15.69],
         lons=[136.39,134.80,133.46,130.18,128.53,127.28,126.20,124.81,123.15,122.27,
               121.21,120.17,119.10,117.58,116.18,114.46,112.49,110.88,109.50,107.41,
               105.81,105.33,103.91],
         maxPop=4800000, maxRisk=72.0),
    dict(name="KOTO",      color="#a29bfe", region="S. China Sea",
         lats=[12.05,12.55,12.12,12.56,12.98,13.08,12.85,12.45,12.26,12.22,12.29,12.39,
               12.68,13.04,13.15,13.45,13.62,13.98,14.43,14.58,14.78,14.55,14.62],
         lons=[119.11,117.76,116.32,115.61,114.92,114.28,113.80,113.95,113.33,113.07,
               112.69,112.59,112.52,112.45,112.10,112.05,112.07,112.19,112.03,112.06,
               111.73,111.70,111.43],
         maxPop=3200000, maxRisk=70.5),
    dict(name="MELISSA",   color="#ff6b81", region="Caribbean Sea",
         lats=[14.91,15.28,15.36,15.73,15.63,15.67,15.86,16.15,16.54,16.26,16.30,16.44,16.51],
         lons=[-75.01,-75.08,-75.14,-75.41,-75.63,-74.88,-74.94,-75.05,-75.36,-75.54,
                -76.15,-76.37,-76.72],
         maxPop=2800000, maxRisk=68.0),
    dict(name="GEZANI",    color="#00cec9", region="Mozambique Channel",
         lats=[-18.26,-18.10,-18.15,-18.09,-18.83,-19.02,-18.93,-19.39,-19.93,-20.40,
                -20.64,-21.15,-21.49,-22.22,-22.95,-24.00],
         lons=[51.00,50.10,49.16,47.80,45.29,44.33,43.47,41.98,41.07,39.82,38.87,37.65,
               36.96,36.17,35.83,35.65],
         maxPop=1900000, maxRisk=65.0),
    dict(name="DUDZAI",    color="#fd79a8", region="Indian Ocean",
         lats=[-16.87,-17.45,-18.23,-19.55,-20.81],
         lons=[73.40,70.34,67.45,64.34,63.58],
         maxPop=1200000, maxRisk=63.0),
]

ALL_REGIONS = [
    dict(id="R_8_31",  pop=1879852, risk=75.36, p90=76.53, cones=19),
    dict(id="R_9_26",  pop=1220146, risk=74.65, p90=75.67, cones=20),
    dict(id="R_7_30",  pop=3709698, risk=74.29, p90=76.13, cones=99),
    dict(id="R_7_31",  pop=2478108, risk=74.13, p90=77.71, cones=38),
    dict(id="R_10_29", pop=4667615, risk=73.87, p90=78.61, cones=218),
    dict(id="R_10_9",  pop=4432656, risk=73.38, p90=73.38, cones=1),
    dict(id="R_10_10", pop=3916870, risk=72.33, p90=75.03, cones=100),
    dict(id="R_10_26", pop=2177408, risk=71.71, p90=76.55, cones=107),
    dict(id="R_10_6",  pop=1031304, risk=70.86, p90=72.04, cones=15),
    dict(id="R_10_30", pop=974805,  risk=70.65, p90=74.23, cones=72),
    dict(id="R_9_30",  pop=409128,  risk=70.63, p90=71.91, cones=9),
    dict(id="R_10_32", pop=413112,  risk=70.44, p90=70.59, cones=2),
    dict(id="R_9_32",  pop=334912,  risk=70.06, p90=70.26, cones=3),
    dict(id="R_10_31", pop=463306,  risk=69.46, p90=70.68, cones=33),
    dict(id="R_11_29", pop=1649229, risk=66.82, p90=68.84, cones=25),
    dict(id="R_6_22",  pop=2912567, risk=66.56, p90=70.37, cones=9),
    dict(id="R_10_28", pop=1447357, risk=66.00, p90=73.76, cones=68),
    dict(id="R_10_5",  pop=722547,  risk=65.58, p90=71.30, cones=51),
    dict(id="R_9_28",  pop=319518,  risk=65.38, p90=76.26, cones=33),
    dict(id="R_6_21",  pop=1903430, risk=65.31, p90=68.97, cones=64),
]

HORIZONS = [
    dict(h=6,  exp=987841,  p90=2240284, re=67.94, rp=74.23),
    dict(h=12, exp=1154520, p90=2532746, re=68.80, rp=74.67),
    dict(h=24, exp=1593987, p90=3537966, re=68.47, rp=75.33),
    dict(h=48, exp=2542446, p90=6246027, re=68.15, rp=76.87),
    dict(h=72, exp=3400938, p90=9330418, re=67.88, rp=77.90),
    dict(h=96, exp=3830991, p90=9269411, re=65.62, rp=78.39),
]

LEAD_LABELS   = ["6h","12h","24h","48h","72h","96h"]
MAX_STEPS     = max(len(s["lats"]) for s in STORMS)

# Region lat/lon for 3D globe markers (approximate centroids)
_REGION_COORDS = [
    (10.5,131.5),(9.5,126.0),(7.5,130.5),(7.8,131.2),(10.2,129.5),
    (10.1,9.5),(10.0,10.1),(10.3,10.4),(10.1,9.8),(10.4,10.6),
    (9.4,9.7),(10.5,10.5),(9.5,9.6),(10.4,10.5),(11.2,9.4),
    (6.3,22.1),(10.3,9.5),(10.1,9.3),(9.3,9.6),(6.2,21.2),
]


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

BG   = "rgba(0,0,0,0)"
FONT = dict(family="Inter, sans-serif", color="#6a8cb8", size=11)

def _base(**kw):
    d = dict(paper_bgcolor=BG, plot_bgcolor=BG, font=FONT,
             margin=dict(l=50, r=20, t=20, b=40))
    d.update(kw)
    return d

def fmt_pop(n):
    if n >= 1e6: return f"{n/1e6:.2f}M"
    if n >= 1e3: return f"{round(n/1e3)}K"
    return str(round(n))

def circle_pts(lat0, lon0, deg_r=2.5, n=52):
    pts = []
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        lat = lat0 + deg_r * math.sin(a)
        lon = lon0 + deg_r * math.cos(a) / max(0.01, math.cos(math.radians(lat0)))
        pts.append((lat, lon))
    return pts

def ll_to_xyz(lat, lon, r=1.015):
    ph, th = math.radians(lat), math.radians(lon)
    return r*math.cos(ph)*math.cos(th), r*math.cos(ph)*math.sin(th), r*math.sin(ph)


# ══════════════════════════════════════════════════════════════════════════════
#  CHART BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def build_globe(step=None):
    """Animated storm-track geo globe."""
    traces = []
    for s in STORMS:
        n    = len(s["lats"]) if step is None else min(int(step), len(s["lats"]))
        lats = s["lats"][:n];  lons = s["lons"][:n]
        sz   = [5]*n;          sym  = ["circle"]*n
        if n: sz[-1] = 15;     sym[-1] = "star"

        traces.append(go.Scattergeo(
            lat=lats, lon=lons, mode="lines", showlegend=False, hoverinfo="skip",
            line=dict(color=s["color"], width=2.8)))

        traces.append(go.Scattergeo(
            lat=lats, lon=lons, mode="markers",
            name=f"{s['name']} — {s['region']}", showlegend=True,
            marker=dict(size=sz, color=s["color"], symbol=sym,
                        line=dict(color="white", width=0.8)),
            hovertemplate=(f"<b>{s['name']}</b><br>%{{lat:.2f}}, %{{lon:.2f}}<br>"
                           f"{s['region']}<br>Risk: {s['maxRisk']}<extra></extra>")))

        if step is None or n >= len(s["lats"]):
            ring = circle_pts(s["lats"][-1], s["lons"][-1])
            traces.append(go.Scattergeo(
                lat=[p[0] for p in ring], lon=[p[1] for p in ring],
                mode="lines", showlegend=False, hoverinfo="skip", opacity=0.5,
                line=dict(color=s["color"], width=1.2, dash="dot")))

    return go.Figure(data=traces, layout=go.Layout(
        **_base(margin=dict(l=0,r=0,t=0,b=0), showlegend=True,
                legend=dict(orientation="h", x=0, y=-0.06, bgcolor=BG,
                            font=dict(size=9, color="#6a8cb8")),
                geo=dict(projection=dict(type="natural earth"),
                         showland=True,  landcolor="#142030",
                         showocean=True, oceancolor="#060d1c",
                         showlakes=True, lakecolor="#0a1525",
                         showcoastlines=True, coastlinecolor="#1e3050",
                         showcountries=True, countrycolor="#192840",
                         showframe=False, bgcolor=BG, resolution=50))))


def build_gauge():
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta", value=67.86,
        delta=dict(reference=60, increasing=dict(color="#ff4757")),
        title=dict(text="PORTFOLIO RISK INDEX",
                   font=dict(size=11, color="#6a8cb8", family="Rajdhani, sans-serif")),
        gauge=dict(
            axis=dict(range=[0,100], tickwidth=1, tickcolor="#2d4a70",
                      tickfont=dict(size=8, color="#6a8cb8")),
            bar=dict(color="#ff5e3a", thickness=0.25),
            bgcolor=BG, borderwidth=0,
            steps=[dict(range=[0,40],   color="rgba(48,209,88,.12)"),
                   dict(range=[40,60],  color="rgba(255,204,0,.10)"),
                   dict(range=[60,80],  color="rgba(255,149,0,.12)"),
                   dict(range=[80,100], color="rgba(255,59,48,.18)")],
            threshold=dict(line=dict(color="#ffcc00", width=3), thickness=0.7, value=76.14)),
        number=dict(font=dict(size=38, color="#ff5e3a", family="Rajdhani, sans-serif"))))
    fig.update_layout(**_base(margin=dict(l=25,r=25,t=30,b=10), height=200))
    return fig


def build_risk_regions(sort_by="risk", min_risk=0):
    regions = sorted(
        [r for r in ALL_REGIONS if r["risk"] >= min_risk],
        key=lambda r: -r.get(sort_by, r["risk"]))
    colors = ["#ff4757" if r["risk"]>=74 else "#ffa502" if r["risk"]>=70 else "#ffcc00"
              for r in regions]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[r["risk"] for r in regions], y=[r["id"] for r in regions],
        orientation="h", name="Risk Score",
        marker=dict(color=colors, opacity=0.85),
        hovertemplate="<b>%{y}</b><br>Risk: %{x:.2f}<extra></extra>"))
    fig.add_trace(go.Bar(
        x=[r["p90"] for r in regions], y=[r["id"] for r in regions],
        orientation="h", name="P90 Risk",
        marker=dict(color="rgba(255,204,0,.25)", opacity=0.7),
        hovertemplate="<b>%{y}</b><br>P90: %{x:.2f}<extra></extra>"))
    fig.update_layout(**_base(
        barmode="overlay",
        xaxis=dict(range=[60,82], title="Risk Score", gridcolor="rgba(255,255,255,.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,.04)", tickfont=dict(size=9)),
        legend=dict(orientation="h", x=0, y=1.08, bgcolor=BG, font=dict(size=9)),
        showlegend=True, margin=dict(l=75,r=20,t=10,b=40)))
    return fig


def build_risk_scatter():
    fig = go.Figure()
    for s in STORMS:
        fig.add_trace(go.Scatter(
            x=[s["maxPop"]/1e6], y=[s["maxRisk"]],
            mode="markers+text",
            marker=dict(size=max(8, s["maxPop"]/600000), color=s["color"], opacity=0.85,
                        line=dict(color="white", width=1)),
            text=[s["name"]], textposition="top center",
            textfont=dict(size=9, color=s["color"]),
            name=s["name"],
            hovertemplate=f"<b>{s['name']}</b><br>Pop: %{{x:.2f}}M<br>Risk: %{{y:.1f}}<extra></extra>"))
    fig.update_layout(**_base(
        showlegend=False,
        xaxis=dict(title="Max Population at Risk (M)", gridcolor="rgba(255,255,255,.05)", zeroline=False),
        yaxis=dict(title="Max Risk Score", gridcolor="rgba(255,255,255,.05)", zeroline=False),
        margin=dict(l=55,r=20,t=10,b=45)))
    return fig


def build_rescue_3d(rot_angle=0.0):
    """3D sphere globe with region+storm markers."""
    traces = []
    # Wireframe sphere
    u_pts = [i * math.pi / 18 for i in range(19)]
    v_pts = [i * 2 * math.pi / 36 for i in range(37)]
    for u in u_pts:
        xs = [math.sin(u)*math.cos(v) for v in v_pts]
        ys = [math.sin(u)*math.sin(v) for v in v_pts]
        zs = [math.cos(u)]*len(v_pts)
        traces.append(go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", showlegend=False,
                                   hoverinfo="skip", line=dict(color="rgba(0,170,255,0.07)", width=1)))
    for v in v_pts[::3]:
        xs = [math.sin(u)*math.cos(v) for u in u_pts]
        ys = [math.sin(u)*math.sin(v) for u in u_pts]
        zs = [math.cos(u) for u in u_pts]
        traces.append(go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", showlegend=False,
                                   hoverinfo="skip", line=dict(color="rgba(0,170,255,0.07)", width=1)))
    # Region markers
    for i, r in enumerate(ALL_REGIONS):
        lat, lon = _REGION_COORDS[i % len(_REGION_COORDS)]
        x, y, z  = ll_to_xyz(lat, lon)
        color     = "#ff4757" if r["risk"]>=74 else "#ffa502" if r["risk"]>=70 else "#ffcc00"
        traces.append(go.Scatter3d(
            x=[x], y=[y], z=[z], mode="markers", name=r["id"],
            marker=dict(size=max(4, r["pop"]/900000), color=color, opacity=0.85,
                        line=dict(color="white", width=0.5)),
            hovertemplate=(f"<b>{r['id']}</b><br>Risk: {r['risk']:.2f}<br>"
                           f"Pop: {fmt_pop(r['pop'])}<br>P90: {r['p90']:.2f}<extra></extra>")))
    # Storm markers
    for s in STORMS:
        x, y, z = ll_to_xyz(s["lats"][-1], s["lons"][-1])
        traces.append(go.Scatter3d(
            x=[x], y=[y], z=[z], mode="markers", name=s["name"],
            marker=dict(size=10, color=s["color"], symbol="diamond",
                        line=dict(color="white", width=1)),
            hovertemplate=f"<b>{s['name']}</b><br>{s['region']}<br>Risk: {s['maxRisk']}<extra></extra>"))

    rad = math.radians(rot_angle)
    return go.Figure(data=traces, layout=go.Layout(
        paper_bgcolor="#020810", plot_bgcolor="#020810", font=FONT,
        margin=dict(l=0,r=0,t=0,b=0), height=510, showlegend=False,
        scene=dict(
            bgcolor="#020810",
            xaxis=dict(visible=False, showgrid=False),
            yaxis=dict(visible=False, showgrid=False),
            zaxis=dict(visible=False, showgrid=False),
            camera=dict(eye=dict(x=1.4*math.cos(rad), y=1.4*math.sin(rad), z=0.45),
                        up=dict(x=0, y=0, z=1)),
            aspectmode="cube")))


def build_rescue_pop():
    ss = sorted(STORMS, key=lambda s: -s["maxPop"])
    fig = go.Figure(go.Bar(
        orientation="h",
        y=[s["name"]     for s in ss],
        x=[s["maxPop"]/1e6 for s in ss],
        marker=dict(color=[s["color"] for s in ss], opacity=0.85),
        hovertemplate="<b>%{y}</b><br>Pop: %{x:.2f}M<extra></extra>"))
    fig.update_layout(**_base(
        xaxis=dict(title="Population (M)", gridcolor="rgba(255,255,255,.04)", zeroline=False),
        yaxis=dict(gridcolor="rgba(255,255,255,.04)", tickfont=dict(size=11, color="#ddeeff")),
        showlegend=False, margin=dict(l=110,r=20,t=10,b=40)))
    return fig


def build_exposure(idx=5):
    h = HORIZONS[idx]
    fig = go.Figure()
    # Shaded fill
    fig.add_trace(go.Scatter(x=LEAD_LABELS, y=[d["p90"]/1e6 for d in HORIZONS],
        fill="tozeroy", fillcolor="rgba(255,204,0,.07)",
        line=dict(color="transparent"), showlegend=False, hoverinfo="skip", name=""))
    fig.add_trace(go.Scatter(x=LEAD_LABELS, y=[d["exp"]/1e6 for d in HORIZONS],
        fill="tozeroy", fillcolor="rgba(0,170,255,.12)",
        line=dict(color="transparent"), showlegend=False, hoverinfo="skip", name=""))
    # Lines
    fig.add_trace(go.Scatter(x=LEAD_LABELS, y=[d["exp"]/1e6 for d in HORIZONS],
        mode="lines+markers", name="Expected",
        line=dict(color="#00aaff", width=3),
        marker=dict(size=9, color="#00aaff", line=dict(color="white", width=1.5)),
        hovertemplate="Lead %{x}<br><b>Exp: %{y:.2f}M</b><extra></extra>"))
    fig.add_trace(go.Scatter(x=LEAD_LABELS, y=[d["p90"]/1e6 for d in HORIZONS],
        mode="lines+markers", name="P90 Worst-Case",
        line=dict(color="#ffcc00", width=2, dash="dash"),
        marker=dict(size=7, color="#ffcc00"),
        hovertemplate="Lead %{x}<br><b>P90: %{y:.2f}M</b><extra></extra>"))
    fig.update_layout(**_base(
        margin=dict(l=60,r=20,t=30,b=40),
        xaxis=dict(title="Forecast Lead Time", gridcolor="rgba(255,255,255,.05)"),
        yaxis=dict(title="Population Exposed (M)", gridcolor="rgba(255,255,255,.05)", zeroline=False),
        legend=dict(orientation="h", x=0, y=1.08, bgcolor=BG, font=dict(size=11)),
        showlegend=True,
        shapes=[dict(type="line", x0=idx, x1=idx, y0=0, y1=12,
                     line=dict(color="#00e5ff", width=2, dash="dash"))],
        annotations=[
            dict(x=LEAD_LABELS[idx], y=h["p90"]/1e6+0.4,
                 text=f"\u25b2 {fmt_pop(h['p90'])} P90",
                 showarrow=False, font=dict(size=10, color="#ffcc00")),
            dict(x=LEAD_LABELS[idx], y=h["exp"]/1e6+0.4,
                 text=f"\u25cf {fmt_pop(h['exp'])} Exp.",
                 showarrow=False, font=dict(size=10, color="#00aaff"))]))
    return fig


def build_coastal():
    cf = 0.72
    fig = go.Figure()
    fig.add_trace(go.Bar(x=LEAD_LABELS, y=[d["exp"]*cf/1e6 for d in HORIZONS],
        name="Coastal (72%)", marker=dict(color="#1e90ff", opacity=0.85),
        hovertemplate="Lead %{x}<br>Coastal: %{y:.2f}M<extra></extra>"))
    fig.add_trace(go.Bar(x=LEAD_LABELS, y=[d["exp"]*(1-cf)/1e6 for d in HORIZONS],
        name="Inland (28%)", marker=dict(color="#30d158", opacity=0.85),
        hovertemplate="Lead %{x}<br>Inland: %{y:.2f}M<extra></extra>"))
    fig.update_layout(**_base(
        barmode="stack",
        xaxis=dict(gridcolor="rgba(255,255,255,.04)"),
        yaxis=dict(title="Pop (M)", gridcolor="rgba(255,255,255,.04)", zeroline=False),
        legend=dict(orientation="h", x=0, y=1.08, bgcolor=BG, font=dict(size=10)),
        showlegend=True, margin=dict(l=55,r=20,t=30,b=40)))
    return fig


def build_gantt():
    tasks = [
        dict(task="Emergency Water",   start=0,  end=24, color="#1e90ff", qty="7,662 tanks"),
        dict(task="Food Kits",         start=6,  end=48, color="#30d158", qty="19,155 kits"),
        dict(task="Medical Units",     start=6,  end=72, color="#ff6b81", qty="3,831 units"),
        dict(task="SAR Teams",         start=0,  end=48, color="#ffa502", qty="24 teams"),
        dict(task="Emergency Shelter", start=24, end=96, color="#a29bfe", qty="8,500 kits"),
        dict(task="Sanitation",        start=48, end=96, color="#00cec9", qty="1,200 units"),
    ]
    fig = go.Figure([go.Bar(
        orientation="h", y=[t["task"]], x=[t["end"]-t["start"]], base=[t["start"]],
        marker=dict(color=t["color"], opacity=0.84), name=t["task"],
        showlegend=False, text=[t["qty"]], textposition="inside",
        textfont=dict(size=9, color="white"),
        hovertemplate=f"<b>{t['task']}</b><br>{t['start']}h \u2192 {t['end']}h<br>{t['qty']}<extra></extra>")
        for t in tasks])
    fig.update_layout(**_base(
        margin=dict(l=115,r=20,t=10,b=50),
        xaxis=dict(title="Hours from Warning", range=[0,100],
                   tickvals=[0,6,12,24,48,72,96],
                   ticktext=["0h","6h","12h","24h","48h","72h","96h"],
                   gridcolor="rgba(255,255,255,.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,.04)", tickfont=dict(size=10))))
    return fig


def build_risk_trend():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=LEAD_LABELS, y=[d["re"] for d in HORIZONS],
        mode="lines+markers", name="Expected Risk",
        line=dict(color="#00aaff", width=2), marker=dict(size=7, color="#00aaff"),
        hovertemplate="Lead %{x}<br>Risk: %{y:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=LEAD_LABELS, y=[d["rp"] for d in HORIZONS],
        mode="lines+markers", name="P90 Risk",
        line=dict(color="#ff4757", width=2, dash="dash"), marker=dict(size=7, color="#ff4757"),
        hovertemplate="Lead %{x}<br>P90 Risk: %{y:.2f}<extra></extra>"))
    fig.update_layout(**_base(
        xaxis=dict(gridcolor="rgba(255,255,255,.04)"),
        yaxis=dict(title="Risk Score", range=[62,82],
                   gridcolor="rgba(255,255,255,.04)", zeroline=False),
        legend=dict(orientation="h", x=0, y=1.08, bgcolor=BG, font=dict(size=10)),
        showlegend=True, margin=dict(l=55,r=20,t=30,b=40),
        shapes=[dict(type="line", x0=-0.5, x1=5.5, y0=73, y1=73,
                     line=dict(color="#ffa502", width=1, dash="dash"))],
        annotations=[dict(x=4.5, y=73.4, text="ACTION THRESHOLD",
                          showarrow=False, font=dict(size=8, color="#ffa502"))]))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  STYLE CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

_PANEL  = {"background":"#0c1526","border":"1px solid rgba(0,170,255,0.12)",
           "borderRadius":"11px","overflow":"hidden","marginBottom":"14px"}
_PH     = {"padding":"11px 16px","borderBottom":"1px solid rgba(0,170,255,0.12)",
           "display":"flex","alignItems":"center","justifyContent":"space-between","gap":"10px"}
_PT     = {"fontFamily":"Rajdhani,sans-serif","fontSize":"13px","fontWeight":"600",
           "letterSpacing":"1.4px","textTransform":"uppercase","color":"#00e5ff"}
_BADGE  = {"background":"rgba(0,170,255,.1)","border":"1px solid rgba(0,170,255,.25)",
           "borderRadius":"20px","padding":"2px 9px","fontSize":"10px",
           "color":"#00aaff","letterSpacing":".8px","whiteSpace":"nowrap"}
_BTN    = {"background":"rgba(0,170,255,.08)","border":"1px solid rgba(0,170,255,.25)",
           "borderRadius":"7px","color":"#00aaff","padding":"5px 13px","fontSize":"11px",
           "fontFamily":"Rajdhani,sans-serif","fontWeight":"600","letterSpacing":"1.2px",
           "cursor":"pointer","whiteSpace":"nowrap"}
_ALERT  = {"borderRadius":"9px","padding":"10px 18px","marginBottom":"14px",
           "display":"flex","alignItems":"center","gap":"10px","fontSize":"12.5px","lineHeight":"1.5"}
_A_RED  = {**_ALERT,"background":"rgba(255,59,48,.08)","border":"1px solid rgba(255,59,48,.5)"}
_A_ONG  = {**_ALERT,"background":"rgba(255,149,0,.08)","border":"1px solid rgba(255,149,0,.5)"}
_A_BLU  = {**_ALERT,"background":"rgba(0,170,255,.08)","border":"1px solid rgba(0,170,255,.5)"}
_ROW    = {"display":"flex","gap":"14px","marginBottom":"14px"}

def _panel(title, *children, badge=None, controls=None, extra=None):
    hdr_right = []
    if controls: hdr_right.extend(controls)
    if badge:    hdr_right.append(html.Span(badge, style=_BADGE))
    items = [html.Div([html.Span(title, style=_PT),
                       html.Div(hdr_right, style={"display":"flex","gap":"8px","alignItems":"center"})],
                      style=_PH)]
    if extra: items.extend(extra)
    items.extend(children)
    return html.Div(items, style=_PANEL)


# ══════════════════════════════════════════════════════════════════════════════
#  SUPPLY CARDS
# ══════════════════════════════════════════════════════════════════════════════

def supply_cards(idx):
    h = HORIZONS[idx]
    specs = [
        (round(h["exp"]/200),  f"Food Kits ({h['h']}h Exp.)",  "1 kit / 200 people",     False),
        (round(h["exp"]/500),  f"Water Tanks ({h['h']}h)",      "1 tank / 500 people",    False),
        (round(h["exp"]/1000), f"Medical Units ({h['h']}h)",    "1 unit / 1,000 people",  False),
        (round(h["p90"]/200),  "Food Kits P90",                 "Worst-case pre-position", True),
        (round(h["p90"]/500),  "Water Tanks P90",               "Worst-case threshold",    True),
        (round(h["p90"]/1000), "Medical Units P90",             "P90 planning ceiling",    True),
    ]
    cards = []
    for val, lbl, unit, warn in specs:
        clr = "#ffcc00" if warn else "#30d158"
        brd = "rgba(255,204,0,0.3)" if warn else "rgba(0,170,255,0.12)"
        cards.append(html.Div([
            html.Div(f"{val:,}", style={"fontFamily":"Rajdhani,sans-serif","fontSize":"22px",
                                        "fontWeight":"700","color":clr,"lineHeight":"1"}),
            html.Div(lbl,  style={"fontSize":"9.5px","color":"#6a8cb8","letterSpacing":".8px",
                                   "marginTop":"4px","textTransform":"uppercase"}),
            html.Div(unit, style={"fontSize":"9px","color":"#2d4a70","marginTop":"2px"}),
        ], style={"flex":"1","minWidth":"110px","background":"#0c1526",
                  "border":f"1px solid {brd}","borderRadius":"9px","padding":"11px 13px","textAlign":"center"}))
    return html.Div(cards, style={"display":"flex","gap":"10px","flexWrap":"wrap","marginBottom":"14px"})


# ══════════════════════════════════════════════════════════════════════════════
#  RESCUE TABLE (static)
# ══════════════════════════════════════════════════════════════════════════════

def _prio(r):
    s = r["risk"] * r["pop"] / 1e6
    if s >= 250: return "CRITICAL","#ff6b6b","rgba(255,59,48,.2)","rgba(255,59,48,.4)"
    if s >= 100: return "HIGH",    "#ffb347","rgba(255,149,0,.2)","rgba(255,149,0,.4)"
    return         "MEDIUM",       "#ffdd55","rgba(255,204,0,.2)","rgba(255,204,0,.4)"

_TD = {"padding":"9px 13px","borderBottom":"1px solid rgba(255,255,255,.04)"}
_TH_S = {"background":"rgba(0,170,255,.05)","color":"#6a8cb8","padding":"9px 13px",
          "textAlign":"left","fontSize":"9.5px","fontWeight":"600",
          "letterSpacing":"1px","textTransform":"uppercase",
          "borderBottom":"1px solid rgba(0,170,255,0.12)"}

def rescue_table():
    head = html.Thead(html.Tr([html.Th(h, style=_TH_S)
                               for h in ["Region","Priority","Risk","P90","Pop","Cones","SAR"]]))
    rows = []
    for r in ALL_REGIONS[:12]:
        lbl, tc, bg, bd = _prio(r)
        rc = "#ff4757" if r["risk"]>=74 else "#ffa502" if r["risk"]>=70 else "#ffcc00"
        rows.append(html.Tr([
            html.Td(r["id"], style={**_TD,"fontFamily":"Rajdhani,sans-serif","fontWeight":"700","color":"#00e5ff"}),
            html.Td(html.Span(lbl, style={"display":"inline-block","padding":"2px 8px","borderRadius":"4px",
                                           "fontSize":"9.5px","fontWeight":"700","letterSpacing":".8px",
                                           "background":bg,"color":tc,"border":f"1px solid {bd}"}), style=_TD),
            html.Td(f"{r['risk']:.2f}", style={**_TD,"color":rc}),
            html.Td(f"{r['p90']:.2f}", style={**_TD,"color":"#6a8cb8"}),
            html.Td(fmt_pop(r["pop"]), style=_TD),
            html.Td(str(r["cones"]),   style=_TD),
            html.Td(f"{math.ceil(r['pop']/500000)} teams", style={**_TD,"color":"#30d158"}),
        ]))
    return html.Table([head, html.Tbody(rows)],
                      style={"width":"100%","borderCollapse":"collapse","fontSize":"11.5px"})


# ══════════════════════════════════════════════════════════════════════════════
#  STORM PROGRESS BARS (static)
# ══════════════════════════════════════════════════════════════════════════════

def storm_progress_bars():
    items = []
    for s in sorted(STORMS, key=lambda x: -x["maxRisk"]):
        items.append(html.Div([
            html.Div([
                html.Span(s["name"],            style={"fontSize":"11.5px","color":s["color"]}),
                html.Span(f"{s['maxRisk']:.1f}",style={"fontSize":"11.5px","fontWeight":"700","color":s["color"]}),
            ], style={"display":"flex","justifyContent":"space-between","marginBottom":"5px"}),
            html.Div(html.Div(style={
                "height":"100%","borderRadius":"3px",
                "width":f"{s['maxRisk']}%",
                "background":f"linear-gradient(90deg,{s['color']}44,{s['color']})"}),
                style={"height":"5px","background":"rgba(255,255,255,.06)",
                       "borderRadius":"3px","overflow":"hidden"}),
        ], style={"marginBottom":"12px"}))
    return html.Div(items, style={"padding":"10px 16px 14px"})


# ══════════════════════════════════════════════════════════════════════════════
#  APP
# ══════════════════════════════════════════════════════════════════════════════

app = Dash(__name__, title="UNICEF Humanitarian Risk Command",
           suppress_callback_exceptions=True)

# Custom index with dark background + grid + Google Fonts
app.index_string = """<!DOCTYPE html>
<html>
<head>
{%metas%}<title>{%title%}</title>{%favicon%}{%css%}
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#04080f;color:#ddeeff;font-family:Inter,sans-serif;overflow-x:hidden;}
body::before{content:"";position:fixed;top:0;left:0;width:100%;height:100%;
  background-image:linear-gradient(rgba(0,170,255,.025) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(0,170,255,.025) 1px,transparent 1px);
  background-size:40px 40px;pointer-events:none;z-index:0;}
::-webkit-scrollbar{width:5px;}
::-webkit-scrollbar-track{background:#04080f;}
::-webkit-scrollbar-thumb{background:#1e3050;border-radius:3px;}
.Select-control,.Select-menu-outer,.Select-option{background:#101e30!important;color:#ddeeff!important;border-color:rgba(0,170,255,0.25)!important;}
.Select-option.is-focused{background:#1e3050!important;}
.rc-slider-track{background:linear-gradient(90deg,#00aaff,#00e5ff)!important;}
.rc-slider-handle{border-color:#00e5ff!important;background:#00e5ff!important;}
</style>
</head>
<body>
{%app_entry%}
<footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>"""

app.layout = html.Div([
    # ── Intervals ────────────────────────────────────────────────────────────
    dcc.Interval(id="clk",  interval=1000, n_intervals=0),
    dcc.Interval(id="anim", interval=200,  n_intervals=0, disabled=False),
    dcc.Interval(id="rot",  interval=80,   n_intervals=0, disabled=False),

    # ── State stores ─────────────────────────────────────────────────────────
    dcc.Store(id="s-step",    data=0),
    dcc.Store(id="s-play",    data=True),
    dcc.Store(id="s-angle",   data=0.0),
    dcc.Store(id="s-rot-off", data=False),

    # ══════════════════════════════════════════════════════════════════════════
    #  HEADER
    # ══════════════════════════════════════════════════════════════════════════
    html.Header([
        html.Div([
            html.Div("🌐", style={
                "width":"50px","height":"50px","flexShrink":"0",
                "background":"linear-gradient(135deg,#005fa3,#0099ee)",
                "borderRadius":"10px","display":"flex","alignItems":"center",
                "justifyContent":"center","fontSize":"24px",
                "boxShadow":"0 0 18px rgba(0,170,255,.4)"}),
            html.Div([
                html.Div("HUMANITARIAN RISK COMMAND",
                         style={"fontFamily":"Rajdhani,sans-serif","fontSize":"19px",
                                "fontWeight":"700","letterSpacing":"3px","color":"#00e5ff"}),
                html.Div("UNICEF · TROPICAL CYCLONE INTELLIGENCE · LIVE DASHBOARD",
                         style={"fontSize":"10px","color":"#6a8cb8","letterSpacing":"1.4px","marginTop":"2px"}),
            ]),
        ], style={"display":"flex","alignItems":"center","gap":"12px"}),

        html.Div(id="live-clock", children="⊙ UTC …",
                 style={"fontFamily":"Rajdhani,sans-serif","fontSize":"13px","color":"#00e5ff",
                        "letterSpacing":"2px","background":"rgba(0,229,255,.06)",
                        "border":"1px solid rgba(0,229,255,.18)","borderRadius":"7px",
                        "padding":"5px 12px","whiteSpace":"nowrap"}),

        html.Div([
            *[html.Div([
                html.Div(v, style={"fontFamily":"Rajdhani,sans-serif","fontSize":"26px",
                                   "fontWeight":"700","lineHeight":"1","color":c}),
                html.Div(l, style={"fontSize":"9px","color":"#6a8cb8","letterSpacing":"1px",
                                   "marginTop":"3px","textTransform":"uppercase"}),
              ], style={"background":"#0c1526","border":f"1px solid rgba(0,170,255,0.12)",
                        "borderRadius":"9px","padding":"8px 16px","minWidth":"106px","textAlign":"center"})
              for v, l, c in [
                  ("1,262",  "Active Cones",    "#ff3b30"),
                  ("67.86",  "Mean Risk",        "#ff9500"),
                  ("2.19M",  "Avg Pop Exposed",  "#00aaff"),
                  ("8",      "Storm Systems",    "#ff9500"),
                  ("46",     "Risk Regions",     "#30d158"),
              ]]
        ], style={"display":"flex","gap":"10px"}),
    ], style={
        "position":"sticky","top":"0","zIndex":"200",
        "background":"linear-gradient(180deg,#060c1a 0%,rgba(6,12,26,.95) 100%)",
        "borderBottom":"1px solid rgba(0,170,255,0.12)","backdropFilter":"blur(16px)",
        "display":"flex","alignItems":"center","justifyContent":"space-between",
        "padding":"10px 22px","gap":"16px","position":"relative","zIndex":"200"}),

    # ══════════════════════════════════════════════════════════════════════════
    #  TABS
    # ══════════════════════════════════════════════════════════════════════════
    dcc.Tabs(id="tabs", value="risk",
        style={"background":"#080e1c","borderBottom":"1px solid rgba(0,170,255,0.12)","position":"relative","zIndex":"190"},
        colors={"border":"transparent","primary":"#00e5ff","background":"#080e1c"},
        children=[
            dcc.Tab(label="⚠  RISK PREP",   value="risk",
                style={"fontFamily":"Rajdhani,sans-serif","fontSize":"13px","fontWeight":"600",
                       "letterSpacing":"2px","color":"#6a8cb8","background":"#080e1c",
                       "border":"none","padding":"12px 26px"},
                selected_style={"fontFamily":"Rajdhani,sans-serif","fontSize":"13px","fontWeight":"600",
                                "letterSpacing":"2px","color":"#00e5ff","background":"#080e1c",
                                "border":"none","borderBottom":"3px solid #00e5ff","padding":"12px 26px"}),
            dcc.Tab(label="🚑  RESCUE PREP", value="rescue",
                style={"fontFamily":"Rajdhani,sans-serif","fontSize":"13px","fontWeight":"600",
                       "letterSpacing":"2px","color":"#6a8cb8","background":"#080e1c",
                       "border":"none","padding":"12px 26px"},
                selected_style={"fontFamily":"Rajdhani,sans-serif","fontSize":"13px","fontWeight":"600",
                                "letterSpacing":"2px","color":"#00e5ff","background":"#080e1c",
                                "border":"none","borderBottom":"3px solid #00e5ff","padding":"12px 26px"}),
            dcc.Tab(label="📦  SUPPLY PREP", value="supply",
                style={"fontFamily":"Rajdhani,sans-serif","fontSize":"13px","fontWeight":"600",
                       "letterSpacing":"2px","color":"#6a8cb8","background":"#080e1c",
                       "border":"none","padding":"12px 26px"},
                selected_style={"fontFamily":"Rajdhani,sans-serif","fontSize":"13px","fontWeight":"600",
                                "letterSpacing":"2px","color":"#00e5ff","background":"#080e1c",
                                "border":"none","borderBottom":"3px solid #00e5ff","padding":"12px 26px"}),
        ]),

    html.Div(id="tab-body", style={"padding":"18px 22px","position":"relative","zIndex":"1"}),

], style={"background":"#04080f","minHeight":"100vh"})


# ══════════════════════════════════════════════════════════════════════════════
#  CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════

# ── Clock ─────────────────────────────────────────────────────────────────────
@app.callback(Output("live-clock","children"), Input("clk","n_intervals"))
def _clock(n):
    now = datetime.now(timezone.utc)
    return f"UTC {now.strftime('%Y-%m-%d %H:%M:%S')}"


# ── Tab render ────────────────────────────────────────────────────────────────
@app.callback(Output("tab-body","children"), Input("tabs","value"))
def _render_tab(tab):

    # ── RISK TAB ──────────────────────────────────────────────────────────────
    if tab == "risk":
        return html.Div([
            html.Div([
                html.Span("🚨", style={"fontSize":"18px","flexShrink":"0"}),
                html.Span([
                    html.B("CRITICAL: ", style={"color":"#ff3b30"}),
                    "8 active storm systems across 3 ocean basins. Regions ",
                    html.B("R_10_29",style={"color":"#ff3b30"})," (218 cones), ",
                    html.B("R_7_30", style={"color":"#ff3b30"})," (99 cones) exceed P90 risk 78.6. "
                    "DITWAH ensemble projects ",
                    html.B("6.49 M people",style={"color":"#ff3b30"})," within 96 h cone.",
                ]),
            ], style=_A_RED),

            html.Div([
                # Globe panel
                html.Div([
                    _panel("🌍 Storm Track Intelligence — Live Animation",
                        dcc.Graph(id="globe", figure=build_globe(1),
                                  config={"displayModeBar":False}, style={"height":"420px"}),
                        controls=[
                            html.Button("⏸ PAUSE", id="btn-play", n_clicks=0, style=_BTN),
                            html.Button("↺ REPLAY", id="btn-replay", n_clicks=0, style=_BTN),
                            html.Span("STEP 0", id="anim-badge", style=_BADGE),
                        ])
                ], style={"flex":"2.2","minWidth":"0"}),

                # Gauge + progress panel
                html.Div([
                    _panel("⚠ Portfolio Risk Index",
                           dcc.Graph(figure=build_gauge(), config={"displayModeBar":False},
                                     style={"height":"210px"})),
                    html.Div([
                        html.Div([
                            html.Span("🌙 Storm Risk Scores",style=_PT),
                            html.Span("/ 100",style={"fontSize":"9px","color":"#2d4a70"}),
                        ], style=_PH),
                        storm_progress_bars(),
                    ], style=_PANEL),
                ], style={"flex":"1","minWidth":"0"}),
            ], style=_ROW),

            html.Div([
                # Regional bar chart
                html.Div([
                    html.Div([
                        html.Span("🗺 Regional Risk Scores",style=_PT),
                        html.Span("46 REGIONS",style=_BADGE),
                    ], style=_PH),
                    html.Div([
                        html.Span("SORT BY:",style={"fontSize":"10px","color":"#6a8cb8","letterSpacing":".8px"}),
                        dcc.Dropdown(id="sort-by",
                            options=[{"label":"Risk Score","value":"risk"},
                                     {"label":"Population","value":"pop"},
                                     {"label":"Cone Count","value":"cones"},
                                     {"label":"P90 Risk","value":"p90"}],
                            value="risk", clearable=False,
                            style={"width":"140px","fontSize":"11px","color":"#ddeeff"}),
                        html.Span("FILTER RISK >:",style={"fontSize":"10px","color":"#6a8cb8","letterSpacing":".8px","marginLeft":"10px"}),
                        dcc.Dropdown(id="filt-risk",
                            options=[{"label":"All","value":0},{"label":"70","value":70},
                                     {"label":"72","value":72},{"label":"74","value":74}],
                            value=0, clearable=False,
                            style={"width":"85px","fontSize":"11px","color":"#ddeeff"}),
                    ], style={"display":"flex","alignItems":"center","gap":"8px",
                              "padding":"7px 14px","borderBottom":"1px solid rgba(0,170,255,0.12)"}),
                    dcc.Graph(id="reg-bars", figure=build_risk_regions(),
                              config={"displayModeBar":False}, style={"height":"285px"}),
                ], style={**_PANEL,"flex":"3","minWidth":"0"}),

                # Scatter
                html.Div([
                    html.Div(html.Span("📊 Population vs Risk",style=_PT),style=_PH),
                    dcc.Graph(figure=build_risk_scatter(),
                              config={"displayModeBar":False}, style={"height":"325px"}),
                ], style={**_PANEL,"flex":"1.8","minWidth":"0"}),
            ], style={"display":"flex","gap":"14px"}),
        ])

    # ── RESCUE TAB ────────────────────────────────────────────────────────────
    elif tab == "rescue":
        return html.Div([
            html.Div([
                html.Span("🚑",style={"fontSize":"18px","flexShrink":"0"}),
                html.Span([
                    html.B("RESCUE ALERT: ",style={"color":"#ff9500"}),
                    "P90 ensemble exposure at 96 h peaks at ",
                    html.B("9.27 M people",style={"color":"#ff9500"}),
                    ". Deploy pre-positioned SAR teams to ",
                    html.B("R_10_29",style={"color":"#ff9500"}),
                    " (4.67 M, 218 cones) and ",
                    html.B("R_7_30",style={"color":"#ff9500"}),
                    " (3.71 M). Coastal exposure ~72%.",
                ]),
            ], style=_A_ONG),

            _panel("🌍 3D Population-Exposure Globe — Auto-Rotating",
                dcc.Graph(id="globe3d", figure=build_rescue_3d(),
                          config={"displayModeBar":False}, style={"height":"510px"}),
                controls=[
                    html.Span("● LIVE ROTATION",style={
                        "fontSize":"9px","color":"#30d158",
                        "background":"rgba(48,209,88,.1)","border":"1px solid rgba(48,209,88,.25)",
                        "borderRadius":"12px","padding":"2px 8px","letterSpacing":".8px"}),
                    html.Button("⏸ PAUSE", id="btn-rot", n_clicks=0, style=_BTN),
                    html.Span("DRAG TO EXPLORE",style=_BADGE),
                ]),

            html.Div([
                html.Div([
                    html.Div([
                        html.Span("🎯 Rescue Priority Zones",style=_PT),
                        html.Span("TOP 12 REGIONS",style=_BADGE),
                    ], style=_PH),
                    rescue_table(),
                ], style={**_PANEL,"flex":"1.6","minWidth":"0","overflowX":"auto"}),

                html.Div([
                    html.Div(html.Span("📋 Max Population at Risk by Storm",style=_PT),style=_PH),
                    dcc.Graph(figure=build_rescue_pop(),
                              config={"displayModeBar":False}, style={"height":"300px"}),
                ], style={**_PANEL,"flex":"1","minWidth":"0"}),
            ], style={"display":"flex","gap":"14px"}),
        ])

    # ── SUPPLY TAB ────────────────────────────────────────────────────────────
    elif tab == "supply":
        return html.Div([
            html.Div([
                html.Span("📦",style={"fontSize":"18px","flexShrink":"0"}),
                html.Span([
                    html.B("SUPPLY ALERT: ",style={"color":"#00aaff"}),
                    "Drag the forecast slider to see live supply requirements. "
                    "Expected exposure: ",
                    html.B("987 K at 6 h → 3.83 M at 96 h",style={"color":"#00aaff"}),
                    ". P90 worst-case peaks at ",
                    html.B("9.33 M at 72 h",style={"color":"#00aaff"}),"."],
                ),
            ], style=_A_BLU),

            _panel("📈 Population Exposure by Forecast Horizon",
                dcc.Graph(id="exp-chart", figure=build_exposure(5),
                          config={"displayModeBar":False}, style={"height":"300px"}),
                badge="INTERACTIVE SLIDER",
                extra=[html.Div([
                    html.Span("FORECAST LEAD TIME:",
                              style={"fontFamily":"Rajdhani,sans-serif","fontSize":"12px",
                                     "fontWeight":"600","letterSpacing":"1.2px",
                                     "color":"#6a8cb8","whiteSpace":"nowrap"}),
                    dcc.Slider(id="lead-sl", min=0, max=5, step=1, value=5,
                        marks={i: {"label":f"{[6,12,24,48,72,96][i]}h",
                                   "style":{"color":"#6a8cb8","fontSize":"10px"}} for i in range(6)},
                        tooltip={"always_visible":False}),
                    html.Span("96h", id="lead-val",
                              style={"fontFamily":"Rajdhani,sans-serif","fontSize":"22px",
                                     "fontWeight":"700","color":"#00e5ff",
                                     "minWidth":"48px","textAlign":"center"}),
                ], style={"display":"flex","alignItems":"center","gap":"14px",
                          "padding":"12px 16px 8px"})]
            ),

            html.Div(id="supply-cards", children=supply_cards(5)),

            html.Div([
                html.Div([
                    html.Div(html.Span("🌊 Coastal vs Inland",style=_PT),style=_PH),
                    dcc.Graph(figure=build_coastal(),config={"displayModeBar":False},style={"height":"265px"}),
                ], style={**_PANEL,"flex":"1","minWidth":"0"}),
                html.Div([
                    html.Div(html.Span("⏳ Supply Deployment Gantt",style=_PT),style=_PH),
                    dcc.Graph(figure=build_gantt(),config={"displayModeBar":False},style={"height":"265px"}),
                ], style={**_PANEL,"flex":"1","minWidth":"0"}),
                html.Div([
                    html.Div(html.Span("📉 Risk Score Trend",style=_PT),style=_PH),
                    dcc.Graph(figure=build_risk_trend(),config={"displayModeBar":False},style={"height":"265px"}),
                ], style={**_PANEL,"flex":"1","minWidth":"0"}),
            ], style={"display":"flex","gap":"14px"}),
        ])


# ── Region sort/filter ────────────────────────────────────────────────────────
@app.callback(
    Output("reg-bars","figure"),
    Input("sort-by","value"), Input("filt-risk","value"),
    prevent_initial_call=True)
def _regions(sort_by, min_risk):
    return build_risk_regions(sort_by, min_risk or 0)


# ── Supply slider ─────────────────────────────────────────────────────────────
@app.callback(
    Output("exp-chart","figure"),
    Output("supply-cards","children"),
    Output("lead-val","children"),
    Input("lead-sl","value"),
    prevent_initial_call=True)
def _supply(idx):
    h = HORIZONS[int(idx)]
    return build_exposure(int(idx)), supply_cards(int(idx)), f"{h['h']}h"


# ── Storm animation ───────────────────────────────────────────────────────────
@app.callback(
    Output("s-step","data"),
    Output("anim-badge","children"),
    Output("globe","figure"),
    Input("anim","n_intervals"),
    State("s-step","data"),
    State("s-play","data"),
    State("tabs","value"),
    prevent_initial_call=True)
def _anim_tick(n, step, playing, tab):
    if not playing or tab != "risk":
        return no_update, no_update, no_update
    step = (step + 1) % (MAX_STEPS + 6)
    return step, f"STEP {step}", build_globe(step)


@app.callback(
    Output("s-play","data"),
    Output("anim","disabled"),
    Output("btn-play","children"),
    Input("btn-play","n_clicks"),
    State("s-play","data"),
    prevent_initial_call=True)
def _toggle_play(n, playing):
    new_p = not playing
    return new_p, not new_p, ("⏸ PAUSE" if new_p else "▶ PLAY")


@app.callback(
    Output("s-step","data", allow_duplicate=True),
    Output("s-play","data", allow_duplicate=True),
    Output("anim","disabled", allow_duplicate=True),
    Output("btn-play","children", allow_duplicate=True),
    Input("btn-replay","n_clicks"),
    prevent_initial_call=True)
def _replay(n):
    return 0, True, False, "⏸ PAUSE"


# ── 3D globe rotation ─────────────────────────────────────────────────────────
@app.callback(
    Output("globe3d","figure"),
    Output("s-angle","data"),
    Input("rot","n_intervals"),
    State("s-angle","data"),
    State("s-rot-off","data"),
    State("tabs","value"),
    prevent_initial_call=True)
def _rotate(n, angle, paused, tab):
    if paused or tab != "rescue":
        return no_update, no_update
    angle = (angle + 1.5) % 360
    patched = Patch()
    rad = math.radians(angle)
    patched["layout"]["scene"]["camera"]["eye"] = {
        "x": 1.4 * math.cos(rad), "y": 1.4 * math.sin(rad), "z": 0.45}
    return patched, angle


@app.callback(
    Output("s-rot-off","data"),
    Output("rot","disabled"),
    Output("btn-rot","children"),
    Input("btn-rot","n_clicks"),
    State("s-rot-off","data"),
    prevent_initial_call=True)
def _toggle_rot(n, paused):
    new_p = not paused
    return new_p, new_p, ("▶ RESUME" if new_p else "⏸ PAUSE")


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║  UNICEF Humanitarian Risk Command Dashboard  ║")
    print("  ╠══════════════════════════════════════════════╣")
    print("  ║  → http://127.0.0.1:8050                     ║")
    print("  ║  Press  Ctrl+C  to stop                      ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()
    app.run(debug=False, port=8050)
