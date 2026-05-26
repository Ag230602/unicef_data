from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class PromptOutputs:
    baseline_script: str
    improved_script: str
    required_facts: list[str]


def _fmt_int(value: float) -> str:
    return f"{int(round(value, 0)):,}"


def _fmt_float(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}"


def build_scripts(summary: pd.DataFrame, regions: pd.DataFrame, horizons: pd.DataFrame) -> PromptOutputs:
    s = summary.iloc[0]

    top_regions = regions.sort_values("mean_risk_score", ascending=False).head(3)
    top_region_names = ", ".join(top_regions["region_id"].tolist())

    h72 = horizons[horizons["lead_time"] == 72]
    if h72.empty:
        h72 = horizons.sort_values("lead_time").iloc[[len(horizons) - 1]]
    h72_row = h72.iloc[0]

    baseline_script = (
        "Humanitarian risk update. "
        f"Average risk is {_fmt_float(s['mean_risk_score'], 1)} out of one hundred. "
        f"Expected population exposure is about {_fmt_int(s['mean_population_exposed'])} people. "
        f"The highest-risk areas include {top_region_names}. "
        "Use caution in response planning."
    )

    improved_script = (
        "Operational humanitarian bulletin for the next four days. "
        f"Across {_fmt_int(s['cones'])} forecast cones, the mean risk score is {_fmt_float(s['mean_risk_score'], 2)}, "
        f"and the ninetyth percentile risk score is {_fmt_float(s['p90_risk_score'], 2)}. "
        f"Average exposed population is {_fmt_int(s['mean_population_exposed'])}, "
        f"with a ninetyth percentile of {_fmt_int(s['p90_population_exposed'])}. "
        f"By seventy-two hours, expected exposure reaches {_fmt_int(h72_row['expected_exposure'])}, "
        f"and high-end exposure reaches {_fmt_int(h72_row['p90_exposure'])}. "
        f"Priority regions by mean risk are {top_region_names}. "
        f"Proxy external data usage is set to {s['used_proxy_external_data']}. "
        "Recommended action: pre-position supplies, validate local partner readiness, and schedule six-hour monitoring updates."
    )

    required_facts = [
        "mean risk score",
        "ninetyth percentile risk score",
        "average exposed population",
        "seventy-two hours",
        "priority regions",
        "proxy external data usage",
    ]

    return PromptOutputs(
        baseline_script=baseline_script,
        improved_script=improved_script,
        required_facts=required_facts,
    )
