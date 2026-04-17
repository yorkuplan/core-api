#!/usr/bin/env python3
"""Flag course objects that have no courseId and no section data (scraping stubs)."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def is_stub(c: dict) -> bool:
    cid = (c.get("courseId") or "").strip()
    if cid:
        return False
    secs = c.get("sections") or []
    if secs:
        return False
    cred = (c.get("credits") or "").strip()
    loi = (c.get("languageOfInstruction") or "").strip()
    if cred or loi:
        return False
    return True


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "data_dir",
        nargs="?",
        default="scraping/data/fall-winter-2026-2027",
        help="Directory of *.json faculty exports (default: 2026-2027)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Print one JSON array of stub records to stdout",
    )
    p.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        help="Write full stub list as JSON to PATH (UTF-8)",
    )
    p.add_argument(
        "--csv",
        metavar="PATH",
        help="Write stub list as CSV to PATH",
    )
    args = p.parse_args()

    root = Path(__file__).resolve().parents[1]
    d = (root / args.data_dir).resolve()
    if not d.is_dir():
        print(f"Not a directory: {d}", file=sys.stderr)
        return 1

    stubs: list[dict] = []
    for path in sorted(d.glob("*.json")):
        if path.name in {"duplicates.json"}:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"Skip {path.name}: {e}", file=sys.stderr)
            continue
        if not isinstance(data, dict) or "courses" not in data:
            continue
        for i, c in enumerate(data["courses"]):
            if not isinstance(c, dict):
                continue
            if is_stub(c):
                fac = c.get("faculty") or ""
                dept = c.get("department") or ""
                term = c.get("term") or ""
                title = c.get("courseTitle") or ""
                stubs.append(
                    {
                        "file": path.name,
                        "index": i,
                        "faculty": fac,
                        "department": dept,
                        "term": term,
                        "courseTitle": title[:500],
                        "lookup_hint": f"{fac}/{dept} — {term} — {title[:200]}",
                    }
                )

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(stubs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {len(stubs)} stubs to {out}", file=sys.stderr)

    if args.csv:
        csv_path = Path(args.csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "file",
                    "index",
                    "faculty",
                    "department",
                    "term",
                    "courseTitle",
                    "lookup_hint",
                ],
            )
            w.writeheader()
            w.writerows(stubs)
        print(f"Wrote {len(stubs)} rows to {csv_path}", file=sys.stderr)

    if args.json:
        print(json.dumps(stubs, indent=2, ensure_ascii=False))
        return 0

    if args.output or args.csv:
        return 0

    print(f"Stub courses (empty courseId, no sections, no credits/LOI): {len(stubs)}")
    by_dept: dict[str, int] = {}
    for s in stubs:
        dept = s.get("department") or "?"
        by_dept[dept] = by_dept.get(dept, 0) + 1
    for dept, n in sorted(by_dept.items(), key=lambda x: -x[1])[:25]:
        print(f"  {dept}: {n}")
    if len(by_dept) > 25:
        print(f"  ... +{len(by_dept) - 25} more departments")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
