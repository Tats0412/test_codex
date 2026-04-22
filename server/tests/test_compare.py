from pathlib import Path

from app.compare import compare_to_reference
from tests.helpers import write_tone


def test_identical_tones_match(tmp_path: Path):
    ref = write_tone(tmp_path / "ref.wav", freq_hz=440.0, duration_sec=2.0)
    usr = write_tone(tmp_path / "usr.wav", freq_hz=440.0, duration_sec=2.0)
    r = compare_to_reference(usr, ref)
    assert r.key_offset_semitones == 0
    assert r.avg_abs_cents_off < 15
    assert r.pitch_match_ratio > 0.9


def test_transposed_user_detected(tmp_path: Path):
    ref = write_tone(tmp_path / "ref.wav", freq_hz=440.0, duration_sec=2.0)
    # User sings 2 semitones higher (B4 = 493.88 Hz)
    usr = write_tone(tmp_path / "usr.wav", freq_hz=493.88, duration_sec=2.0)
    r = compare_to_reference(usr, ref)
    assert r.key_offset_semitones == 2
    assert r.avg_abs_cents_off < 20


def test_off_pitch_flagged(tmp_path: Path):
    ref = write_tone(tmp_path / "ref.wav", freq_hz=440.0, duration_sec=2.0)
    # User sings 40 cents flat — within the same semitone bucket, so no
    # auto-transposition should happen and the deviation should be reported.
    flat_hz = 440.0 * (2 ** (-0.4 / 12.0))
    usr = write_tone(tmp_path / "usr.wav", freq_hz=flat_hz, duration_sec=2.0)
    r = compare_to_reference(usr, ref)
    assert r.key_offset_semitones == 0
    assert r.avg_abs_cents_off > 25
    assert r.pitch_match_ratio < 0.7
