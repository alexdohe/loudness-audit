import pytest

from loudness_audit.cli import render
from loudness_audit.core import Measurement, Target, check, parse_loudnorm

STDERR = """Input #0, wav ...
[Parsed_loudnorm_0 @ 0x55] 
{
	"input_i" : "-23.04",
	"input_tp" : "-5.20",
	"input_lra" : "1.30",
	"input_thresh" : "-33.10",
	"output_i" : "-24.00",
	"target_offset" : "0.00"
}
"""


def test_parse():
    assert parse_loudnorm(STDERR) == {"integrated": -23.04, "true_peak": -5.2, "lra": 1.3}


def test_parse_missing():
    with pytest.raises(ValueError):
        parse_loudnorm("nothing here")


def test_parse_silence_inf():
    out = parse_loudnorm(STDERR.replace('"-23.04"', '"-inf"'))
    assert out["integrated"] == float("-inf")


def test_check_pass_and_fail():
    t = Target.preset("ebu-r128")
    assert check(Measurement("a", -23.4, -2.0, 5), t) == []
    probs = check(Measurement("b", -14.0, -0.2, 5), t)
    assert len(probs) == 2


def test_lra_optional():
    t = Target(-23, 1, -1, max_lra=10)
    assert check(Measurement("a", -23, -3, 15), t)


def test_unknown_preset():
    with pytest.raises(ValueError):
        Target.preset("nope")


def test_render_formats():
    rows = [{"file": "a.wav", "integrated": -23.0, "true_peak": -3.0, "lra": 2.0, "status": "PASS", "problems": []}]
    assert "PASS" in render(rows, "table")
    assert render(rows, "csv").startswith("file,")
    assert '"status": "PASS"' in render(rows, "json")
