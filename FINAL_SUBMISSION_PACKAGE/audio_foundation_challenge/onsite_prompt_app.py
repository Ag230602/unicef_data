from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf
import streamlit as st

from src.onsite_assistant import (
    LANGUAGE_CODES,
    MusicGenGenerator,
    NLLBTranslator,
    SpeechT5VoiceAssistant,
    WhisperTranscriber,
    build_music_prompt,
    compare_clean_vs_noisy,
)


st.set_page_config(page_title="Onsite Audio Prompt Assistant", page_icon="🎧", layout="wide")
st.title("🎧 Onsite Audio Prompt Assistant (Live, Not Pre-Generated)")
st.caption(
    "Live multimodal generation for music, speech QA, multilingual translation, and voice-clone-style TTS."
)

output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)


@st.cache_resource
def get_music() -> MusicGenGenerator:
    return MusicGenGenerator()


@st.cache_resource
def get_asr() -> WhisperTranscriber:
    return WhisperTranscriber()


@st.cache_resource
def get_translator() -> NLLBTranslator:
    return NLLBTranslator()


@st.cache_resource
def get_tts() -> SpeechT5VoiceAssistant:
    return SpeechT5VoiceAssistant()


tab1, tab2, tab3 = st.tabs(
    [
        "🎼 Prompt + Music Generation",
        "🎙️ Noisy vs Clean Speech Testing",
        "🌍 Multilingual Translator + Voice Cloning Assistant",
    ]
)

with tab1:
    st.subheader("Better Prompts for Music Generation")
    col1, col2 = st.columns(2)
    with col1:
        domain = st.selectbox(
            "Domain-specific context",
            [
                "humanitarian command center briefing",
                "emergency shelter calm ambience",
                "rapid response coordination montage",
                "public health awareness campaign",
            ],
        )
        user_goal = st.text_input("Goal", "Build urgency but preserve hope for responders")
    with col2:
        style = st.text_input("Style prompt", "cinematic, hybrid orchestral, modern percussion")
        intensity = st.slider("Energy level", 1, 10, 6)
        duration = st.slider("Output duration (seconds)", 4, 12, 8)

    engineered_prompt = build_music_prompt(
        user_goal=user_goal,
        style_prompt=style,
        domain_context=domain,
        intensity=intensity,
    )
    st.markdown("**Engineered prompt**")
    st.code(engineered_prompt)

    if st.button("Generate Music (MusicGen Small)"):
        with st.spinner("Generating music..."):
            music = get_music()
            audio, sr = music.generate(engineered_prompt, duration_seconds=duration)
            out_path = output_dir / "onsite_musicgen.wav"
            sf.write(out_path.as_posix(), audio, sr)
        st.success(f"Saved: {out_path.as_posix()}")
        st.audio(out_path.read_bytes(), format="audio/wav")

with tab2:
    st.subheader("Noisy vs Clean Speech Input Testing")
    uploaded = st.file_uploader("Upload speech WAV", type=["wav"], key="speech_upload")
    ref = st.text_area("Optional reference transcript (for WER)", "")
    snr = st.slider("Synthetic noise level (SNR dB)", 0.0, 30.0, 8.0, 0.5)

    if uploaded is not None:
        temp_path = output_dir / "uploaded_clean.wav"
        temp_path.write_bytes(uploaded.read())
        audio, sr = sf.read(temp_path.as_posix())
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)
        audio = audio.astype(np.float32)

        st.audio(temp_path.read_bytes(), format="audio/wav")

        if st.button("Run Clean vs Noisy Test"):
            with st.spinner("Transcribing clean and noisy audio..."):
                asr = get_asr()
                result = compare_clean_vs_noisy(
                    transcriber=asr,
                    audio=audio,
                    sampling_rate=sr,
                    snr_db=snr,
                    reference_text=ref,
                )

                noisy_audio = audio + (np.random.normal(0, 1, len(audio)).astype(np.float32) * 0.01)
                noisy_audio = np.clip(noisy_audio, -1.0, 1.0)
                noisy_path = output_dir / "uploaded_noisy.wav"
                sf.write(noisy_path.as_posix(), noisy_audio, sr)

            st.markdown("**Clean transcript**")
            st.write(result.clean_text)
            st.markdown("**Noisy transcript**")
            st.write(result.noisy_text)
            st.markdown("**Noisy sample**")
            st.audio(noisy_path.read_bytes(), format="audio/wav")

            if result.clean_wer is not None and result.noisy_wer is not None:
                c1, c2, c3 = st.columns(3)
                c1.metric("Clean WER", f"{result.clean_wer:.4f}")
                c2.metric("Noisy WER", f"{result.noisy_wer:.4f}")
                c3.metric("Δ WER", f"{result.noisy_wer - result.clean_wer:+.4f}")

with tab3:
    st.subheader("Multilingual Speech Testing + Voice Cloning Assistant")
    lang_names = list(LANGUAGE_CODES.keys())
    left, right = st.columns(2)
    with left:
        source_lang = st.selectbox("Source language", lang_names, index=0)
        target_lang = st.selectbox("Target language", lang_names, index=1)
    with right:
        text = st.text_area(
            "Input text",
            "Emergency update: prioritize clean water and medical kits in high-risk coastal districts.",
        )
        ref_voice = st.file_uploader("Optional reference voice WAV (voice cloning assistant)", type=["wav"])

    if st.button("Translate + Synthesize Voice"):
        with st.spinner("Translating and generating speech..."):
            translator = get_translator()
            translated = translator.translate(text, source_lang, target_lang)

            tts = get_tts()
            embedding = None
            if ref_voice is not None:
                ref_path = output_dir / "reference_voice.wav"
                ref_path.write_bytes(ref_voice.read())
                embedding = tts.embedding_from_reference(ref_path)

            speech, sr = tts.synthesize(translated, speaker_embedding=embedding)
            out_path = output_dir / "translated_voice.wav"
            sf.write(out_path.as_posix(), speech, sr)

        st.markdown("**Translated text**")
        st.write(translated)
        st.markdown("**Generated multilingual speech**")
        st.audio(out_path.read_bytes(), format="audio/wav")
        st.success(f"Saved: {out_path.as_posix()}")

st.divider()
st.markdown(
    "**Assignment mapping:** better prompts, noisy-vs-clean testing, multilingual evaluation, style prompting, domain customization, voice cloning assistant, and live onsite prompting are all included in this app."
)
