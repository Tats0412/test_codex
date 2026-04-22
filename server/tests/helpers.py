from pathlib import Path

import numpy as np
import soundfile as sf


def write_tone(
    path: Path,
    freq_hz: float = 440.0,
    duration_sec: float = 3.0,
    sr: int = 22050,
    vibrato_hz: float = 0.0,
    vibrato_cents: float = 0.0,
) -> Path:
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
    if vibrato_hz > 0 and vibrato_cents > 0:
        semis = (vibrato_cents / 100.0) * np.sin(2 * np.pi * vibrato_hz * t)
        inst_freq = freq_hz * (2 ** (semis / 12.0))
        phase = 2 * np.pi * np.cumsum(inst_freq) / sr
        y = 0.3 * np.sin(phase)
    else:
        y = 0.3 * np.sin(2 * np.pi * freq_hz * t)
    # Apply short fade to avoid clicks
    n_fade = int(0.02 * sr)
    env = np.ones_like(y)
    env[:n_fade] = np.linspace(0, 1, n_fade)
    env[-n_fade:] = np.linspace(1, 0, n_fade)
    y = (y * env).astype(np.float32)
    sf.write(str(path), y, sr)
    return path
