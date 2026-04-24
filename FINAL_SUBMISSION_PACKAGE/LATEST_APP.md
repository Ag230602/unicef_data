# Latest App With Everything

Latest complete app: `streamlit_app.py` at repository root.

It includes:
- Risk/Rescue/Supply dashboard
- Audio Briefing tab
- AI Assistance panel
- Onsite AI tab with multimodal chains:
  - speech -> text -> summary -> voice narration
  - text -> music -> video montage
  - voice -> translation -> cloned speech output

Run locally:
1. `python -m venv .venv`
2. `source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python -m pip install -r audio_foundation_challenge/requirements.txt`
5. `streamlit run streamlit_app.py`

Primary folder for assignment submission artifacts:
- `audio_foundation_challenge/`
- mirror copy: `FINAL_SUBMISSION_PACKAGE/audio_foundation_challenge/`
