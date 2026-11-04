# loudness-audit

A small CLI that checks audio/video files against loudness delivery specs (EBU R128, ATSC A/85, streaming, podcast). It measures **integrated loudness**, **true peak** and **loudness range (LRA)** with ffmpeg's `loudnorm` filter and fails with a non-zero exit code if any file is out of spec, so it drops straight into CI or a render pipeline.

## Why

Broadcasters reject deliveries that miss loudness specs, and platforms turn loud masters down. Checking by ear or by eye on a meter doesn't scale across a batch. This makes the check automatic and repeatable.

- Uses ffmpeg's standard EBU R128 measurement, so numbers match what QC will see.
- Presets for common targets, every value overridable from the command line.
- Table for humans, CSV/JSON for spreadsheets and pipelines.
- Exit code `0` = all pass, `1` = any failure or unreadable file.

## Quickstart

Requires Python 3.10+ and ffmpeg on your PATH. No other dependencies.

```bash
python -m loudness_audit master.mov                      # EBU R128: -23 LUFS ±1, ≤ -1 dBTP
python -m loudness_audit *.mp4 --preset streaming        # -14 LUFS
python -m loudness_audit ep01.wav --target -16 --max-true-peak -1.5 --format csv > report.csv
```

| Preset    | Integrated | Tolerance | True peak |
|-----------|-----------:|----------:|----------:|
| ebu-r128  | -23 LUFS   | ±1 LU     | -1 dBTP   |
| atsc-a85  | -24 LKFS   | ±2 LU     | -2 dBTP   |
| streaming | -14 LUFS   | ±1 LU     | -1 dBTP   |
| podcast   | -16 LUFS   | ±1 LU     | -1 dBTP   |

Add `--max-lra 15` (or similar) if your spec limits loudness range. Always check your actual delivery spec, as broadcasters vary.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Unit tests cover parsing ffmpeg's output (including `-inf` for silence), pass/fail rules and report formats. An integration test generates a test tone with ffmpeg and measures it; it is skipped automatically if ffmpeg isn't installed.

## Licence

MIT
