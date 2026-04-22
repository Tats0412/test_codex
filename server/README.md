# AI Vocal Trainer — Server

FastAPI backend that accepts a karaoke recording, extracts vocal features with
librosa, and asks Claude (Sonnet 4.6) to return actionable coaching feedback.

## Setup

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY
```

### System dependencies

`librosa` needs `ffmpeg` (and `libsndfile`) to decode m4a/mp3/webm.

- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt-get install ffmpeg libsndfile1`

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: `curl http://localhost:8000/health`

## API

### `POST /analyze`

Multipart form fields:

| field | type | required | description |
| --- | --- | --- | --- |
| `audio` | file | yes | WAV/MP3/M4A/AAC/FLAC/OGG/WEBM, ≤25 MB |
| `song_title` | string | yes | 曲名 |
| `artist` | string | no | アーティスト名 |
| `user_note` | string | no | ユーザーが気にしている点 |

Response:

```json
{
  "features": { "pitch_stability_cents": 18.2, "vibrato_rate_hz": 5.4, ... },
  "feedback": {
    "overall_score": 78,
    "scores": {"pitch": 82, "rhythm": 75, "expression": 70, "stability": 80},
    "one_point": "...",
    "strengths": ["..."],
    "improvements": [{"area": "音程", "detail": "...", "drill": "..."}],
    "song_specific": "...",
    "next_step": "..."
  }
}
```

## Endpoints

| method | path | purpose |
| --- | --- | --- |
| `POST` | `/analyze` | 録音を解析してフィードバックを返す。`reference` を付けるとお手本比較も返す |
| `GET` | `/sessions` | 過去のセッション一覧 |
| `GET` | `/sessions/{id}` | セッションの詳細(特徴量・フィードバック・比較結果) |
| `DELETE` | `/sessions/{id}` | セッション削除 |

## Tests

```bash
pip install pytest
pytest tests/ -q
```

テストは合成トーン(librosa で生成)を用いるので録音データ不要・API不要で走ります。

## Notes

- Claude cannot process audio directly. Features are extracted server-side
  and passed as text, together with the song title — Claude then reasons
  about the song from its own knowledge.
- If you later want reference-track comparison, add a second upload slot and
  run DTW alignment of the pitch contours (`librosa.sequence.dtw`) before
  prompting Claude.
