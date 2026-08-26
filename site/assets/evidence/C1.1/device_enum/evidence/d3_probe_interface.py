from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import sys

BFCL_ROOT = Path(__file__).resolve().parents[5]
DEVICE_ENUM_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BFCL_ROOT))
sys.path.insert(0, str(DEVICE_ENUM_ROOT))

from vehicle_control_r_plus import VehicleControlAPI  # noqa: E402

SAFE_PROBE_FUNCTIONS = {
    "setHeadlights": {"mode"},
    "adjustClimateControl": {"temperature", "unit", "fanSpeed", "mode"},
}
MAX_PROBES = 8


class ProbeMeter:
    def __init__(self, max_probes: int = MAX_PROBES):
        self.max_probes = max_probes
        self.count = 0
        self.log = []

    def probe(self, action: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if self.count >= self.max_probes:
            return {"error": "Probe budget exhausted."}
        if action not in SAFE_PROBE_FUNCTIONS:
            return {"error": "Unsafe or unsupported probe action."}
        unexpected = set(arguments) - SAFE_PROBE_FUNCTIONS[action]
        if unexpected:
            return {"error": f"Unsupported probe arguments: {sorted(unexpected)}"}

        self.count += 1
        api = VehicleControlAPI()
        api._load_scenario({})
        result = getattr(api, action)(**arguments)
        self.log.append({"probe_index": self.count, "action": action, "arguments": arguments, "outcome": result})
        return result


_meter = ProbeMeter()


def probe(action: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    return _meter.probe(action, arguments)
