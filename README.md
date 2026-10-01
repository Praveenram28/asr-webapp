# ASR Studio – Speech-to-Text Web App (Frontend + Backend)

A full-stack Automatic Speech Recognition (ASR) application. Upload an audio/video file or record from your microphone, and get a transcript with timestamps. Download results as TXT, SRT, VTT or JSON.

## Features
- Upload (drag & drop) or record audio directly in the browser
- Automatic language detection, or pick one (English, Tamil, Hindi, Telugu, etc.)
- Translate speech to English
- 5 model sizes: tiny to large-v3 (speed vs. accuracy)
- Timestamped segments; click a segment to jump to that point in the audio
- Copy transcript, download as TXT / SRT / VTT / JSON
- REST API with auto-generated docs at `/docs`
- Light/dark theme, responsive layout
- Unit and API tests (pytest)

## Tools & Technologies Used
| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, vanilla JavaScript (Fetch API, MediaRecorder API, Drag & Drop API) |
| Backend | Python 3.9+, FastAPI, Uvicorn, python-multipart |
| ASR engine | faster-whisper (CTranslate2 implementation of OpenAI Whisper) |
| Audio decoding | PyAV (bundled with faster-whisper; no FFmpeg install needed) |
| Testing | pytest, FastAPI TestClient, httpx |
| Tooling | Git, GitHub, VS Code |

## Project Structure
```
asr-webapp/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, REST endpoints, serves frontend
│   │   ├── transcriber.py   # ASR service (model loading/caching, validation)
│   │   └── formats.py       # TXT / SRT / VTT / JSON formatters
│   ├── tests/               # pytest tests (formatters + API)
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── index.html           # UI
│   ├── style.css            # styling
│   └── app.js               # upload, recording, API calls, downloads
├── .vscode/launch.json      # F5 debug config for VS Code
├── .gitignore
└── README.md
```

## How to Run

### 1. Setup
```bash
cd asr-webapp/backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start the server (from the `backend` folder)
```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Open the app
- Web UI: http://127.0.0.1:8000
- API docs (Swagger): http://127.0.0.1:8000/docs

The first transcription downloads the selected model (`base` is about 140 MB) and caches it. Later requests are faster.

### 4. Run the tests
```bash
cd backend
pytest -v
```

## API
`GET /api/health` returns status and the available models.

`POST /api/transcribe` (multipart/form-data):

| Field | Description | Default |
|-------|-------------|---------|
| `file` | audio/video file | required |
| `model` | tiny, base, small, medium, large-v3 | base |
| `language` | language code, empty = auto | "" |
| `task` | `transcribe` or `translate` | transcribe |

Example:
```bash
curl -F file=@clip.mp3 -F model=base http://127.0.0.1:8000/api/transcribe
```
Response: `{ language, duration, text, segments[], txt, srt, vtt }`

## Configuration (environment variables)
| Variable | Meaning | Default |
|----------|---------|---------|
| `ASR_MAX_UPLOAD_MB` | upload size limit | 50 |
| `ASR_DEVICE` | `cpu` or `cuda` | cpu |
| `ASR_COMPUTE` | `int8` (CPU) / `float16` (GPU) | int8 |

## Hosting the frontend separately (optional)
The backend already serves the frontend. To host it elsewhere, set `window.ASR_API_BASE = "http://127.0.0.1:8000"` before `app.js` loads in `index.html`. CORS is enabled on the backend.

## Notes
- Microphone recording requires `localhost`/`127.0.0.1` or HTTPS (browser security rule).
- Accuracy depends on audio quality, accents and model size; larger models are slower on CPU.

## License
MIT
