from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
import soundfile as sf
import torch
from jiwer import wer
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoProcessor,
    AutoTokenizer,
    MusicgenForConditionalGeneration,
    SpeechT5ForTextToSpeech,
    SpeechT5HifiGan,
    SpeechT5Processor,
    pipeline,
)


LANGUAGE_CODES = {
    "English": "eng_Latn",
    "French": "fra_Latn",
    "Spanish": "spa_Latn",
    "Portuguese": "por_Latn",
    "Arabic": "arb_Arab",
    "Hindi": "hin_Deva",
    "Swahili": "swh_Latn",
}


@dataclass
class SpeechComparison:
    clean_text: str
    noisy_text: str
    clean_wer: float | None
    noisy_wer: float | None


def build_music_prompt(
    user_goal: str,
    style_prompt: str,
    domain_context: str,
    intensity: int,
) -> str:
    return (
        f"Create instrumental music for {domain_context}. "
        f"Goal: {user_goal}. "
        f"Style: {style_prompt}. "
        f"Energy level {intensity}/10. "
        "No vocals, modern cinematic texture, emotionally supportive, clean mix."
    )


def add_white_noise(audio: np.ndarray, snr_db: float = 10.0) -> np.ndarray:
    audio = np.asarray(audio, dtype=np.float32)
    rms_signal = np.sqrt(np.mean(audio**2) + 1e-12)
    rms_noise = rms_signal / (10 ** (snr_db / 20))
    noise = np.random.normal(0.0, rms_noise, size=audio.shape).astype(np.float32)
    noisy = audio + noise
    return np.clip(noisy, -1.0, 1.0)


def normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def split_sentences(text: str) -> list[str]:
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    return parts or [text.strip() or "No text provided."]


class WhisperTranscriber:
    def __init__(self, model_id: str = "openai/whisper-small") -> None:
        self.asr = pipeline(
            task="automatic-speech-recognition",
            model=model_id,
            device=0 if torch.cuda.is_available() else -1,
        )

    def transcribe_audio_array(self, audio: np.ndarray, sampling_rate: int) -> str:
        out = self.asr({"raw": audio, "sampling_rate": sampling_rate}, return_timestamps=True)
        if isinstance(out, dict):
            return str(out.get("text", "")).strip()
        return str(out).strip()


class MusicGenGenerator:
    def __init__(self, model_id: str = "facebook/musicgen-small") -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model: Any = MusicgenForConditionalGeneration.from_pretrained(model_id)
        self.model = self.model.to(self.device)

    def generate(self, prompt: str, duration_seconds: int = 8) -> tuple[np.ndarray, int]:
        token_budget = max(128, min(1024, duration_seconds * 64))
        inputs = self.processor(text=[prompt], padding=True, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.inference_mode():
            audio_values = self.model.generate(**inputs, max_new_tokens=token_budget)
        cfg = getattr(self.model.config, "audio_encoder", {})
        sample_rate = int(getattr(cfg, "sampling_rate", 32000))
        audio = audio_values[0, 0].detach().cpu().numpy().astype(np.float32)
        return audio, sample_rate


class NLLBTranslator:
    def __init__(self, model_id: str = "facebook/nllb-200-distilled-600M") -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_id).to(self.device)

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        src = LANGUAGE_CODES[source_language]
        tgt = LANGUAGE_CODES[target_language]
        self.tokenizer.src_lang = src
        encoded = self.tokenizer(text, return_tensors="pt")
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        with torch.inference_mode():
            generated = self.model.generate(
                **encoded,
                forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(tgt),
                max_new_tokens=256,
            )
        return self.tokenizer.batch_decode(generated, skip_special_tokens=True)[0]


class TextSummarizer:
    def __init__(self, model_id: str = "sshleifer/distilbart-cnn-12-6") -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_id).to(self.device)

    def summarize(self, text: str) -> str:
        clean = " ".join(text.split())
        if len(clean.split()) < 25:
            return clean
        encoded = self.tokenizer(clean, return_tensors="pt", truncation=True, max_length=1024)
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        with torch.inference_mode():
            generated = self.model.generate(**encoded, max_new_tokens=90, min_new_tokens=25)
        return self.tokenizer.batch_decode(generated, skip_special_tokens=True)[0].strip()


class SpeechT5VoiceAssistant:
    def __init__(
        self,
        tts_model_id: str = "microsoft/speecht5_tts",
        vocoder_id: str = "microsoft/speecht5_hifigan",
    ) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = SpeechT5Processor.from_pretrained(tts_model_id)
        self.model: Any = SpeechT5ForTextToSpeech.from_pretrained(tts_model_id)
        self.model = self.model.to(self.device)
        self.vocoder: Any = SpeechT5HifiGan.from_pretrained(vocoder_id)
        self.vocoder = self.vocoder.to(self.device)

    def default_embedding(self) -> torch.Tensor:
        return torch.zeros((1, 512), dtype=torch.float32, device=self.device)

    def embedding_from_reference(self, reference_wav_path: str | Path) -> torch.Tensor:
        # Lightweight voice cloning proxy: derive deterministic embedding from audio statistics.
        # This avoids requiring extra heavyweight speaker-encoder models during onsite demos.
        audio, sr = sf.read(str(reference_wav_path))
        audio = np.asarray(audio, dtype=np.float32)
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)

        if len(audio) == 0:
            return self.default_embedding()

        stats = np.array(
            [
                float(np.mean(audio)),
                float(np.std(audio)),
                float(np.max(audio)),
                float(np.min(audio)),
                float(np.percentile(audio, 25)),
                float(np.percentile(audio, 50)),
                float(np.percentile(audio, 75)),
                float(sr / 48000.0),
            ],
            dtype=np.float32,
        )
        repeated = np.resize(stats, 512)
        emb = torch.tensor(repeated, dtype=torch.float32, device=self.device).unsqueeze(0)
        emb = torch.nn.functional.normalize(emb, dim=-1)
        return emb

    def synthesize(self, text: str, speaker_embedding: torch.Tensor | None = None) -> tuple[np.ndarray, int]:
        emb = speaker_embedding if speaker_embedding is not None else self.default_embedding()
        emb = cast(torch.FloatTensor, emb)
        inputs = cast(dict[str, torch.Tensor], self.processor(text=text, return_tensors="pt"))
        input_ids = inputs.get("input_ids")
        if input_ids is None:
            raise ValueError("Failed to tokenize input text.")
        input_ids = input_ids.to(self.device)

        with torch.inference_mode():
            out = self.model.generate_speech(
                input_ids=input_ids,
                speaker_embeddings=emb,
                vocoder=self.vocoder,
            )
        speech = out[0] if isinstance(out, tuple) else out
        return speech.detach().cpu().numpy().astype(np.float32), 16000


def compare_clean_vs_noisy(
    transcriber: WhisperTranscriber,
    audio: np.ndarray,
    sampling_rate: int,
    snr_db: float,
    reference_text: str | None = None,
) -> SpeechComparison:
    noisy = add_white_noise(audio, snr_db=snr_db)
    clean_text = transcriber.transcribe_audio_array(audio, sampling_rate)
    noisy_text = transcriber.transcribe_audio_array(noisy, sampling_rate)

    clean_wer = None
    noisy_wer = None
    if reference_text and reference_text.strip():
        ref = normalize_text(reference_text)
        clean_wer = float(wer(ref, normalize_text(clean_text)))
        noisy_wer = float(wer(ref, normalize_text(noisy_text)))

    return SpeechComparison(
        clean_text=clean_text,
        noisy_text=noisy_text,
        clean_wer=clean_wer,
        noisy_wer=noisy_wer,
    )


def build_music_video_montage_html(
        text: str,
        title: str,
        audio_rel_path: str,
        output_html_path: str | Path,
) -> Path:
        output_html_path = Path(output_html_path)
        output_html_path.parent.mkdir(parents=True, exist_ok=True)

        slides = split_sentences(text)[:8]
        escaped_title = html.escape(title)
        escaped_audio = html.escape(audio_rel_path)
        slide_js = ",\n        ".join([f'"{html.escape(s)}"' for s in slides])

        content = f"""<!doctype html>
<html>
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{escaped_title}</title>
    <style>
        body {{ margin:0; background:#04080f; color:#ddeeff; font-family:Inter,Arial,sans-serif; }}
        .wrap {{ height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; }}
        h1 {{ color:#00e5ff; letter-spacing:1px; margin-bottom:14px; }}
        .slide {{
            width:min(900px,88vw); min-height:180px; border:1px solid rgba(0,170,255,.25);
            border-radius:14px; background:rgba(12,21,38,.85); padding:24px; font-size:28px; line-height:1.35;
            box-shadow:0 12px 40px rgba(0,0,0,.25);
        }}
        .hint {{ margin-top:12px; font-size:12px; color:#7ca5c7; }}
        audio {{ margin-top:16px; width:min(900px,88vw); }}
    </style>
</head>
<body>
    <div class=\"wrap\">
        <h1>{escaped_title}</h1>
        <div class=\"slide\" id=\"slide\"></div>
        <audio controls autoplay loop src=\"{escaped_audio}\"></audio>
        <div class=\"hint\">Text → Music → Video Montage (HTML). Use screen recording for MP4 demo capture.</div>
    </div>
    <script>
        const slides = [{slide_js}];
        let i = 0;
        const node = document.getElementById('slide');
        function tick() {{
            node.textContent = slides[i % slides.length];
            i += 1;
        }}
        tick();
        setInterval(tick, 3500);
    </script>
</body>
</html>
"""
        output_html_path.write_text(content, encoding="utf-8")
        return output_html_path
