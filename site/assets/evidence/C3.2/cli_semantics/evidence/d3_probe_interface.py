import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from gorilla_filesystem import GorillaCLI


PROBE_STATES = {
    "R2": {"files": {"summary.txt": "one\ntwo\nthree"}, "dirs": ["."]},
    "R3": {"files": {"summary.txt": "one\ntwo\nthree"}, "dirs": [".", "archives"]},
}


def run_probe(command, rule_id, log_path=None):
    state = PROBE_STATES[rule_id]
    cli = GorillaCLI("r_plus", state)
    state_before = cli.fs.snapshot()
    result = cli.run(command)
    record = {
        "rule_id": rule_id,
        "state_before": state_before,
        "action": command,
        "response": {
            "exit_code": result["exit_code"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
        },
        "state_after": result["state"],
        "cost": result["cost"],
    }
    if log_path:
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: d3_probe_interface.py <R2|R3> <command>")
    print(json.dumps(run_probe(sys.argv[2], sys.argv[1]), indent=2, sort_keys=True))
