from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import soundfile as sf
import torch
from transformers import SpeechT5ForTextToSpeech, SpeechT5HifiGan, SpeechT5Processor


@dataclass
class SynthesisResult:
    audio_path: Path
    latency_seconds: float


class SpeechT5Synthesizer:
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

        self.speaker_embeddings = cast(
            torch.FloatTensor,
            torch.zeros((1, 512), dtype=torch.float32, device=self.device),
        )

    def synthesize_to_file(self, text: str, output_path: str | Path) -> SynthesisResult:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        inputs = cast(dict[str, torch.Tensor], self.processor(text=text, return_tensors="pt"))
        input_ids = inputs.get("input_ids")
        if input_ids is None:
            raise ValueError("Could not create input IDs from text.")
        input_ids = input_ids.to(self.device)

        start = time.perf_counter()
        with torch.inference_mode():
            speech_output = self.model.generate_speech(
                input_ids=input_ids,
                speaker_embeddings=self.speaker_embeddings,
                vocoder=self.vocoder,
            )
        latency = time.perf_counter() - start

        speech = speech_output[0] if isinstance(speech_output, tuple) else speech_output

        sf.write(output_path.as_posix(), speech.detach().cpu().numpy(), samplerate=16000)

        return SynthesisResult(audio_path=output_path, latency_seconds=latency)
