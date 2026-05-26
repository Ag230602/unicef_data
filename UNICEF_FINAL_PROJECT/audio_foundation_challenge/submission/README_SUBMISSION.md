# Submission Pack (Audio Challenge)

This folder collects all assignment-ready audio materials in one place.

## Core code
- [../run_pipeline.py](../run_pipeline.py)
- [../onsite_prompt_app.py](../onsite_prompt_app.py)
- [../src/data_loader.py](../src/data_loader.py)
- [../src/prompt_engineering.py](../src/prompt_engineering.py)
- [../src/tts_model.py](../src/tts_model.py)
- [../src/evaluate.py](../src/evaluate.py)
- [../src/onsite_assistant.py](../src/onsite_assistant.py)

## Outputs for submission/demo
- [../outputs/baseline_briefing.wav](../outputs/baseline_briefing.wav)
- [../outputs/improved_briefing.wav](../outputs/improved_briefing.wav)
- [../outputs/baseline_script.txt](../outputs/baseline_script.txt)
- [../outputs/improved_script.txt](../outputs/improved_script.txt)
- [../outputs/evaluation_results.csv](../outputs/evaluation_results.csv)
- [../outputs/evaluation_report.md](../outputs/evaluation_report.md)

## Presentation + demo assets
- [../slides/slide_outline.md](../slides/slide_outline.md)
- [../demo/demo_script.md](../demo/demo_script.md)
- [../AI_TOOLS_DISCLOSURE.md](../AI_TOOLS_DISCLOSURE.md)
- [DASHBOARD_AI_ASSISTANCE.md](DASHBOARD_AI_ASSISTANCE.md)
- [FEATURE_COVERAGE_CHECKLIST.md](FEATURE_COVERAGE_CHECKLIST.md)

## Quick checklist before submit
- [ ] Run pipeline once and confirm outputs exist
- [ ] Record 1-2 minute demo video
- [ ] Create PPT (10+ slides) using slide outline
- [ ] Add GitHub link
- [ ] Add demo video link
- [ ] Include AI transparency disclosure

## Optional: regenerate outputs
From `audio_foundation_challenge/`:

- `python run_pipeline.py`
- `streamlit run onsite_prompt_app.py`
