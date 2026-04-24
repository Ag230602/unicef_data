#!/usr/bin/env python3
"""
UNICEF Humanitarian Risk Command Dashboard — Streamlit
══════════════════════════════════════════════════════════════════════
Run locally:
    pip install streamlit plotly
    streamlit run streamlit_app.py

Deploy to Streamlit Cloud:
    1. Push this repo to GitHub (Ag230602/unicef_data)
    2. Go to https://share.streamlit.io
    3. Connect repo → branch: main → Main file: streamlit_app.py
    4. Click Deploy!
"""

import math
import csv
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from datetime import datetime, timezone

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UNICEF – Humanitarian Risk Command",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Google Fonts + Dark Theme CSS ─────────────────────────────────────────────
# Inject CSS via parent-frame JS — works in ALL Streamlit versions including 1.36+
# (newer Streamlit strips <style> tags from st.markdown for security, so we
#  inject a real <style> element directly into the parent document's <head>)
_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;600;700&display=swap');

[data-testid="stAppViewContainer"] { background: #04080f !important; }
[data-testid="stHeader"]           { background: rgba(4,8,15,0.95) !important; border-bottom: 1px solid rgba(0,170,255,0.1); }
section[data-testid="stMain"]      { background: #04080f !important; }
[data-testid="stToolbar"]          { display: none; }
div.block-container { padding: 1rem 1.5rem 2rem !important; max-width: 1800px; }
body { background: #04080f; color: #ddeeff; font-family: 'Inter', sans-serif; }
h1,h2,h3 { color: #ddeeff; font-family: 'Rajdhani', sans-serif; }
p { color: #8ab0d0; }

button[data-baseweb="tab"] {
    background: transparent; color: #6a8cb8;
    font-family: 'Rajdhani', sans-serif; font-size: 13px; font-weight: 600;
    letter-spacing: 1.1px; text-transform: uppercase;
    border: none; padding: 10px 20px;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: rgba(0,170,255,0.1) !important;
    color: #00e5ff !important;
    border-bottom: 2px solid #00e5ff !important;
}
button[data-baseweb="tab"]:hover { color: #00aaff !important; }

[data-testid="metric-container"] {
    background: #0c1526; border: 1px solid rgba(0,170,255,0.14);
    border-radius: 11px; padding: 14px 16px;
}
[data-testid="stMetricLabel"] > div {
    color: #6a8cb8 !important; font-family: 'Rajdhani', sans-serif !important;
    font-size: 10px !important; letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] > div {
    color: #ddeeff !important; font-family: 'Rajdhani', sans-serif !important;
    font-size: 22px !important; font-weight: 700 !important;
}

[data-testid="stSlider"] label      { color: #6a8cb8 !important; font-size: 11px; }
[data-testid="stSelectbox"] label   { color: #6a8cb8 !important; font-size: 11px; }
div[data-baseweb="select"] > div    { background: #0c1526 !important; border-color: rgba(0,170,255,0.2) !important; color: #ddeeff !important; }
[data-testid="stPlotlyChart"] > div { background: transparent !important; }

::-webkit-scrollbar       { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #04080f; }
::-webkit-scrollbar-thumb { background: #1e3050; border-radius: 3px; }

.alert-red  { background:rgba(255,59,48,.08);  border:1px solid rgba(255,59,48,.5);  border-radius:9px; padding:10px 16px; margin-bottom:10px; font-size:12.5px; color:#ffaaaa; }
.alert-ong  { background:rgba(255,149,0,.08);  border:1px solid rgba(255,149,0,.5);  border-radius:9px; padding:10px 16px; margin-bottom:10px; font-size:12.5px; color:#ffcc88; }
.alert-blu  { background:rgba(0,170,255,.08);  border:1px solid rgba(0,170,255,.5);  border-radius:9px; padding:10px 16px; margin-bottom:10px; font-size:12.5px; color:#88ccff; }
.panel-hdr  { font-family:'Rajdhani',sans-serif; font-size:12.5px; font-weight:600; letter-spacing:1.3px; text-transform:uppercase; color:#00e5ff; margin-bottom:8px; padding:4px 0 6px; border-bottom:1px solid rgba(0,170,255,0.12); }
"""

# Use components.html to inject CSS via JS into the parent document <head>
# This is the only method that reliably works in Streamlit 1.36+
components.html(
    f"""<script>
    (function() {{
        var id = 'unicef-dark-theme';
        if (window.parent.document.getElementById(id)) return;
        var s = window.parent.document.createElement('style');
        s.id = id;
        s.textContent = `{_CSS}`;
        window.parent.document.head.appendChild(s);
    }})();
    </script>""",
    height=0,
)


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

LEAD_LABELS = ["6h", "12h", "24h", "48h", "72h", "96h"]
MAX_STEPS   = max(len(s["lats"]) for s in STORMS)

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
        a   = 2 * math.pi * i / n
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
    """Animated storm-track geo globe with slider control."""
    traces = []
    for s in STORMS:
        n    = len(s["lats"]) if step is None else min(int(step) + 1, len(s["lats"]))
        lats = s["lats"][:n]
        lons = s["lons"][:n]
        sz   = [5] * n
        sym  = ["circle"] * n
        if n:
            sz[-1]  = 15
            sym[-1] = "star"

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
        **_base(margin=dict(l=0, r=0, t=0, b=0), showlegend=True,
                legend=dict(orientation="h", x=0, y=-0.04, bgcolor=BG,
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
            axis=dict(range=[0, 100], tickwidth=1, tickcolor="#2d4a70",
                      tickfont=dict(size=8, color="#6a8cb8")),
            bar=dict(color="#ff5e3a", thickness=0.25),
            bgcolor=BG, borderwidth=0,
            steps=[dict(range=[0,  40], color="rgba(48,209,88,.12)"),
                   dict(range=[40, 60], color="rgba(255,204,0,.10)"),
                   dict(range=[60, 80], color="rgba(255,149,0,.12)"),
                   dict(range=[80,100], color="rgba(255,59,48,.18)")],
            threshold=dict(line=dict(color="#ffcc00", width=3), thickness=0.7, value=76.14)),
        number=dict(font=dict(size=38, color="#ff5e3a", family="Rajdhani, sans-serif"))))
    fig.update_layout(**_base(margin=dict(l=25, r=25, t=30, b=10), height=200))
    return fig


def build_risk_regions(sort_by="risk", min_risk=0):
    regions = sorted(
        [r for r in ALL_REGIONS if r["risk"] >= min_risk],
        key=lambda r: -r.get(sort_by, r["risk"]))
    colors = ["#ff4757" if r["risk"] >= 74 else "#ffa502" if r["risk"] >= 70 else "#ffcc00"
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
        xaxis=dict(range=[60, 82], title="Risk Score", gridcolor="rgba(255,255,255,.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,.04)", tickfont=dict(size=9)),
        legend=dict(orientation="h", x=0, y=1.08, bgcolor=BG, font=dict(size=9)),
        showlegend=True, margin=dict(l=75, r=20, t=10, b=40)))
    return fig


def build_risk_scatter():
    fig = go.Figure()
    for s in STORMS:
        fig.add_trace(go.Scatter(
            x=[s["maxPop"] / 1e6], y=[s["maxRisk"]],
            mode="markers+text",
            marker=dict(size=max(8, s["maxPop"] / 600000), color=s["color"], opacity=0.85,
                        line=dict(color="white", width=1)),
            text=[s["name"]], textposition="top center",
            textfont=dict(size=9, color=s["color"]),
            name=s["name"],
            hovertemplate=f"<b>{s['name']}</b><br>Pop: %{{x:.2f}}M<br>Risk: %{{y:.1f}}<extra></extra>"))
    fig.update_layout(**_base(
        showlegend=False,
        xaxis=dict(title="Max Population at Risk (M)", gridcolor="rgba(255,255,255,.05)", zeroline=False),
        yaxis=dict(title="Max Risk Score", gridcolor="rgba(255,255,255,.05)", zeroline=False),
        margin=dict(l=55, r=20, t=10, b=45)))
    return fig


def build_rescue_3d(rot_angle=0.0):
    """3D sphere globe with region + storm markers."""
    traces = []
    u_pts = [i * math.pi / 18 for i in range(19)]
    v_pts = [i * 2 * math.pi / 36 for i in range(37)]
    for u in u_pts:
        xs = [math.sin(u) * math.cos(v) for v in v_pts]
        ys = [math.sin(u) * math.sin(v) for v in v_pts]
        zs = [math.cos(u)] * len(v_pts)
        traces.append(go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", showlegend=False,
                                   hoverinfo="skip",
                                   line=dict(color="rgba(0,170,255,0.07)", width=1)))
    for v in v_pts[::3]:
        xs = [math.sin(u) * math.cos(v) for u in u_pts]
        ys = [math.sin(u) * math.sin(v) for u in u_pts]
        zs = [math.cos(u) for u in u_pts]
        traces.append(go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", showlegend=False,
                                   hoverinfo="skip",
                                   line=dict(color="rgba(0,170,255,0.07)", width=1)))
    for i, r in enumerate(ALL_REGIONS):
        lat, lon = _REGION_COORDS[i % len(_REGION_COORDS)]
        x, y, z  = ll_to_xyz(lat, lon)
        color     = "#ff4757" if r["risk"] >= 74 else "#ffa502" if r["risk"] >= 70 else "#ffcc00"
        traces.append(go.Scatter3d(
            x=[x], y=[y], z=[z], mode="markers", name=r["id"],
            marker=dict(size=max(4, r["pop"] / 900000), color=color, opacity=0.85,
                        line=dict(color="white", width=0.5)),
            hovertemplate=(f"<b>{r['id']}</b><br>Risk: {r['risk']:.2f}<br>"
                           f"Pop: {fmt_pop(r['pop'])}<br>P90: {r['p90']:.2f}<extra></extra>")))
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
        margin=dict(l=0, r=0, t=0, b=0), height=500, showlegend=False,
        scene=dict(
            bgcolor="#020810",
            xaxis=dict(visible=False, showgrid=False),
            yaxis=dict(visible=False, showgrid=False),
            zaxis=dict(visible=False, showgrid=False),
            camera=dict(eye=dict(x=1.4 * math.cos(rad), y=1.4 * math.sin(rad), z=0.45),
                        up=dict(x=0, y=0, z=1)),
            aspectmode="cube")))


def build_rescue_pop():
    ss = sorted(STORMS, key=lambda s: -s["maxPop"])
    fig = go.Figure(go.Bar(
        orientation="h",
        y=[s["name"]        for s in ss],
        x=[s["maxPop"] / 1e6 for s in ss],
        marker=dict(color=[s["color"] for s in ss], opacity=0.85),
        hovertemplate="<b>%{y}</b><br>Pop: %{x:.2f}M<extra></extra>"))
    fig.update_layout(**_base(
        xaxis=dict(title="Population (M)", gridcolor="rgba(255,255,255,.04)", zeroline=False),
        yaxis=dict(gridcolor="rgba(255,255,255,.04)", tickfont=dict(size=11, color="#ddeeff")),
        showlegend=False, margin=dict(l=110, r=20, t=10, b=40)))
    return fig


def build_exposure(idx=5):
    h = HORIZONS[idx]
    no_fill = "rgba(0,0,0,0)"  # transparent — use rgba not 'transparent'
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=LEAD_LABELS, y=[d["p90"] / 1e6 for d in HORIZONS],
        fill="tozeroy", fillcolor="rgba(255,204,0,.07)",
        line=dict(color=no_fill), showlegend=False, hoverinfo="skip", name=""))
    fig.add_trace(go.Scatter(
        x=LEAD_LABELS, y=[d["exp"] / 1e6 for d in HORIZONS],
        fill="tozeroy", fillcolor="rgba(0,170,255,.12)",
        line=dict(color=no_fill), showlegend=False, hoverinfo="skip", name=""))
    fig.add_trace(go.Scatter(
        x=LEAD_LABELS, y=[d["exp"] / 1e6 for d in HORIZONS],
        mode="lines+markers", name="Expected",
        line=dict(color="#00aaff", width=3),
        marker=dict(size=9, color="#00aaff", line=dict(color="white", width=1.5)),
        hovertemplate="Lead %{x}<br><b>Exp: %{y:.2f}M</b><extra></extra>"))
    fig.add_trace(go.Scatter(
        x=LEAD_LABELS, y=[d["p90"] / 1e6 for d in HORIZONS],
        mode="lines+markers", name="P90 Worst-Case",
        line=dict(color="#ffcc00", width=2, dash="dash"),
        marker=dict(size=7, color="#ffcc00"),
        hovertemplate="Lead %{x}<br><b>P90: %{y:.2f}M</b><extra></extra>"))
    fig.update_layout(**_base(
        margin=dict(l=60, r=20, t=30, b=40),
        xaxis=dict(title="Forecast Lead Time", gridcolor="rgba(255,255,255,.05)"),
        yaxis=dict(title="Population Exposed (M)", gridcolor="rgba(255,255,255,.05)", zeroline=False),
        legend=dict(orientation="h", x=0, y=1.08, bgcolor=BG, font=dict(size=11)),
        showlegend=True,
        shapes=[dict(type="line", x0=idx, x1=idx, y0=0, y1=12,
                     line=dict(color="#00e5ff", width=2, dash="dash"))],
        annotations=[
            dict(x=LEAD_LABELS[idx], y=h["p90"] / 1e6 + 0.4,
                 text=f"\u25b2 {fmt_pop(h['p90'])} P90",
                 showarrow=False, font=dict(size=10, color="#ffcc00")),
            dict(x=LEAD_LABELS[idx], y=h["exp"] / 1e6 + 0.4,
                 text=f"\u25cf {fmt_pop(h['exp'])} Exp.",
                 showarrow=False, font=dict(size=10, color="#00aaff"))]))
    return fig


def build_coastal():
    cf = 0.72
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=LEAD_LABELS, y=[d["exp"] * cf / 1e6 for d in HORIZONS],
        name="Coastal (72%)", marker=dict(color="#1e90ff", opacity=0.85),
        hovertemplate="Lead %{x}<br>Coastal: %{y:.2f}M<extra></extra>"))
    fig.add_trace(go.Bar(
        x=LEAD_LABELS, y=[d["exp"] * (1 - cf) / 1e6 for d in HORIZONS],
        name="Inland (28%)", marker=dict(color="#30d158", opacity=0.85),
        hovertemplate="Lead %{x}<br>Inland: %{y:.2f}M<extra></extra>"))
    fig.update_layout(**_base(
        barmode="stack",
        xaxis=dict(gridcolor="rgba(255,255,255,.04)"),
        yaxis=dict(title="Pop (M)", gridcolor="rgba(255,255,255,.04)", zeroline=False),
        legend=dict(orientation="h", x=0, y=1.08, bgcolor=BG, font=dict(size=10)),
        showlegend=True, margin=dict(l=55, r=20, t=30, b=40)))
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
        orientation="h",
        y=[t["task"]], x=[t["end"] - t["start"]], base=[t["start"]],
        marker=dict(color=t["color"], opacity=0.84),
        name=t["task"], showlegend=False,
        text=[t["qty"]], textposition="inside",
        textfont=dict(size=9, color="white"),
        hovertemplate=f"<b>{t['task']}</b><br>{t['start']}h \u2192 {t['end']}h<br>{t['qty']}<extra></extra>")
        for t in tasks])
    fig.update_layout(**_base(
        margin=dict(l=115, r=20, t=10, b=50),
        xaxis=dict(title="Hours from Warning", range=[0, 100],
                   tickvals=[0, 6, 12, 24, 48, 72, 96],
                   ticktext=["0h", "6h", "12h", "24h", "48h", "72h", "96h"],
                   gridcolor="rgba(255,255,255,.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,.04)", tickfont=dict(size=10))))
    return fig


def build_risk_trend():
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=LEAD_LABELS, y=[d["re"] for d in HORIZONS],
        mode="lines+markers", name="Expected Risk",
        line=dict(color="#00aaff", width=2), marker=dict(size=7, color="#00aaff"),
        hovertemplate="Lead %{x}<br>Risk: %{y:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=LEAD_LABELS, y=[d["rp"] for d in HORIZONS],
        mode="lines+markers", name="P90 Risk",
        line=dict(color="#ff4757", width=2, dash="dash"), marker=dict(size=7, color="#ff4757"),
        hovertemplate="Lead %{x}<br>P90 Risk: %{y:.2f}<extra></extra>"))
    fig.update_layout(**_base(
        xaxis=dict(gridcolor="rgba(255,255,255,.04)"),
        yaxis=dict(title="Risk Score", range=[62, 82],
                   gridcolor="rgba(255,255,255,.04)", zeroline=False),
        legend=dict(orientation="h", x=0, y=1.08, bgcolor=BG, font=dict(size=10)),
        showlegend=True, margin=dict(l=55, r=20, t=30, b=40),
        shapes=[dict(type="line", x0=-0.5, x1=5.5, y0=73, y1=73,
                     line=dict(color="#ffa502", width=1, dash="dash"))],
        annotations=[dict(x=4.5, y=73.4, text="ACTION THRESHOLD",
                          showarrow=False, font=dict(size=8, color="#ffa502"))]))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER RENDERERS
# ══════════════════════════════════════════════════════════════════════════════

def _prio(r):
    s = r["risk"] * r["pop"] / 1e6
    if s >= 250: return "CRITICAL", "#ff6b6b"
    if s >= 100: return "HIGH",     "#ffb347"
    return              "MEDIUM",   "#ffdd55"


def render_rescue_table():
    rows_html = ""
    for r in ALL_REGIONS[:12]:
        lbl, tc = _prio(r)
        rc = "#ff4757" if r["risk"] >= 74 else "#ffa502" if r["risk"] >= 70 else "#ffcc00"
        sar = math.ceil(r["pop"] / 500000)
        rows_html += f"""
        <tr style="border-bottom:1px solid rgba(255,255,255,.04)">
          <td style="padding:8px 12px;font-family:Rajdhani,sans-serif;font-weight:700;color:#00e5ff">{r['id']}</td>
          <td style="padding:8px 12px"><span style="background:rgba(0,0,0,.3);border:1px solid {tc};color:{tc};border-radius:4px;padding:2px 7px;font-size:9.5px;font-weight:700">{lbl}</span></td>
          <td style="padding:8px 12px;color:{rc}">{r['risk']:.2f}</td>
          <td style="padding:8px 12px;color:#6a8cb8">{r['p90']:.2f}</td>
          <td style="padding:8px 12px">{fmt_pop(r['pop'])}</td>
          <td style="padding:8px 12px">{r['cones']}</td>
          <td style="padding:8px 12px;color:#30d158">{sar} teams</td>
        </tr>"""
    return f"""
    <div style="background:#0c1526;border:1px solid rgba(0,170,255,0.12);border-radius:11px;overflow:hidden">
      <table style="width:100%;border-collapse:collapse;font-size:11.5px;color:#ddeeff">
        <thead>
          <tr style="background:rgba(0,170,255,.05);border-bottom:1px solid rgba(0,170,255,0.12)">
            <th style="padding:9px 12px;text-align:left;color:#6a8cb8;font-size:9.5px;letter-spacing:1px;text-transform:uppercase">Region</th>
            <th style="padding:9px 12px;text-align:left;color:#6a8cb8;font-size:9.5px;letter-spacing:1px;text-transform:uppercase">Priority</th>
            <th style="padding:9px 12px;text-align:left;color:#6a8cb8;font-size:9.5px;letter-spacing:1px;text-transform:uppercase">Risk</th>
            <th style="padding:9px 12px;text-align:left;color:#6a8cb8;font-size:9.5px;letter-spacing:1px;text-transform:uppercase">P90</th>
            <th style="padding:9px 12px;text-align:left;color:#6a8cb8;font-size:9.5px;letter-spacing:1px;text-transform:uppercase">Pop</th>
            <th style="padding:9px 12px;text-align:left;color:#6a8cb8;font-size:9.5px;letter-spacing:1px;text-transform:uppercase">Cones</th>
            <th style="padding:9px 12px;text-align:left;color:#6a8cb8;font-size:9.5px;letter-spacing:1px;text-transform:uppercase">SAR</th>
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>"""


def render_storm_progress():
    html = '<div style="background:#0c1526;border:1px solid rgba(0,170,255,0.12);border-radius:11px;padding:14px 16px">'
    for s in sorted(STORMS, key=lambda x: -x["maxRisk"]):
        html += f"""
        <div style="margin-bottom:12px">
          <div style="display:flex;justify-content:space-between;margin-bottom:4px">
            <span style="font-size:11.5px;color:{s['color']}">{s['name']}</span>
            <span style="font-size:11.5px;font-weight:700;color:{s['color']}">{s['maxRisk']:.1f}</span>
          </div>
          <div style="height:5px;background:rgba(255,255,255,.06);border-radius:3px;overflow:hidden">
            <div style="height:100%;border-radius:3px;width:{s['maxRisk']}%;background:linear-gradient(90deg,{s['color']}44,{s['color']})"></div>
          </div>
        </div>"""
    html += "</div>"
    return html


def render_supply_cards(idx):
    h = HORIZONS[idx]
    specs = [
        (round(h["exp"] / 200),  f"Food Kits ({h['h']}h Exp.)",  "1 kit / 200 people",     False),
        (round(h["exp"] / 500),  f"Water Tanks ({h['h']}h)",     "1 tank / 500 people",    False),
        (round(h["exp"] / 1000), f"Medical Units ({h['h']}h)",   "1 unit / 1,000 people",  False),
        (round(h["p90"] / 200),  "Food Kits P90",                "Worst-case pre-position", True),
        (round(h["p90"] / 500),  "Water Tanks P90",              "Worst-case threshold",    True),
        (round(h["p90"] / 1000), "Medical Units P90",            "P90 planning ceiling",    True),
    ]
    cards = ""
    for val, lbl, unit, warn in specs:
        clr = "#ffcc00" if warn else "#30d158"
        brd = "rgba(255,204,0,0.3)" if warn else "rgba(0,170,255,0.12)"
        cards += f"""
        <div style="flex:1;min-width:120px;background:#0c1526;border:1px solid {brd};border-radius:9px;padding:12px 14px;text-align:center">
          <div style="font-family:Rajdhani,sans-serif;font-size:22px;font-weight:700;color:{clr};line-height:1">{val:,}</div>
          <div style="font-size:9.5px;color:#6a8cb8;letter-spacing:.8px;margin-top:4px;text-transform:uppercase">{lbl}</div>
          <div style="font-size:9px;color:#2d4a70;margin-top:2px">{unit}</div>
        </div>"""
    return f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px">{cards}</div>'


def load_audio_artifacts():
    base = Path(__file__).resolve().parent / "audio_foundation_challenge" / "outputs"
    files = {
        "baseline_audio": base / "baseline_briefing.wav",
        "improved_audio": base / "improved_briefing.wav",
        "baseline_script": base / "baseline_script.txt",
        "improved_script": base / "improved_script.txt",
        "eval_csv": base / "evaluation_results.csv",
    }

    has_minimum = files["baseline_audio"].exists() and files["improved_audio"].exists()
    scripts = {
        "baseline": files["baseline_script"].read_text(encoding="utf-8") if files["baseline_script"].exists() else "",
        "improved": files["improved_script"].read_text(encoding="utf-8") if files["improved_script"].exists() else "",
    }

    eval_rows = []
    if files["eval_csv"].exists():
        with files["eval_csv"].open("r", encoding="utf-8", newline="") as f:
            eval_rows = list(csv.DictReader(f))

    return base, files, has_minimum, scripts, eval_rows


# ══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════════════

now = datetime.now(timezone.utc)
clock_str = now.strftime("UTC %Y-%m-%d  %H:%M:%S")

total_pop = sum(s["maxPop"] for s in STORMS)
avg_risk  = sum(s["maxRisk"] for s in STORMS) / len(STORMS)

st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:14px 20px;margin-bottom:18px;
            background:linear-gradient(135deg,rgba(0,40,80,0.9),rgba(4,8,15,0.98));
            border:1px solid rgba(0,170,255,0.2);border-radius:14px;
            box-shadow:0 4px 30px rgba(0,100,200,0.15);">
  <div style="display:flex;align-items:center;gap:16px">
    <div style="width:42px;height:42px;border-radius:50%;background:rgba(0,170,255,.15);
                border:2px solid rgba(0,170,255,.4);display:flex;align-items:center;
                justify-content:center;font-size:22px">🌐</div>
    <div>
      <div style="font-family:Rajdhani,sans-serif;font-size:22px;font-weight:700;
                  letter-spacing:2px;color:#00e5ff;text-transform:uppercase">
        UNICEF Humanitarian Risk Command
      </div>
      <div style="font-size:10px;color:#6a8cb8;letter-spacing:1.8px;text-transform:uppercase">
        Multi-Hazard Intelligence Platform &nbsp;·&nbsp; Real-Time Situational Awareness
      </div>
    </div>
  </div>
  <div style="text-align:right">
    <div style="font-family:Rajdhani,sans-serif;font-size:13px;color:#00aaff;letter-spacing:1px">{clock_str}</div>
    <div style="font-size:10px;color:#2d4a70;margin-top:2px;letter-spacing:.8px">AUTO-REFRESHES ON INTERACTION</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPI Row ────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("🌀  ACTIVE STORMS",     "8",                delta="↑2 from 24h ago",    delta_color="inverse")
k2.metric("👥  POPULATION AT RISK", fmt_pop(total_pop), delta="↑3.2% from 24h ago", delta_color="inverse")
k3.metric("⚠️  AVG RISK INDEX",     f"{avg_risk:.1f}",  delta="↑1.4 pts",           delta_color="inverse")
k4.metric("🌍  REGIONS MONITORED",  "20",               delta="All systems nominal", delta_color="off")
k5.metric("📡  FORECAST LEAD",      "6h–96h",           delta="6 horizons active",  delta_color="off")

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── Alert Banner ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="alert-red">🔴 <b>CRITICAL:</b> DITWAH (Bay of Bengal) — Cat 4 landfall imminent · 6.49M at risk · Evacuations ordered in 3 districts</div>
<div class="alert-ong">🟠 <b>HIGH:</b> FUNG-WONG (W. Pacific) — Rapid intensification · 5.2M at risk · Pre-positioning underway</div>
<div class="alert-blu">🔵 <b>WATCH:</b> KALMAEGI (S. China Sea) — Track shift possible · 4.8M in uncertainty cone · Monitoring elevated</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "  ⚠️  RISK PREP  ",
    "  🚑  RESCUE PREP  ",
    "  📦  SUPPLY PREP  ",
    "  🔊  AUDIO BRIEFING  ",
])


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 1 — RISK PREP
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    col_left, col_right = st.columns([3, 2], gap="medium")

    with col_left:
        st.markdown('<div class="panel-hdr">🌀  ACTIVE STORM TRACKS</div>', unsafe_allow_html=True)
        step = st.slider(
            "Animation step (0 = beginning, max = full tracks)",
            min_value=0, max_value=MAX_STEPS - 1, value=MAX_STEPS - 1,
            key="storm_step")
        st.plotly_chart(build_globe(step), use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="panel-hdr">📊  PORTFOLIO RISK GAUGE</div>', unsafe_allow_html=True)
        st.plotly_chart(build_gauge(), use_container_width=True, config={"displayModeBar": False})

    with col_right:
        st.markdown('<div class="panel-hdr">📈  REGIONAL RISK SCORES</div>', unsafe_allow_html=True)
        rc1, rc2 = st.columns(2)
        with rc1:
            sort_by = st.selectbox("Sort by", ["risk", "pop", "p90"], key="sort_by")
        with rc2:
            min_risk_opts = [0, 65, 70, 74]
            min_risk_lbl  = ["All", "≥ 65", "≥ 70", "≥ 74"]
            filt_idx = st.selectbox("Min risk", min_risk_lbl, key="filt_risk")
            min_risk = min_risk_opts[min_risk_lbl.index(filt_idx)]
        st.plotly_chart(build_risk_regions(sort_by, min_risk),
                        use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="panel-hdr">🔵  POPULATION vs RISK SCATTER</div>', unsafe_allow_html=True)
        st.plotly_chart(build_risk_scatter(),
                        use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 2 — RESCUE PREP
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    col_left, col_right = st.columns([3, 2], gap="medium")

    with col_left:
        st.markdown('<div class="panel-hdr">🌐  3D RESCUE GLOBE</div>', unsafe_allow_html=True)
        rot_angle = st.slider(
            "Globe rotation angle (°)",
            min_value=0, max_value=359, value=25, step=5,
            key="rot_angle")
        st.plotly_chart(build_rescue_3d(rot_angle),
                        use_container_width=True, config={"displayModeBar": False})

    with col_right:
        st.markdown('<div class="panel-hdr">📋  PRIORITY RESCUE REGIONS</div>', unsafe_allow_html=True)
        st.markdown(render_rescue_table(), unsafe_allow_html=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    bc1, bc2 = st.columns([1, 1], gap="medium")
    with bc1:
        st.markdown('<div class="panel-hdr">👥  POPULATION AT RISK BY STORM</div>', unsafe_allow_html=True)
        st.plotly_chart(build_rescue_pop(),
                        use_container_width=True, config={"displayModeBar": False})
    with bc2:
        st.markdown('<div class="panel-hdr">🌀  STORM RISK INTENSITY</div>', unsafe_allow_html=True)
        st.markdown(render_storm_progress(), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 3 — SUPPLY PREP
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="panel-hdr">⏱️  FORECAST LEAD TIME</div>', unsafe_allow_html=True)
    lead_idx = st.slider(
        "Select forecast horizon",
        min_value=0, max_value=5, value=2,
        format="%d",
        key="lead_idx")
    h = HORIZONS[lead_idx]
    st.markdown(
        f'<div style="font-family:Rajdhani,sans-serif;font-size:13px;color:#00e5ff;'
        f'letter-spacing:1px;margin-bottom:6px">Selected horizon: '
        f'<b>{LEAD_LABELS[lead_idx]}</b> &nbsp;·&nbsp; '
        f'Expected exposure: <b>{fmt_pop(h["exp"])}</b> &nbsp;·&nbsp; '
        f'P90: <b>{fmt_pop(h["p90"])}</b></div>',
        unsafe_allow_html=True)

    st.markdown('<div class="panel-hdr">📦  PRE-POSITION REQUIREMENTS</div>', unsafe_allow_html=True)
    st.markdown(render_supply_cards(lead_idx), unsafe_allow_html=True)

    sc1, sc2 = st.columns(2, gap="medium")
    with sc1:
        st.markdown('<div class="panel-hdr">📈  POPULATION EXPOSURE TIMELINE</div>', unsafe_allow_html=True)
        st.plotly_chart(build_exposure(lead_idx),
                        use_container_width=True, config={"displayModeBar": False})
    with sc2:
        st.markdown('<div class="panel-hdr">🏝️  COASTAL vs INLAND BREAKDOWN</div>', unsafe_allow_html=True)
        st.plotly_chart(build_coastal(),
                        use_container_width=True, config={"displayModeBar": False})

    sc3, sc4 = st.columns(2, gap="medium")
    with sc3:
        st.markdown('<div class="panel-hdr">📅  SUPPLY DEPLOYMENT TIMELINE</div>', unsafe_allow_html=True)
        st.plotly_chart(build_gantt(),
                        use_container_width=True, config={"displayModeBar": False})
    with sc4:
        st.markdown('<div class="panel-hdr">📉  RISK TREND BY LEAD TIME</div>', unsafe_allow_html=True)
        st.plotly_chart(build_risk_trend(),
                        use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 4 — AUDIO BRIEFING
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="panel-hdr">🗣️  FOUNDATION-MODEL BRIEFINGS</div>', unsafe_allow_html=True)
    base_dir, audio_files, has_audio, scripts, eval_rows = load_audio_artifacts()

    st.caption(f"Source folder: {base_dir}")

    if not has_audio:
        st.warning(
            "Audio files are not found yet. Run the pipeline in the separate folder: "
            "audio_foundation_challenge/run_pipeline.py"
        )
    else:
        a1, a2 = st.columns(2, gap="medium")

        with a1:
            st.markdown('<div class="panel-hdr">BASELINE BRIEFING</div>', unsafe_allow_html=True)
            if audio_files["baseline_audio"].exists():
                st.audio(audio_files["baseline_audio"].read_bytes(), format="audio/wav")
            st.text_area("Baseline Script", value=scripts["baseline"], height=130, key="baseline_script_view")

        with a2:
            st.markdown('<div class="panel-hdr">IMPROVED BRIEFING</div>', unsafe_allow_html=True)
            if audio_files["improved_audio"].exists():
                st.audio(audio_files["improved_audio"].read_bytes(), format="audio/wav")
            st.text_area("Improved Script", value=scripts["improved"], height=130, key="improved_script_view")

    if eval_rows:
        st.markdown('<div class="panel-hdr">📏  BASELINE vs IMPROVED EVALUATION</div>', unsafe_allow_html=True)
        st.dataframe(eval_rows, use_container_width=True, hide_index=True)

        by_name = {r.get("setting", ""): r for r in eval_rows}
        if "baseline" in by_name and "improved" in by_name:
            b = by_name["baseline"]
            i = by_name["improved"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Δ WER (improved - baseline)", f"{float(i['asr_wer']) - float(b['asr_wer']):+.4f}")
            c2.metric("Δ Latency (s)", f"{float(i['tts_latency_seconds']) - float(b['tts_latency_seconds']):+.4f}")
            c3.metric("Δ Fact Coverage", f"{float(i['fact_coverage_score']) - float(b['fact_coverage_score']):+.4f}")
    else:
        st.info("No evaluation CSV found yet. Generate it from the audio pipeline to display metrics here.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:30px;padding:14px 20px;border-top:1px solid rgba(0,170,255,0.1);
            display:flex;justify-content:space-between;align-items:center;
            font-size:10px;color:#2d4a70;letter-spacing:.8px">
  <span>UNICEF HUMANITARIAN RISK COMMAND &nbsp;·&nbsp; MULTI-HAZARD INTELLIGENCE PLATFORM</span>
  <span>DATA: GNO-DYN-GNN MODEL · AOTS TRACK ARCHIVE · POPULATION EXPOSURE ENGINE</span>
  <span>CLASSIFICATION: INTERNAL USE ONLY</span>
</div>
""", unsafe_allow_html=True)
