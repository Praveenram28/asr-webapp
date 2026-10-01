import json
from app.formats import Segment, to_json, to_srt, to_txt, to_vtt, _timestamp

SEGS = [Segment(0.0, 1.5, " Hello world."), Segment(3661.25, 3662.0, "Second line")]


def test_timestamp():
    assert _timestamp(3661.25, ",") == "01:01:01,250"


def test_txt():
    assert to_txt(SEGS) == "Hello world.\nSecond line\n"


def test_srt():
    out = to_srt(SEGS)
    assert out.startswith("1\n00:00:00,000 --> 00:00:01,500\nHello world.")
    assert "2\n01:01:01,250 --> 01:01:02,000" in out


def test_vtt():
    assert to_vtt(SEGS).startswith("WEBVTT")


def test_json():
    data = json.loads(to_json(SEGS, "en"))
    assert data["text"] == "Hello world. Second line"
