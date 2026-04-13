# UNICEF Humanitarian Risk Command Dashboard

A live, interactive single-page dashboard for tropical cyclone humanitarian risk intelligence.

🌐 **Live Demo:** https://ag230602.github.io/unicef_data/

## Features

- **Risk Prep** — Animated storm track drawing across 3 ocean basins, portfolio risk gauge, regional risk bar chart with sort/filter, population-vs-risk scatter
- **Rescue Prep** — Auto-rotating 3D globe with storm tracks, SAR priority table, population-at-risk by storm
- **Supply Prep** — Interactive forecast horizon slider (6h → 96h) with live supply card updates, coastal/inland breakdown, deployment Gantt, risk trend chart

## Dynamic Capabilities

| Feature | Description |
|---|---|
| Live UTC clock | Updates every second |
| KPI count-up | All 5 header metrics animate on load |
| Animated tracks | 8 storms draw step-by-step with star markers |
| Pulsing storm heads | Storm heads pulse after animation completes |
| 3D globe rotation | Auto-rotates at 0.32°/frame, pauses on drag |
| Animated gauge | Needle sweeps 0 → 67.86 on load |
| CSS progress bars | 1.6s cubic-bezier fill animation |
| Interactive slider | Live supply requirements recalculate per horizon |

## Data

Built from UNICEF AOTS ensemble outputs covering:
- **8 storm systems**: DITWAH, FINA, FUNG-WONG, KALMAEGI, KOTO, MELISSA, GEZANI, DUDZAI
- **20 high-risk regions** with population exposure and P90 risk scores
- **6 forecast horizons**: 6h → 96h

## Tech Stack

- Pure HTML/CSS/JS (no framework)
- [Plotly.js 2.27.0](https://plotly.com/javascript/) for all visualizations
- Google Fonts (Rajdhani, Inter)
- Self-contained single file — no build step required
