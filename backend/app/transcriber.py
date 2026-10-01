"""Core ASR service wrapping faster-whisper (models are cached after first load)."""
import os
import threading
from typing import List, Optional, Tuple

from .formats import Segment

AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".opus", ".wma", ".aac",
                    ".mp4", ".mkv", ".webm"}
MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v3"]


class ASRError(Exception):
    """Raised for user-facing ASR errors."""


def validate_extension(filename: str) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in AUDIO_EXTENSIONS:
        raise ASRError(f"Unsupported file type '{ext or 'unknown'}'. "
                       f"Supported: {', '.join(sorted(AUDIO_EXTENSIONS))}")
    return ext


class ASRService:
    def __init__(self, device: str = "cpu", compute_type: str = "int8"):
        self.device, self.compute_type = device, compute_type
        self._models = {}
        self._lock = threading.Lock()

    def _get_model(self, size: str):
        with self._lock:
            if size not in self._models:
                try:
                    from faster_whisper import WhisperModel
                except ImportError as e:
                    raise ASRError("faster-whisper is not installed. "
                                   "Run: pip install -r requirements.txt") from e
                self._models[size] = WhisperModel(size, device=self.device,
                                                  compute_type=self.compute_type)
            return self._models[size]

    def transcribe(self, path: str, model: str = "base", language: Optional[str] = None,
                   task: str = "transcribe") -> Tuple[List[Segment], str, float]:
        """Return (segments, detected_language, audio_duration_seconds)."""
        if model not in MODEL_SIZES:
            raise ASRError(f"Unknown model '{model}'. Choose from: {', '.join(MODEL_SIZES)}")
        if task not in ("transcribe", "translate"):
            raise ASRError("task must be 'transcribe' or 'translate'")
        whisper = self._get_model(model)
        try:
            raw, info = whisper.transcribe(path, language=language or None, task=task,
                                           vad_filter=True, beam_size=5)
            segments = [Segment(s.start, s.end, s.text) for s in raw]
        except Exception as e:  # undecodable / corrupt audio etc.
            raise ASRError(f"Could not process audio: {e}") from e
        return segments, info.language, float(getattr(info, "duration", 0.0))
