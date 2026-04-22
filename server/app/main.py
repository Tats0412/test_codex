"""FastAPI entrypoint for the AI vocal trainer."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .analyze import extract_features, features_to_dict
from .coach import generate_feedback

load_dotenv()
logger = logging.getLogger("vocal_trainer")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Vocal Trainer", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".webm", ".mp4"}
MAX_BYTES = 25 * 1024 * 1024  # 25 MB


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(
    audio: UploadFile = File(...),
    song_title: str = Form(...),
    artist: str = Form(""),
    user_note: str = Form(""),
) -> dict:
    suffix = Path(audio.filename or "").suffix.lower()
    if suffix and suffix not in ALLOWED_EXTS:
        raise HTTPException(400, f"Unsupported audio format: {suffix}")

    data = await audio.read()
    if len(data) == 0:
        raise HTTPException(400, "Empty audio upload")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Audio file too large (max 25 MB)")

    with tempfile.NamedTemporaryFile(suffix=suffix or ".m4a", delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)

    try:
        logger.info("Extracting features from %s (%d bytes)", tmp_path.name, len(data))
        features = extract_features(tmp_path)
        features_dict = features_to_dict(features)

        logger.info("Requesting Claude feedback for %r", song_title)
        feedback = generate_feedback(
            features=features_dict,
            song_title=song_title,
            artist=artist,
            user_note=user_note,
        )
    except ValueError as e:
        raise HTTPException(422, f"Failed to parse Claude response: {e}")
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    finally:
        tmp_path.unlink(missing_ok=True)

    return {
        "features": features_dict,
        "feedback": feedback,
    }
