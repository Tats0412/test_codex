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


def test_song_filter_and_recent(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SESSION_DB_PATH", str(tmp_path / "sessions.db"))
    from app import db as db_module
    importlib.reload(db_module)

    db_module.init_db()
    db_module.save_session(
        "A", "artistA", "", {"x": 1}, {"overall_score": 70}, None
    )
    db_module.save_session(
        "A", "artistA", "", {"x": 1}, {"overall_score": 85}, None
    )
    db_module.save_session(
        "B", "artistB", "", {"x": 1}, {"overall_score": 60}, None
    )

    a_only = db_module.list_sessions(song="A")
    assert len(a_only) == 2
    assert all(r["song_title"] == "A" for r in a_only)

    songs = db_module.recent_songs()
    assert {s["song_title"] for s in songs} == {"A", "B"}
    a_row = next(s for s in songs if s["song_title"] == "A")
    assert a_row["times"] == 2
    assert a_row["best_score"] == 85
