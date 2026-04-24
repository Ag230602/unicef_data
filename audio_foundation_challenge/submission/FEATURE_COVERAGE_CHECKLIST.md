# Requested Feature Coverage Checklist

This file maps your requested assignment features to implementation.

## 1) Better prompts for music generation
- Implemented in: [../onsite_prompt_app.py](../onsite_prompt_app.py)
- Helper: [../src/onsite_assistant.py](../src/onsite_assistant.py) -> `build_music_prompt()`
- Model: `facebook/musicgen-small`

## 2) Noisy vs clean speech input
- Implemented in: [../onsite_prompt_app.py](../onsite_prompt_app.py)
- Helper: `compare_clean_vs_noisy()` + `add_white_noise()`
- Model: `openai/whisper-small`

## 3) Multilingual speech testing
- Implemented in: [../onsite_prompt_app.py](../onsite_prompt_app.py)
- Model: `facebook/nllb-200-distilled-600M`

## 4) Style prompts
- Implemented in music prompt controls (style field + intensity)

## 5) Domain-specific customization
- Implemented via humanitarian context selector and domain-focused prompt assembly

## 6) Voice cloning assistant
- Implemented in translation/TTS tab with optional reference voice upload
- Model family: SpeechT5 (`microsoft/speecht5_tts` + `microsoft/speecht5_hifigan`)

## 7) Multilingual translator
- Implemented in translation/TTS tab
- Supports: English, French, Spanish, Portuguese, Arabic, Hindi, Swahili

## 8) Onsite prompt (not pre-generated)
- Main design goal of [../onsite_prompt_app.py](../onsite_prompt_app.py)
- User enters live prompts and gets on-demand outputs.
