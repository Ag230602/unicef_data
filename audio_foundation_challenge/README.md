# UNICEF Audio Foundation Model Challenge (Separate Folder)

This project is a complete, standalone submission scaffold for your audio/multimodal challenge using the **given UNICEF risk CSV data** in `../outputs/`.

## What this system does

It builds a practical speech intelligence pipeline:

1. Reads humanitarian risk metrics from provided CSVs.
2. Creates two spoken briefings:
   - **Baseline prompt/input setting**
   - **Improved prompt/input setting** (structured, domain-aware)
3. Generates speech audio with a pretrained foundation model:
   - `microsoft/speecht5_tts`
4. Evaluates outputs with:
   - **Transcription quality** (Whisper Small + WER)
   - **Latency** (TTS generation time)
   - **Summary quality proxy** (fact coverage score)
5. Saves audio + evaluation reports for GitHub/demo/slides.

---

## Models used

- TTS: `microsoft/speecht5_tts`
- Vocoder: `microsoft/speecht5_hifigan`
- ASR evaluator: `openai/whisper-small`

All are open-source models available through Hugging Face.

---

## Folder structure

- `run_pipeline.py` - end-to-end runner
- `src/data_loader.py` - reads UNICEF CSVs
- `src/prompt_engineering.py` - baseline vs improved script generation
- `src/tts_model.py` - SpeechT5 synthesis
- `src/evaluate.py` - WER, latency, quality metrics + report output
- `requirements.txt` - Python dependencies
- `slides/slide_outline.md` - ready 10+ slide content plan
- `demo/demo_script.md` - 1-2 minute demo talking points
- `outputs/` - generated artifacts

---

## Setup

```bash
cd audio_foundation_challenge
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python run_pipeline.py
```

Optional custom input location:

```bash
python run_pipeline.py \
  --summary-csv ../outputs/aots_humanitarian_risk_summary.csv \
  --region-csv ../outputs/aots_region_risk_scores.csv \
  --horizon-csv ../outputs/aots_expected_exposure_by_horizon.csv
```

---

## Generated outputs

In `outputs/` after running:

- `baseline_briefing.wav`
- `improved_briefing.wav`
- `baseline_script.txt`
- `improved_script.txt`
- `evaluation_results.csv`
- `evaluation_report.md`

---

## Evaluation design (required section)

This project compares baseline vs improved settings.

Metrics:

- **Transcription quality**: WER from Whisper transcript vs intended script
- **Latency**: TTS inference time in seconds
- **Summary quality proxy**: fact coverage score (0 to 1)

Interpretation:

- Lower WER is better
- Lower latency is better
- Higher coverage is better

---

## AI tools disclosure (for grading transparency)

Document in your final README/slides:

- GitHub Copilot (code drafting/refactoring)
- Hugging Face (model hosting + transformers)
- Any slide/video tools used (Canva, Gamma, etc.)

Use format: tool name, where used, what was AI-assisted.

---

## Notes

- First run downloads models and may take time.
- CPU is supported but slower.
- This scaffold is intentionally designed so you can directly build your required PPT/video/GitHub submission.
