from __future__ import annotations

import argparse
from pathlib import Path

from src.data_loader import load_risk_data
from src.evaluate import AudioEvaluator, evaluate_pair, save_evaluation_artifacts
from src.prompt_engineering import build_scripts
from src.tts_model import SpeechT5Synthesizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UNICEF audio foundation model challenge pipeline")
    parser.add_argument(
        "--summary-csv",
        type=str,
        default="../outputs/aots_humanitarian_risk_summary.csv",
        help="Path to humanitarian risk summary CSV",
    )
    parser.add_argument(
        "--region-csv",
        type=str,
        default="../outputs/aots_region_risk_scores.csv",
        help="Path to region risk score CSV",
    )
    parser.add_argument(
        "--horizon-csv",
        type=str,
        default="../outputs/aots_expected_exposure_by_horizon.csv",
        help="Path to horizon exposure CSV",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./outputs",
        help="Folder for generated audio and reports",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    data = load_risk_data(args.summary_csv, args.region_csv, args.horizon_csv)
    prompts = build_scripts(data.summary, data.regions, data.horizons)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline_text_path = output_dir / "baseline_script.txt"
    improved_text_path = output_dir / "improved_script.txt"
    baseline_text_path.write_text(prompts.baseline_script, encoding="utf-8")
    improved_text_path.write_text(prompts.improved_script, encoding="utf-8")

    synthesizer = SpeechT5Synthesizer()

    baseline_audio = synthesizer.synthesize_to_file(
        prompts.baseline_script,
        output_dir / "baseline_briefing.wav",
    )
    improved_audio = synthesizer.synthesize_to_file(
        prompts.improved_script,
        output_dir / "improved_briefing.wav",
    )

    evaluator = AudioEvaluator()
    baseline_transcript = evaluator.transcribe(baseline_audio.audio_path)
    improved_transcript = evaluator.transcribe(improved_audio.audio_path)

    baseline_row = evaluate_pair(
        setting_name="baseline",
        intended_script=prompts.baseline_script,
        transcribed_script=baseline_transcript,
        tts_latency_seconds=baseline_audio.latency_seconds,
        required_facts=prompts.required_facts,
    )
    improved_row = evaluate_pair(
        setting_name="improved",
        intended_script=prompts.improved_script,
        transcribed_script=improved_transcript,
        tts_latency_seconds=improved_audio.latency_seconds,
        required_facts=prompts.required_facts,
    )

    save_evaluation_artifacts([baseline_row, improved_row], output_dir)

    print("Done.")
    print(f"Audio files: {baseline_audio.audio_path}, {improved_audio.audio_path}")
    print(f"Evaluation CSV: {(output_dir / 'evaluation_results.csv').as_posix()}")
    print(f"Evaluation report: {(output_dir / 'evaluation_report.md').as_posix()}")


if __name__ == "__main__":
    main()
