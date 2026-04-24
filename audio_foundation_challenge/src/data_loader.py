from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class RiskData:
    summary: pd.DataFrame
    regions: pd.DataFrame
    horizons: pd.DataFrame


def load_risk_data(summary_csv: str | Path, region_csv: str | Path, horizon_csv: str | Path) -> RiskData:
    summary = pd.read_csv(summary_csv)
    regions = pd.read_csv(region_csv)
    horizons = pd.read_csv(horizon_csv)

    if summary.empty:
        raise ValueError("Summary CSV is empty.")
    if regions.empty:
        raise ValueError("Region CSV is empty.")
    if horizons.empty:
        raise ValueError("Horizon CSV is empty.")

    return RiskData(summary=summary, regions=regions, horizons=horizons)
