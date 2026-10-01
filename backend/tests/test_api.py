import io
from fastapi.testclient import TestClient
from app import main
from app.formats import Segment
from app.transcriber import ASRError, ASRService

client = TestClient(main.app)


class FakeService:
    def transcribe(self, path, model="base", language=None, task="transcribe"):
        return [Segment(0, 1.2, " hello api")], "en", 1.2


def post(name="a.wav", data=b"RIFFfake", **form):
    return client.post("/api/transcribe", files={"file": (name, io.BytesIO(data))}, data=form)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_frontend_served():
    r = client.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]


def test_transcribe_ok(monkeypatch):
    monkeypatch.setattr(main, "asr_service", FakeService())
    r = post(model="tiny", language="en")
    assert r.status_code == 200
    body = r.json()
    assert body["text"] == "hello api" and body["language"] == "en"
    assert "00:00:00,000 --> 00:00:01,200" in body["srt"]
    assert body["vtt"].startswith("WEBVTT")


def test_bad_extension():
    r = post(name="notes.txt")
    assert r.status_code == 400 and "Unsupported" in r.json()["detail"]


def test_empty_file(monkeypatch):
    monkeypatch.setattr(main, "asr_service", FakeService())
    assert post(data=b"").status_code == 400


def test_too_large(monkeypatch):
    monkeypatch.setattr(main, "MAX_UPLOAD_MB", 0)
    monkeypatch.setattr(main, "asr_service", FakeService())
    assert post(data=b"x" * 10).status_code == 413


def test_service_error_is_400(monkeypatch):
    class Boom:
        def transcribe(self, *a, **k):
            raise ASRError("bad audio")
    monkeypatch.setattr(main, "asr_service", Boom())
    r = post()
    assert r.status_code == 400 and r.json()["detail"] == "bad audio"


def test_unknown_model_validation():
    import pytest
    with pytest.raises(ASRError):
        ASRService().transcribe("x.wav", model="gigantic")
