from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from account_service_r_plus import AccountServiceRPlus  # noqa: E402


class MeteredD3Probe:
    """Learner-visible probe surface for current-regime identity checks."""

    def __init__(self) -> None:
        self.service = AccountServiceRPlus()
        self.cost = 0
        self.log: list[dict[str, Any]] = []

    def run(self, action: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        state_before = dict(self.service.state)
        response = self.service.run_action(
            {"action": action, "arguments": arguments or {}}
        )
        self.cost += 1
        record = {
            "probe_id": f"B10.1-d3-live-{self.cost:03d}",
            "rule_id": "E02",
            "state_before": state_before,
            "action": action,
            "arguments": arguments or {},
            "response": response,
            "state_after": dict(self.service.state),
            "cost": self.cost,
        }
        self.log.append(record)
        return response


def demo_sequence() -> list[dict[str, Any]]:
    probe = MeteredD3Probe()
    probe.run("issue_account_credit", {"amount": 40, "reason": "goodwill"})
    probe.run("verify_identity")
    probe.run("issue_account_credit", {"amount": 40, "reason": "goodwill"})
    return probe.log


if __name__ == "__main__":
    for entry in demo_sequence():
        print(entry)
