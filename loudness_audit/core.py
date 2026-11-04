from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass

PRESETS = {
    # name: (target integrated LUFS, tolerance LU, max true peak dBTP, max LRA LU or None)
    "ebu-r128": (-23.0, 1.0, -1.0, None),     # European broadcast
    "atsc-a85": (-24.0, 2.0, -2.0, None),     # US broadcast
    "streaming": (-14.0, 1.0, -1.0, None),    # typical music/video streaming
    "podcast": (-16.0, 1.0, -1.0, None),
}


@dataclass
class Target:
    integrated: float
    tolerance: float
    true_peak: float
    max_lra: float | None = None

    @classmethod
    def preset(cls, name: str) -> "Target":
        if name not in PRESETS:
            raise ValueError(f"unknown preset {name!r}; choose from {', '.join(PRESETS)}")
        return cls(*PRESETS[name])


@dataclass
class Measurement:
    file: str
    integrated: float
    true_peak: float
    lra: float


_JSON_BLOCK = re.compile(r"\{[^{}]*\"input_i\"[^{}]*\}", re.S)


def parse_loudnorm(stderr: str) -> dict[str, float]:
    """Pull the JSON block that `loudnorm=print_format=json` writes to stderr."""
    m = _JSON_BLOCK.search(stderr)
    if not m:
        raise ValueError("no loudnorm JSON found in ffmpeg output")
    raw = json.loads(m.group(0))

    # float() accepts "-inf", which ffmpeg reports for digital silence
    return {"integrated": float(raw["input_i"]), "true_peak": float(raw["input_tp"]),
            "lra": float(raw["input_lra"])}


def measure(path: str, ffmpeg: str = "ffmpeg") -> Measurement:
    cmd = [ffmpeg, "-hide_banner", "-nostats", "-i", path,
           "-af", "loudnorm=print_format=json", "-vn", "-f", "null", "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed on {path}: {proc.stderr.strip()[-300:]}")
    return Measurement(path, **parse_loudnorm(proc.stderr))


def check(m: Measurement, t: Target) -> list[str]:
    """Return a list of problems; empty means pass."""
    problems = []
    if abs(m.integrated - t.integrated) > t.tolerance:
        problems.append(f"integrated {m.integrated:.1f} LUFS outside {t.integrated:.1f}±{t.tolerance:g}")
    if m.true_peak > t.true_peak:
        problems.append(f"true peak {m.true_peak:.1f} dBTP above {t.true_peak:.1f}")
    if t.max_lra is not None and m.lra > t.max_lra:
        problems.append(f"LRA {m.lra:.1f} LU above {t.max_lra:.1f}")
    return problems
