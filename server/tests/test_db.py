import importlib
from pathlib import Path


def test_session_roundtrip(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SESSION_DB_PATH", str(tmp_path / "sessions.db"))
    # Reimport so the module picks up the new env-based path
    from app import db as db_module
    importlib.reload(db_module)

    db_module.init_db()
    sid = db_module.save_session(
        song_title="テスト曲",
        artist="テスト歌手",
        user_note="",
        features={"pitch_stability_cents": 15.0},
        feedback={"overall_score": 80, "one_point": "ok"},
        comparison=None,
    )
    assert sid > 0

    listed = db_module.list_sessions()
    assert len(listed) == 1
    assert listed[0]["song_title"] == "テスト曲"
    assert listed[0]["overall"] == 80

    detail = db_module.get_session(sid)
    assert detail["feedback"]["overall_score"] == 80
    assert detail["features"]["pitch_stability_cents"] == 15.0
    assert detail.get("comparison") is None

    assert db_module.delete_session(sid) is True
    assert db_module.get_session(sid) is None
