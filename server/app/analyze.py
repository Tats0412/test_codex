"""Audio feature extraction for vocal recordings.

Given a path to a recording, returns a dict of musically meaningful numbers
that a language model can reason over (pitch stability, vibrato, rhythm,
dynamics, etc.).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path

import librosa
import numpy as np


@dataclass
class VocalFeatures:
    duration_sec: float
    tempo_bpm: float

    # Pitch
    median_pitch_hz: float
    pitch_range_semitones: float
    pitch_stability_cents: float  # std dev of detuning from nearest semitone
    in_tune_ratio: float          # fraction of voiced frames within 35 cents
    voiced_ratio: float           # fraction of frames that were voiced

    # Vibrato
    vibrato_rate_hz: float
    vibrato_extent_cents: float

    # Dynamics
    loudness_mean_db: float
    loudness_range_db: float
    dynamic_variation: float      # std dev of loudness in dB

    # Rhythm / timing
    onset_count: int
    onset_regularity: float       # 1 = perfectly regular, 0 = chaotic

    # Breath / pauses
    silence_ratio: float
    longest_phrase_sec: float


def _hz_to_cents_from_nearest_semitone(f0: np.ndarray) -> np.ndarray:
    """For each valid f0, return detuning in cents from the nearest semitone."""
    valid = f0[~np.isnan(f0) & (f0 > 0)]
    if valid.size == 0:
        return np.array([])
    midi = 69 + 12 * np.log2(valid / 440.0)
    return (midi - np.round(midi)) * 100.0


def _estimate_vibrato(f0: np.ndarray, sr_frames: float) -> tuple[float, float]:
    """Estimate vibrato rate (Hz) and extent (cents) from f0 contour."""
    f0 = f0.copy()
    f0[np.isnan(f0)] = 0.0
    if (f0 > 0).sum() < sr_frames * 0.3:
        return 0.0, 0.0

    voiced = f0[f0 > 0]
    midi = 69 + 12 * np.log2(voiced / 440.0)
    cents = (midi - np.mean(midi)) * 100.0

    # Band-pass-ish: detrend with rolling mean
    window = max(3, int(sr_frames * 0.25))  # 250ms window
    if window >= cents.size:
        return 0.0, 0.0
    kernel = np.ones(window) / window
    smooth = np.convolve(cents, kernel, mode="same")
    residual = cents - smooth

    # FFT to find dominant frequency in 3-9 Hz range (typical vibrato)
    n = residual.size
    spectrum = np.abs(np.fft.rfft(residual))
    freqs = np.fft.rfftfreq(n, d=1.0 / sr_frames)

    mask = (freqs >= 3.0) & (freqs <= 9.0)
    if not mask.any():
        return 0.0, 0.0
    band = spectrum[mask]
    if band.max() < spectrum.mean() * 2:
        return 0.0, float(np.std(residual))

    peak_hz = float(freqs[mask][np.argmax(band)])
    extent = float(np.std(residual) * math.sqrt(2))  # approx peak amplitude
    return peak_hz, extent


def _onset_regularity(onset_times: np.ndarray) -> float:
    if onset_times.size < 3:
        return 0.0
    intervals = np.diff(onset_times)
    if intervals.mean() == 0:
        return 0.0
    cv = np.std(intervals) / np.mean(intervals)
    return float(max(0.0, 1.0 - min(cv, 1.0)))


def _longest_voiced_run(voiced_flag: np.ndarray, hop_sec: float) -> float:
    longest = run = 0
    for v in voiced_flag:
        if v:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    return longest * hop_sec


def extract_features(path: str | Path) -> VocalFeatures:
    y, sr = librosa.load(str(path), sr=22050, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    # Normalize loudness-ish
    if np.max(np.abs(y)) > 0:
        y = y / np.max(np.abs(y))

    hop = 512
    frame_length = 2048

    # Pitch via pyin (reliable for monophonic vocals)
    f0, voiced_flag, _ = librosa.pyin(
        y,
        fmin=float(librosa.note_to_hz("C2")),
        fmax=float(librosa.note_to_hz("C6")),
        sr=sr,
        hop_length=hop,
    )
    frame_rate = sr / hop
    voiced = voiced_flag.astype(bool)
    voiced_ratio = float(voiced.mean()) if voiced.size else 0.0

    f0_valid = f0[voiced & ~np.isnan(f0)]
    if f0_valid.size:
        median_pitch = float(np.median(f0_valid))
        midi_vals = 69 + 12 * np.log2(f0_valid / 440.0)
        pitch_range_semitones = float(np.percentile(midi_vals, 95) - np.percentile(midi_vals, 5))
    else:
        median_pitch = 0.0
        pitch_range_semitones = 0.0

    cents_offsets = _hz_to_cents_from_nearest_semitone(f0_valid)
    if cents_offsets.size:
        pitch_stability = float(np.std(cents_offsets))
        in_tune_ratio = float(np.mean(np.abs(cents_offsets) < 35))
    else:
        pitch_stability = 0.0
        in_tune_ratio = 0.0

    vibrato_rate, vibrato_extent = _estimate_vibrato(f0, frame_rate)

    # Loudness
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop)[0]
    rms_db = librosa.amplitude_to_db(rms + 1e-6)
    loudness_mean = float(np.mean(rms_db))
    loudness_range = float(np.percentile(rms_db, 95) - np.percentile(rms_db, 5))
    dynamic_variation = float(np.std(rms_db))

    # Rhythm
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop)
    onsets = librosa.onset.onset_detect(y=y, sr=sr, hop_length=hop, units="time")

    # Silence / phrasing
    silence_threshold = loudness_mean - 15  # 15 dB below mean = quiet
    silent_frames = rms_db < silence_threshold
    silence_ratio = float(silent_frames.mean())
    longest_phrase = _longest_voiced_run(voiced, hop / sr)

    return VocalFeatures(
        duration_sec=float(duration),
        tempo_bpm=float(tempo),
        median_pitch_hz=median_pitch,
        pitch_range_semitones=pitch_range_semitones,
        pitch_stability_cents=pitch_stability,
        in_tune_ratio=in_tune_ratio,
        voiced_ratio=voiced_ratio,
        vibrato_rate_hz=float(vibrato_rate),
        vibrato_extent_cents=float(vibrato_extent),
        loudness_mean_db=loudness_mean,
        loudness_range_db=loudness_range,
        dynamic_variation=dynamic_variation,
        onset_count=int(onsets.size),
        onset_regularity=_onset_regularity(onsets),
        silence_ratio=silence_ratio,
        longest_phrase_sec=float(longest_phrase),
    )


def features_to_dict(features: VocalFeatures) -> dict:
    return asdict(features)
