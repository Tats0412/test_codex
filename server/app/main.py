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
from .compare import compare_to_reference, report_to_dict
from .db import delete_session, get_session, init_db, list_sessions, save_session

load_dotenv()
logger = logging.getLogger("vocal_trainer")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Vocal Trainer", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".webm", ".mp4"}
MAX_BYTES = 25 * 1024 * 1024  # 25 MB


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _save_upload(upload: UploadFile, data: bytes) -> Path:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix and suffix not in ALLOWED_EXTS:
        raise HTTPException(400, f"Unsupported audio format: {suffix}")
    with tempfile.NamedTemporaryFile(suffix=suffix or ".m4a", delete=False) as tmp:
        tmp.write(data)
        return Path(tmp.name)


@app.post("/analyze")
async def analyze(
    audio: UploadFile = File(...),
    song_title: str = Form(...),
    artist: str = Form(""),
    user_note: str = Form(""),
    reference: UploadFile | None = File(None),
) -> dict:
    audio_bytes = await audio.read()
    if len(audio_bytes) == 0:
        raise HTTPException(400, "Empty audio upload")
    if len(audio_bytes) > MAX_BYTES:
        raise HTTPException(413, "Audio file too large (max 25 MB)")
    user_path = _save_upload(audio, audio_bytes)

    ref_path: Path | None = None
    if reference is not None and reference.filename:
        ref_bytes = await reference.read()
        if len(ref_bytes) > MAX_BYTES:
            user_path.unlink(missing_ok=True)
            raise HTTPException(413, "Reference file too large (max 25 MB)")
        if ref_bytes:
            ref_path = _save_upload(reference, ref_bytes)

    try:
        logger.info("Extracting features from %s (%d bytes)", user_path.name, len(audio_bytes))
        features = features_to_dict(extract_features(user_path))

        comparison = None
        if ref_path is not None:
            logger.info("Comparing against reference %s", ref_path.name)
            comparison = report_to_dict(compare_to_reference(user_path, ref_path))

        logger.info("Requesting Claude feedback for %r", song_title)
        feedback = generate_feedback(
            features=features,
            song_title=song_title,
            artist=artist,
            user_note=user_note,
            comparison=comparison,
        )

        session_id = save_session(
            song_title=song_title,
            artist=artist,
            user_note=user_note,
            features=features,
            feedback=feedback,
            comparison=comparison,
        )
    except ValueError as e:
        raise HTTPException(422, f"Failed to parse Claude response: {e}")
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    finally:
        user_path.unlink(missing_ok=True)
        if ref_path is not None:
            ref_path.unlink(missing_ok=True)

    return {
        "session_id": session_id,
        "features": features,
        "comparison": comparison,
        "feedback": feedback,
    }


@app.get("/sessions")
def sessions() -> dict:
    return {"sessions": list_sessions()}


@app.get("/sessions/{session_id}")
def session_detail(session_id: int) -> dict:
    data = get_session(session_id)
    if not data:
        raise HTTPException(404, "Session not found")
    return data


@app.delete("/sessions/{session_id}")
def session_delete(session_id: int) -> dict:
    if not delete_session(session_id):
        raise HTTPException(404, "Session not found")
    return {"deleted": session_id}
