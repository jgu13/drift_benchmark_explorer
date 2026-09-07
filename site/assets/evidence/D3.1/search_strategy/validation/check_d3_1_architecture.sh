#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FAMILY_ROOT="$(cd "${PACKAGE_ROOT}/.." && pwd)"

required_files=(
  "${FAMILY_ROOT}/D3_1_search_strategy_execution_plan.md"
  "${PACKAGE_ROOT}/README.md"
  "${PACKAGE_ROOT}/compile_d3_1.py"
  "${PACKAGE_ROOT}/drift_spec.json"
  "${PACKAGE_ROOT}/source_task.json"
  "${PACKAGE_ROOT}/siblings.json"
  "${PACKAGE_ROOT}/sibling_summary.json"
  "${PACKAGE_ROOT}/possible_answer_r_minus.json"
  "${PACKAGE_ROOT}/possible_answer_r_plus.json"
  "${PACKAGE_ROOT}/regime_r_minus.json"
  "${PACKAGE_ROOT}/regime_r_plus.json"
  "${PACKAGE_ROOT}/regime_null.json"
  "${PACKAGE_ROOT}/layout_r_minus.json"
  "${PACKAGE_ROOT}/layout_r_plus.json"
  "${PACKAGE_ROOT}/search_prior_r_minus.json"
  "${PACKAGE_ROOT}/search_prior_r_plus.json"
  "${PACKAGE_ROOT}/searchworld_simulator.py"
  "${PACKAGE_ROOT}/skill_r_minus.md"
  "${PACKAGE_ROOT}/skill_r_plus_oracle.md"
  "${PACKAGE_ROOT}/evidence/evidence_allocation.json"
  "${PACKAGE_ROOT}/evidence/d3_probe_log.jsonl"
  "${SCRIPT_DIR}/construction_report.json"
  "${SCRIPT_DIR}/replay_checks.py"
)

for file in "${required_files[@]}"; do
  [[ -f "${file}" ]] || { echo "missing required file: ${file}" >&2; exit 1; }
done

python - "$PACKAGE_ROOT" <<'PY'
import json
import pathlib
import sys
from collections import Counter

root = pathlib.Path(sys.argv[1])
json_files = [
    "drift_spec.json",
    "source_task.json",
    "siblings.json",
    "sibling_summary.json",
    "possible_answer_r_minus.json",
    "possible_answer_r_plus.json",
    "regime_r_minus.json",
    "regime_r_plus.json",
    "regime_null.json",
    "layout_r_minus.json",
    "layout_r_plus.json",
    "search_prior_r_minus.json",
    "search_prior_r_plus.json",
    "evidence/evidence_allocation.json",
    "validation/construction_report.json",
]
for rel in json_files:
    json.loads((root / rel).read_text())

manifest = json.loads((root / "siblings.json").read_text())
tasks = manifest.get("tasks")
assert isinstance(tasks, list), "siblings.json must contain a tasks array"
assert len(tasks) == 19, f"expected 19 tasks, found {len(tasks)}"
assert manifest["composition"] == {
    "total": 19,
    "affected": 8,
    "unchanged-retention": 4,
    "boundary/open-set": 4,
    "matched-null": 3,
}, "manifest composition mismatch"
assert dict(Counter(t["slice"] for t in tasks)) == {
    "affected": 8,
    "unchanged-retention": 4,
    "boundary/open-set": 4,
    "matched-null": 3,
}, "slice count mismatch"
assert all(t["id"].startswith("D3.1_") for t in tasks), "task IDs must be D3.1_ prefixed"
assert sum(1 for t in tasks if t["affected"]) == 8, "affected boolean count mismatch"

allocation = json.loads((root / "evidence/evidence_allocation.json").read_text())
assert allocation["allocation"] == {"D1": 0, "D2": 0, "D3": 100}, "D3-only allocation mismatch"

evidence_files = [p.name for p in (root / "evidence").iterdir() if p.is_file()]
assert "d3_probe_log.jsonl" in evidence_files, "missing D3 probe log"
assert all(name.startswith(("d1", "d2", "d3", "evidence_allocation")) for name in evidence_files), (
    f"evidence filename without D-level prefix: {evidence_files}"
)
assert not (root / "evidence/skill_r_plus_oracle.md").exists(), "oracle skill leaked into evidence"

for rel, regime in [
    ("possible_answer_r_minus.json", "r_minus"),
    ("possible_answer_r_plus.json", "r_plus"),
]:
    answers = json.loads((root / rel).read_text())
    assert answers["regime"] == regime, f"{rel} wrong regime"
    assert {t["id"] for t in answers["tasks"]} == {t["id"] for t in tasks}, f"{rel} coverage mismatch"

with (root / "evidence/d3_probe_log.jsonl").open() as fh:
    probe_rows = [json.loads(line) for line in fh if line.strip()]
assert {row["rule_id"] for row in probe_rows} == {"S1", "S2"}, "D3 probes must cover S1 and S2"
for row in probe_rows:
    for field in ["probe_id", "rule_id", "state_before", "action", "arguments", "response", "state_after", "cost"]:
        assert field in row, f"probe row missing {field}"
    assert isinstance(row["cost"], int) and row["cost"] >= 0, "probe cost must be non-negative integer"
PY

python "${PACKAGE_ROOT}/compile_d3_1.py" --write
python "${SCRIPT_DIR}/replay_checks.py"

echo "D3.1 architecture checks passed"
