"""Compare a user's vocal recording against a reference recording.

Workflow:
  1. Load both audio files at the same sample rate.
  2. Extract chroma features and DTW-align the two recordings on a shared
     time grid (handles tempo differences).
  3. Extract pitch (f0) contours for both.
  4. Auto-detect the semitone offset between the two (user may sing in a
     different key) and transpose the reference before comparison.
  5. Along the aligned timeline, compute per-frame cents deviation, then
     collapse into contiguous "problem segments" for the model to comment on.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import librosa
import numpy as np


@dataclass
class ComparisonReport:
    key_offset_semitones: int          # detected user-vs-reference transposition
    timing_offset_sec: float           # positive = user late, negative = early
    avg_abs_cents_off: float           # mean |cents deviation| across voiced frames
    pitch_match_ratio: float           # fraction of voiced frames within 35 cents
    problem_segments: list[dict]       # [{start_sec,end_sec,avg_cents,kind}]


def _load(path: str | Path, sr: int = 22050) -> np.ndarray:
    y, _ = librosa.load(str(path), sr=sr, mono=True)
    if np.max(np.abs(y)) > 0:
        y = y / np.max(np.abs(y))
    return y


def _pitch_contour(y: np.ndarray, sr: int, hop: int) -> np.ndarray:
    f0, voiced_flag, _ = librosa.pyin(
        y,
        fmin=float(librosa.note_to_hz("C2")),
        fmax=float(librosa.note_to_hz("C6")),
        sr=sr,
        hop_length=hop,
    )
    out = np.where(voiced_flag & ~np.isnan(f0), f0, np.nan)
    return out


def _detect_semitone_offset(user_f0: np.ndarray, ref_f0: np.ndarray) -> int:
    """Return integer semitone offset to transpose `ref` so it matches `user`."""
    u = user_f0[~np.isnan(user_f0)]
    r = ref_f0[~np.isnan(ref_f0)]
    if u.size == 0 or r.size == 0:
        return 0
    u_midi = np.median(69 + 12 * np.log2(u / 440.0))
    r_midi = np.median(69 + 12 * np.log2(r / 440.0))
    return int(round(u_midi - r_midi))


def _align_chroma(user: np.ndarray, ref: np.ndarray, sr: int, hop: int):
    """DTW-align two recordings by chroma. Returns index arrays into each frame axis."""
    user_chroma = librosa.feature.chroma_cqt(y=user, sr=sr, hop_length=hop)
    ref_chroma = librosa.feature.chroma_cqt(y=ref, sr=sr, hop_length=hop)
    _, wp = librosa.sequence.dtw(X=ref_chroma, Y=user_chroma, metric="cosine")
    # wp is (N, 2) array of (ref_idx, user_idx) pairs, ordered end->start.
    wp = wp[::-1]
    return wp[:, 0], wp[:, 1]


def _segments_from_mask(
    mask: np.ndarray,
    cents: np.ndarray,
    times: np.ndarray,
    min_len_sec: float = 0.4,
    max_segments: int = 6,
) -> list[dict]:
    segs = []
    n = len(mask)
    i = 0
    while i < n:
        if not mask[i]:
            i += 1
            continue
        j = i
        while j < n and mask[j]:
            j += 1
        start = float(times[i])
        end = float(times[j - 1])
        if end - start >= min_len_sec:
            chunk = cents[i:j]
            chunk = chunk[~np.isnan(chunk)]
            if chunk.size:
                avg = float(np.mean(chunk))
                segs.append(
                    {
                        "start_sec": round(start, 2),
                        "end_sec": round(end, 2),
                        "avg_cents": round(avg, 1),
                        "kind": "sharp" if avg > 0 else "flat",
                    }
                )
        i = j

    # Keep the most severe segments
    segs.sort(key=lambda s: abs(s["avg_cents"]), reverse=True)
    return segs[:max_segments]


def compare_to_reference(
    user_path: str | Path,
    reference_path: str | Path,
    sr: int = 22050,
    hop: int = 512,
) -> ComparisonReport:
    user_y = _load(user_path, sr)
    ref_y = _load(reference_path, sr)

    user_f0 = _pitch_contour(user_y, sr, hop)
    ref_f0 = _pitch_contour(ref_y, sr, hop)

    # Auto-transpose reference to user's key
    offset = _detect_semitone_offset(user_f0, ref_f0)
    ref_f0_shifted = ref_f0 * (2 ** (offset / 12.0))

    # DTW alignment on chroma (handles tempo differences)
    ref_idx, user_idx = _align_chroma(user_y, ref_y, sr, hop)

    # Global timing offset estimate: compare median alignment slope
    frame_rate = sr / hop
    # Average time difference between corresponding frames (user_time - ref_time)
    timing_offset_sec = float(np.median((user_idx - ref_idx) / frame_rate))

    # Per-aligned-frame cents error (user vs shifted ref)
    ref_at_user = np.full_like(user_f0, np.nan)
    for r_i, u_i in zip(ref_idx, user_idx):
        if u_i < len(user_f0) and r_i < len(ref_f0_shifted):
            # Keep the first mapping; DTW can map many-to-one
            if np.isnan(ref_at_user[u_i]):
                ref_at_user[u_i] = ref_f0_shifted[r_i]

    both_voiced = ~np.isnan(user_f0) & ~np.isnan(ref_at_user)
    cents = np.full_like(user_f0, np.nan)
    cents[both_voiced] = 1200.0 * np.log2(
        user_f0[both_voiced] / ref_at_user[both_voiced]
    )

    valid = cents[~np.isnan(cents)]
    if valid.size:
        avg_abs = float(np.mean(np.abs(valid)))
        match_ratio = float(np.mean(np.abs(valid) < 35))
    else:
        avg_abs = 0.0
        match_ratio = 0.0

    # Problem segments: contiguous frames where |cents| > 50
    times = np.arange(len(cents)) / frame_rate
    bad_mask = np.abs(cents) > 50
    bad_mask[np.isnan(cents)] = False
    segments = _segments_from_mask(bad_mask, cents, times)

    return ComparisonReport(
        key_offset_semitones=offset,
        timing_offset_sec=round(timing_offset_sec, 3),
        avg_abs_cents_off=round(avg_abs, 1),
        pitch_match_ratio=round(match_ratio, 3),
        problem_segments=segments,
    )


def report_to_dict(r: ComparisonReport) -> dict:
    return asdict(r)
