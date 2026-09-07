#!/usr/bin/env python
"""Compile D3.2 sibling traces into package-level regime answers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent


def load_manifest() -> dict:
    return json.loads((PACKAGE_ROOT / "siblings.json").read_text())


def compile_answers(manifest: dict, regime: str) -> dict:
    tasks = []
    for task in manifest["tasks"]:
        tasks.append(
            {
                "id": task["id"],
                "slice": task["slice"],
                "affected": task["affected"],
                "answer": {
                    "actions": task[f"{regime}_ground_truth"],
                    "optimal_cost": task[f"{regime}_optimal_cost"],
                    "expected_final_state": task["expected_final_state"],
                },
            }
        )
    return {
        "benchmark_id": manifest["benchmark_id"],
        "family": manifest["family"],
        "regime": regime,
        "task_file": "siblings.json",
        "tasks": tasks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Write possible_answer files.")
    args = parser.parse_args()

    manifest = load_manifest()
    outputs = {
        "possible_answer_r_minus.json": compile_answers(manifest, "r_minus"),
        "possible_answer_r_plus.json": compile_answers(manifest, "r_plus"),
    }

    if args.write:
        for filename, payload in outputs.items():
            (PACKAGE_ROOT / filename).write_text(json.dumps(payload, indent=2) + "\n")
    else:
        print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
