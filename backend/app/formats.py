"""Output formatters for transcription segments."""
import json
from dataclasses import dataclass, asdict
from typing import List


@dataclass
class Segment:
    start: float
    end: float
    text: str


def _timestamp(seconds: float, sep: str) -> str:
    ms_total = int(round(seconds * 1000))
    h, rem = divmod(ms_total, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def to_txt(segments: List[Segment]) -> str:
    return "\n".join(s.text.strip() for s in segments) + "\n"


def to_srt(segments: List[Segment]) -> str:
    blocks = [
        f"{i}\n{_timestamp(s.start, ',')} --> {_timestamp(s.end, ',')}\n{s.text.strip()}\n"
        for i, s in enumerate(segments, 1)
    ]
    return "\n".join(blocks)


def to_vtt(segments: List[Segment]) -> str:
    body = "\n".join(
        f"{_timestamp(s.start, '.')} --> {_timestamp(s.end, '.')}\n{s.text.strip()}\n"
        for s in segments
    )
    return "WEBVTT\n\n" + body


def to_json(segments: List[Segment], language: str = "") -> str:
    return json.dumps(
        {"language": language,
         "text": " ".join(s.text.strip() for s in segments),
         "segments": [asdict(s) for s in segments]},
        indent=2, ensure_ascii=False,
    )
