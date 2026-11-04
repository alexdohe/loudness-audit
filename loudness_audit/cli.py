from __future__ import annotations

import argparse
import csv
import io
import json
import sys

from .core import PRESETS, Target, check, measure

FIELDS = ["file", "integrated", "true_peak", "lra", "status", "problems"]


def render(rows, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(rows, indent=2)
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=FIELDS)
        w.writeheader()
        w.writerows({**r, "problems": "; ".join(r["problems"])} for r in rows)
        return buf.getvalue()
    lines = [f"{'FILE':40} {'LUFS':>7} {'TP':>6} {'LRA':>5}  STATUS"]
    for r in rows:
        lines.append(f"{r['file'][-40:]:40} {r['integrated']:7.1f} {r['true_peak']:6.1f} "
                     f"{r['lra']:5.1f}  {r['status']}" + (f"  ({'; '.join(r['problems'])})" if r["problems"] else ""))
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="loudness-audit", description="Check files against loudness targets.")
    p.add_argument("files", nargs="+")
    p.add_argument("--preset", default="ebu-r128", choices=sorted(PRESETS))
    p.add_argument("--target", type=float, help="override integrated target (LUFS)")
    p.add_argument("--tolerance", type=float, help="override tolerance (LU)")
    p.add_argument("--max-true-peak", type=float, help="override true peak ceiling (dBTP)")
    p.add_argument("--max-lra", type=float, help="optional loudness range ceiling (LU)")
    p.add_argument("--format", default="table", choices=["table", "csv", "json"])
    p.add_argument("--ffmpeg", default="ffmpeg")
    a = p.parse_args(argv)

    t = Target.preset(a.preset)
    for attr, val in (("integrated", a.target), ("tolerance", a.tolerance),
                      ("true_peak", a.max_true_peak), ("max_lra", a.max_lra)):
        if val is not None:
            setattr(t, attr, val)

    rows, failed = [], 0
    for f in a.files:
        try:
            m = measure(f, a.ffmpeg)
        except (RuntimeError, ValueError) as e:
            print(f"error: {e}", file=sys.stderr)
            failed += 1
            continue
        problems = check(m, t)
        failed += bool(problems)
        rows.append({"file": f, "integrated": m.integrated, "true_peak": m.true_peak,
                     "lra": m.lra, "status": "FAIL" if problems else "PASS", "problems": problems})
    print(render(rows, a.format))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
