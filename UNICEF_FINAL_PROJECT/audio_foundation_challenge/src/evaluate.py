from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import soundfile as sf
import torch
from jiwer import wer
from transformers import pipeline


def _normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


class AudioEvaluator:
    def __init__(self, asr_model_id: str = "openai/whisper-small") -> None:
        self.asr = pipeline(
            task="automatic-speech-recognition",
            model=asr_model_id,
            device=0 if torch.cuda.is_available() else -1,
        )

    def transcribe(self, audio_path: str | Path) -> str:
        audio, sr = sf.read((Path(audio_path)).as_posix())
        result = self.asr({"raw": audio, "sampling_rate": sr}, return_timestamps=True)
        if isinstance(result, dict):
            return str(result.get("text", "")).strip()
        return str(result).strip()


def fact_coverage_score(script: str, required_facts: list[str]) -> float:
    normalized = _normalize_text(script)
    found = sum(1 for item in required_facts if item in normalized)
    return found / max(len(required_facts), 1)


def evaluate_pair(
    setting_name: str,
    intended_script: str,
    transcribed_script: str,
    tts_latency_seconds: float,
    required_facts: list[str],
) -> dict:
    return {
        "setting": setting_name,
        "script_chars": len(intended_script),
        "tts_latency_seconds": round(tts_latency_seconds, 4),
        "asr_wer": round(wer(_normalize_text(intended_script), _normalize_text(transcribed_script)), 4),
        "fact_coverage_score": round(fact_coverage_score(intended_script, required_facts), 4),
    }


def save_evaluation_artifacts(rows: list[dict], output_dir: str | Path) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(rows)
    csv_path = output_dir / "evaluation_results.csv"
    md_path = output_dir / "evaluation_report.md"

    df.to_csv(csv_path, index=False)

    lines = [
        "# Evaluation Report",
        "",
        "## Metrics",
        "- `asr_wer`: lower is better",
        "- `tts_latency_seconds`: lower is better",
        "- `fact_coverage_score`: higher is better",
        "",
        "## Results",
        "",
        "```",
        df.to_string(index=False),
        "```",
        "",
        "## Quick Interpretation",
    ]

    if len(df) >= 2:
        base = df.iloc[0]
        imp = df.iloc[1]
        lines.extend(
            [
                f"- WER change (improved - baseline): {imp['asr_wer'] - base['asr_wer']:+.4f}",
                f"- Latency change (improved - baseline): {imp['tts_latency_seconds'] - base['tts_latency_seconds']:+.4f} s",
                f"- Coverage change (improved - baseline): {imp['fact_coverage_score'] - base['fact_coverage_score']:+.4f}",
            ]
        )

    md_path.write_text("\n".join(lines), encoding="utf-8")
