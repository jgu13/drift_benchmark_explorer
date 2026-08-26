"""D3 interaction wrapper for the C2.2 r+ regime."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, Mapping

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG_PATH = Path(__file__).with_name("interaction_log.jsonl")

ALLOWED_ACTIONS = {
    "activateParkingBrake",
    "displayCarStatus",
    "fillFuelTank",
    "lockDoors",
    "pressBrakePedal",
    "releaseBrakePedal",
    "setCruiseControl",
    "startEngine",
}


def _load_r_plus_backend():
    backend_path = PACKAGE_ROOT / "vehicle_control_c2_r_plus.py"
    spec = importlib.util.spec_from_file_location("vehicle_control_c2_r_plus", backend_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load backend from {backend_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _unwrap_initial_state(initial_state: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not initial_state:
        return {}
    if "VehicleControlAPI" in initial_state:
        return dict(initial_state["VehicleControlAPI"])
    return dict(initial_state)


class D3Session:
    """Safe execution session that logs each r+ interaction."""

    def __init__(
        self,
        task_id: str,
        initial_state: Mapping[str, Any] | None = None,
        log_path: str | Path | None = None,
    ) -> None:
        backend = _load_r_plus_backend()
        self.task_id = task_id
        self.api = backend.load_api(_unwrap_initial_state(initial_state))
        self.cost = 0
        self.log_path = Path(log_path) if log_path is not None else DEFAULT_LOG_PATH

    def state_snapshot(self) -> Dict[str, Any]:
        return {
            "fuelLevel": self.api.fuelLevel,
            "batteryVoltage": self.api.batteryVoltage,
            "engineState": self.api.engine_state,
            "remainingUnlockedDoors": self.api.remainingUnlockedDoors,
            "doorStatus": dict(self.api.doorStatus),
            "parkingBrakeStatus": self.api.parkingBrakeStatus,
            "parkingBrakeForce": self.api._parkingBrakeForce,
            "brakePedalStatus": self.api.brakePedalStatus,
            "brakePedalForce": self.api._brakePedalForce,
            "distanceToNextVehicle": self.api.distanceToNextVehicle,
            "cruiseStatus": self.api.cruiseStatus,
        }

    def execute(self, action: str, arguments: Mapping[str, Any] | None = None) -> Dict[str, Any]:
        if action not in ALLOWED_ACTIONS:
            raise ValueError(f"Action {action!r} is not available for C2.2 D3 interaction")

        arguments = dict(arguments or {})
        state_before = self.state_snapshot()
        response = getattr(self.api, action)(**arguments)
        state_after = self.state_snapshot()
        self.cost += 1

        entry = {
            "task_id": self.task_id,
            "state_before": state_before,
            "action": action,
            "arguments": arguments,
            "response": response,
            "state_after": state_after,
            "cost": self.cost,
        }
        self._append_log(entry)
        return response

    def _append_log(self, entry: Mapping[str, Any]) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")


def execute(
    action: str,
    arguments: Mapping[str, Any] | None = None,
    task_id: str = "ad_hoc",
    initial_state: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """One-shot execution helper for ad hoc probes."""

    session = D3Session(task_id=task_id, initial_state=initial_state)
    return session.execute(action, arguments)


if __name__ == "__main__":
    demo = D3Session(
        task_id="demo",
        initial_state={
            "fuelLevel": 10.0,
            "engineState": "stopped",
            "doorStatus": {
                "driver": "locked",
                "passenger": "locked",
                "rear_left": "locked",
                "rear_right": "locked",
            },
            "parkingBrakeStatus": "released",
            "brakePedalStatus": "pressed",
            "brakePedalForce": 1000.0,
        },
    )
    print(demo.execute("startEngine", {"ignitionMode": "START"}))
