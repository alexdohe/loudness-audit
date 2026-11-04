import shutil
import subprocess

import pytest

from loudness_audit.cli import main
from loudness_audit.core import measure

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


@pytest.fixture
def tone(tmp_path):
    path = tmp_path / "tone.wav"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                    "-i", "sine=frequency=1000:duration=5:sample_rate=48000",
                    str(path)], check=True)
    return str(path)


def test_measure_tone(tone):
    m = measure(tone)
    assert -30 < m.integrated < -10  # lavfi sine peaks at about -18 dBFS
    assert m.true_peak < 0


def test_cli_exit_code(tone, tmp_path):
    m = measure(tone)
    assert main([tone, "--target", str(m.integrated), "--format", "json"]) == 0
    assert main([tone, "--preset", "streaming", "--tolerance", "0.1"]) == 1
    assert main([str(tmp_path / "missing.wav")]) == 1
