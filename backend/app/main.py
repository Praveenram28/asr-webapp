"""FastAPI backend: REST API + serves the frontend."""
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .formats import to_srt, to_txt, to_vtt
from .transcriber import ASRError, ASRService, MODEL_SIZES, validate_extension

MAX_UPLOAD_MB = int(os.environ.get("ASR_MAX_UPLOAD_MB", "50"))
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(title="ASR Web App", version="1.0.0",
              description="Speech-to-text API powered by faster-whisper")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

asr_service = ASRService(device=os.environ.get("ASR_DEVICE", "cpu"),
                         compute_type=os.environ.get("ASR_COMPUTE", "int8"))


@app.get("/api/health")
def health():
    return {"status": "ok", "models": MODEL_SIZES, "max_upload_mb": MAX_UPLOAD_MB}


@app.post("/api/transcribe")
def transcribe(file: UploadFile = File(...),
               model: str = Form("tiny"),
               language: str = Form(""),
               task: str = Form("transcribe")):
    try:
        ext = validate_extension(file.filename)
    except ASRError as e:
        raise HTTPException(status_code=400, detail=str(e))

    limit = MAX_UPLOAD_MB * 1024 * 1024
    size = 0
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    try:
        with tmp:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(status_code=413,
                                        detail=f"File too large (max {MAX_UPLOAD_MB} MB)")
                tmp.write(chunk)
        if size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        try:
            segments, lang, duration = asr_service.transcribe(tmp.name, model, language, task)
        except ASRError as e:
            raise HTTPException(status_code=400, detail=str(e))
    finally:
        os.unlink(tmp.name)

    return {
        "language": lang,
        "duration": round(duration, 2),
        "text": " ".join(s.text.strip() for s in segments),
        "segments": [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments],
        "txt": to_txt(segments),
        "srt": to_srt(segments),
        "vtt": to_vtt(segments),
    }


# Serve the frontend at "/" (must be registered last)
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
