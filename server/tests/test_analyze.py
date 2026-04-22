from pathlib import Path

from app.analyze import extract_features
from tests.helpers import write_tone


def test_pure_tone_is_very_in_tune(tmp_path: Path):
    wav = write_tone(tmp_path / "a4.wav", freq_hz=440.0, duration_sec=2.5)
    f = extract_features(wav)
    assert 2.0 < f.duration_sec < 3.0
    assert f.median_pitch_hz == 0 or 430 < f.median_pitch_hz < 450
    assert f.in_tune_ratio > 0.9
    assert f.pitch_stability_cents < 10
    # No vibrato in a pure tone
    assert f.vibrato_rate_hz == 0.0 or f.vibrato_extent_cents < 20


def test_vibrato_tone_reports_vibrato(tmp_path: Path):
    wav = write_tone(
        tmp_path / "vib.wav",
        freq_hz=440.0,
        duration_sec=3.0,
        vibrato_hz=5.5,
        vibrato_cents=40.0,
    )
    f = extract_features(wav)
    assert f.vibrato_extent_cents > 15
    assert 4.0 < f.vibrato_rate_hz < 7.0


def test_contours_present_and_aligned(tmp_path: Path):
    wav = write_tone(tmp_path / "a4.wav", freq_hz=440.0, duration_sec=2.0)
    f = extract_features(wav)
    assert len(f.pitch_contour_midi) == len(f.contour_times_sec)
    assert len(f.loudness_contour_db) == len(f.contour_times_sec)
    assert f.contour_times_sec[0] == 0.0
    assert f.contour_times_sec[-1] > 1.0
