import sys
import unittest
from pathlib import Path


DRIFT_WEB_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = DRIFT_WEB_ROOT.parents[0]
sys.path.insert(0, str(DRIFT_WEB_ROOT))

from parsers import (  # noqa: E402
    CHANNELS,
    extract_task_list,
    find_execution_plan,
    find_task_file,
    load_json_or_jsonl,
    load_optional_json,
    load_sibling_summary,
    normalize_task,
    parse_evidence_mix,
    validate_family,
)


class DriftWebBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.overrides = load_optional_json(DRIFT_WEB_ROOT / "family_overrides.json") or {}
        cls.c_root = PROJECT_ROOT / "data" / "C_drift_benchmark"
        cls.d_root = PROJECT_ROOT / "data" / "D_drift_benchmark"

    def test_c1_2_single_task_parsing(self):
        family_dir = self.c_root / "C1.2"
        task_file = find_task_file(family_dir)
        self.assertIsNotNone(task_file)
        self.assertEqual(task_file.name, "task.json")

        tasks = extract_task_list(load_json_or_jsonl(task_file))
        self.assertEqual(len(tasks), 1)
        normalized = normalize_task("C1.2", tasks[0], 1, task_file.relative_to(family_dir).as_posix(), self.overrides)
        self.assertEqual(normalized["id"], "C1.2_pilot_001")
        self.assertEqual(normalized["slice"], "unspecified")
        self.assertIn("START to X7", normalized["description"])

    def test_c2_1_sibling_ids_and_slices(self):
        family_dir = self.c_root / "C2.1"
        task_file = find_task_file(family_dir)
        tasks = extract_task_list(load_json_or_jsonl(task_file))
        normalized = [
            normalize_task("C2.1", task, ordinal, task_file.relative_to(family_dir).as_posix(), self.overrides)
            for ordinal, task in enumerate(tasks, start=1)
        ]
        self.assertEqual(len(normalized), 16)
        self.assertEqual(normalized[0]["id"], "C2.1_vehicle_001")
        self.assertEqual(normalized[0]["slice"], "affected-new-edge")
        self.assertTrue(all(task["id"] for task in normalized))

    def test_evidence_compositions(self):
        expected = {
            "C1.1": (self.c_root / "C1.1", {"D1": 0, "D2": 50, "D3": 50}),
            "C1.2": (self.c_root / "C1.2", {"D1": 100, "D2": 0, "D3": 0}),
            "C2.1": (self.c_root / "C2.1", {"D1": 0, "D2": 40, "D3": 60}),
            "C2.2": (self.c_root / "C2.2", {"D1": 0, "D2": 0, "D3": 100}),
            "C3.1": (self.c_root / "C3.1", {"D1": 50, "D2": 0, "D3": 50}),
            "D1.2": (self.d_root / "D1.2", {"D1": 0, "D2": 0, "D3": 100}),
            "D2.1": (self.d_root / "D2.1", {"D1": 30, "D2": 0, "D3": 70}),
            "D2.2": (self.d_root / "D2.2", {"D1": 0, "D2": 0, "D3": 100}),
        }
        for family_id, (family_dir, percentages) in expected.items():
            with self.subTest(family_id=family_id):
                evidence = parse_evidence_mix(
                    family_dir,
                    None,
                    load_sibling_summary(family_dir),
                    self.overrides,
                    family_id,
                )
                observed = {channel: evidence[channel]["percentage"] for channel in CHANNELS}
                self.assertEqual(observed, percentages)

    def test_plan_discovery(self):
        expected = {
            "C1.1": "C1_1_BFCL_execution_plan.md",
            "C1.2": "C1_2_BFCL_execution_plan.md",
            "C2.1": "C2_1_BFCL_execution_plan.md",
            "C2.2": "C2_2_BFCL_execution_plan.md",
            "C3.1": "C3_1_BFCL_execution_plan.md",
            "D1.2": "D1_2_design_level_drift_plan.md",
            "D2.1": "D2_1_design_level_drift_plan.md",
            "D2.2": "D2_2_design_level_drift_plan.md",
        }
        for family_id, filename in expected.items():
            root = self.c_root if family_id.startswith("C") else self.d_root
            with self.subTest(family_id=family_id):
                self.assertEqual(find_execution_plan(root / family_id).name, filename)

    def test_duplicate_ids_fail_validation(self):
        family = {
            "id": "C9.9",
            "task_count": 2,
            "plan": {"filename": "plan.md"},
            "tasks": [{"id": "duplicate"}, {"id": "duplicate"}],
            "evidence": {
                "D1": {"percentage": 100, "present": True, "delivery": "declared", "files": []},
                "D2": {"percentage": 0, "present": False, "delivery": None, "files": []},
                "D3": {"percentage": 0, "present": False, "delivery": None, "files": []},
            },
        }
        with self.assertRaises(ValueError):
            validate_family(family)


if __name__ == "__main__":
    unittest.main()
