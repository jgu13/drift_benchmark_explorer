"""Normalization helpers for the drift benchmark web explorer.

The frontend consumes one stable schema. This module absorbs the benchmark
families' on-disk format differences so new siblings can be added without
editing browser code.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


FAMILY_RE = re.compile(r"^[A-D][0-9]+\.[0-9]+$")
CHANNELS = ("D1", "D2", "D3")
TASK_FILE_NAMES = ("siblings.json", "siblings.jsonl", "task.json")
SLICE_LIKE_PREFIXES = (
    "affected",
    "unchanged",
    "boundary",
    "matched-null",
    "retention",
    "propagated",
)
HIDDEN_DETAIL_KEYS = {
    "gold_r_plus",
    "skill_r_plus_oracle",
    "oracle_r_plus_design_route",
    "oracle_r_plus_route",
    "possible_answer_r_plus",
    "hidden_graph_truth",
    "graph_truth_r_plus",
}


def natural_family_key(family_id: str) -> tuple[str, int, int]:
    match = re.match(r"^([A-D])([0-9]+)\.([0-9]+)$", family_id)
    if not match:
        return (family_id, 0, 0)
    prefix, major, minor = match.groups()
    return (prefix, int(major), int(minor))


def discover_family_dirs(roots: list[Path]) -> list[Path]:
    family_dirs: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for candidate in root.rglob("*"):
            if candidate.is_dir() and FAMILY_RE.match(candidate.name):
                resolved = candidate.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    family_dirs.append(candidate)
    return sorted(family_dirs, key=lambda path: natural_family_key(path.name))


def find_execution_plan(family_dir: Path) -> Path | None:
    patterns = ("*_execution_plan.md", "*execution*plan*.md", "*plan*.md")
    for pattern in patterns:
        matches = sorted(
            (path for path in family_dir.rglob(pattern) if path.is_file()),
            key=lambda path: (len(path.relative_to(family_dir).parts), path.name.lower()),
        )
        if matches:
            return matches[0]
    return None


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_optional_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return read_json(path)
    except json.JSONDecodeError:
        return None


def load_json_or_jsonl(path: Path) -> Any:
    if path.suffix == ".jsonl":
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
        return rows
    return read_json(path)


def find_task_file(family_dir: Path) -> Path | None:
    summaries = sorted(family_dir.rglob("sibling_summary.json"))
    for summary_path in summaries:
        summary = load_optional_json(summary_path)
        sibling_file = summary.get("sibling_file") if isinstance(summary, dict) else None
        if sibling_file:
            exact = summary_path.parent / sibling_file
            if exact.exists():
                return exact
            matches = sorted(family_dir.rglob(sibling_file))
            if matches:
                return matches[0]

    for name in TASK_FILE_NAMES:
        matches = sorted(
            (path for path in family_dir.rglob(name) if path.is_file()),
            key=lambda path: (len(path.relative_to(family_dir).parts), path.name.lower()),
        )
        if matches:
            return matches[0]
    return None


def extract_task_list(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [task for task in raw if isinstance(task, dict)]
    if isinstance(raw, dict):
        for key in ("siblings", "tasks", "task"):
            value = raw.get(key)
            if isinstance(value, list):
                return [task for task in value if isinstance(task, dict)]
            if isinstance(value, dict):
                return [value]
        if any(key in raw for key in ("id", "task_id", "instance_id", "name", "question", "instruction")):
            return [raw]
    return []


def extract_task_id(task: dict[str, Any], family_id: str, ordinal: int) -> str:
    for key in ("id", "task_id", "instance_id", "name"):
        value = task.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return f"{family_id}_task_{ordinal:03d}"


def normalize_slice(value: Any) -> str:
    if value is None or not str(value).strip():
        return "unspecified"
    normalized = str(value).strip().replace("_", "-").replace("/", "-")
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    aliases = {
        "boundary": "boundary-open-set",
        "boundary-open": "boundary-open-set",
        "open-set": "boundary-open-set",
        "unchanged": "unchanged-retention",
        "retention": "unchanged-retention",
        "matched-null": "matched-null",
    }
    return aliases.get(normalized, normalized)


def looks_like_slice(value: Any) -> bool:
    if value is None or not str(value).strip():
        return False
    normalized = normalize_slice(value)
    return any(normalized == prefix or normalized.startswith(f"{prefix}-") for prefix in SLICE_LIKE_PREFIXES)


def extract_task_slice(task: dict[str, Any]) -> str:
    category = task.get("category") or task.get("task_category")
    slice_value = task.get("slice") or task.get("affectedness") or task.get("group")
    if looks_like_slice(category):
        return normalize_slice(category)
    if slice_value is not None and str(slice_value).strip():
        return normalize_slice(slice_value)
    if category is not None and str(category).strip():
        return normalize_slice(category)
    return "unspecified"


def extract_instruction(task: dict[str, Any]) -> str | None:
    for key in ("instruction", "prompt", "user_prompt", "question"):
        value = task.get(key)
        text = extract_text(value)
        if text:
            return text
    return None


def extract_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return " ".join(value.split())
    if isinstance(value, dict):
        for key in ("content", "text", "question", "instruction"):
            if key in value:
                text = extract_text(value[key])
                if text:
                    return text
        parts = [extract_text(item) for item in value.values()]
        joined = " ".join(part for part in parts if part)
        return " ".join(joined.split()) or None
    if isinstance(value, list):
        parts = [extract_text(item) for item in value]
        joined = " ".join(part for part in parts if part)
        return " ".join(joined.split()) or None
    return str(value)


def trim_text(text: str, max_chars: int = 150) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip() + "..."


def make_task_description(
    family_id: str,
    task: dict[str, Any],
    slice_name: str,
    overrides: dict[str, Any],
) -> str:
    for key in ("ui_description", "description", "drift_description", "summary"):
        text = extract_text(task.get(key))
        if text:
            return trim_text(text)

    family_overrides = overrides.get(family_id, {})
    templates = family_overrides.get("task_descriptions", {})
    for key in (slice_name, normalize_slice(task.get("slice")), normalize_slice(task.get("category"))):
        if key in templates:
            return templates[key]

    instruction = extract_instruction(task)
    if instruction:
        return trim_text(instruction)
    return "No description available."


def find_drift_spec(family_dir: Path) -> dict[str, Any] | None:
    matches = sorted(family_dir.rglob("drift_spec.json"))
    if not matches:
        return None
    return load_optional_json(matches[0])


def find_evidence_allocation(family_dir: Path) -> tuple[Path | None, dict[str, Any] | None]:
    matches = sorted(family_dir.rglob("evidence_allocation.json"))
    if not matches:
        return None, None
    path = matches[0]
    data = load_optional_json(path)
    return path, data if isinstance(data, dict) else None


def parse_percentages(
    allocation_data: dict[str, Any] | None,
    drift_spec: dict[str, Any] | None,
    summary: dict[str, Any] | None,
    overrides: dict[str, Any],
    family_id: str,
) -> dict[str, int]:
    candidates: list[Any] = []
    if allocation_data:
        candidates.extend(
            [
                allocation_data.get("allocation"),
                allocation_data.get("weights"),
                {channel: allocation_data.get(channel) for channel in CHANNELS},
            ]
        )
    if drift_spec:
        candidates.extend(
            [
                drift_spec.get("evidence"),
                drift_spec.get("evidence_allocation"),
                drift_spec.get("evidence_split"),
                drift_spec.get("d_evidence_weights"),
            ]
        )
    if summary:
        candidates.append(summary.get("evidence_split"))
    family_default = overrides.get(family_id, {}).get("evidence")
    if family_default:
        candidates.append(family_default)

    for candidate in candidates:
        parsed = coerce_evidence_percentages(candidate)
        if parsed is not None:
            return parsed
    return {channel: 0 for channel in CHANNELS}


def coerce_evidence_percentages(candidate: Any) -> dict[str, int] | None:
    if not isinstance(candidate, dict):
        return None
    values: dict[str, float] = {}
    for channel in CHANNELS:
        raw = candidate.get(channel)
        if raw is None:
            return None
        try:
            values[channel] = float(raw)
        except (TypeError, ValueError):
            return None
    if sum(values.values()) <= 1.01:
        values = {channel: value * 100 for channel, value in values.items()}
    return {channel: int(round(values[channel])) for channel in CHANNELS}


def find_evidence_files(family_dir: Path, allocation_path: Path | None, allocation_data: dict[str, Any] | None) -> dict[str, list[str]]:
    files: dict[str, set[str]] = {channel: set() for channel in CHANNELS}
    if allocation_path and allocation_data:
        for channel in CHANNELS:
            interface = allocation_data.get(f"{channel.lower()}_interface")
            if isinstance(interface, dict):
                for value in interface.values():
                    for candidate in _collect_declared_files(value):
                        resolved = (allocation_path.parent / candidate).resolve()
                        if resolved.exists() and family_dir.resolve() in resolved.parents:
                            files[channel].add(resolved.relative_to(family_dir.resolve()).as_posix())

    heuristics = {
        "D1": ("d1", "changelog", "notice", "policy", "declaration"),
        "D2": ("d2", "success_trace", "success_transcript", "success", "demonstration"),
        "D3": ("d3", "probe", "interaction", "counterexample", "help"),
    }
    for path in family_dir.rglob("*"):
        if not path.is_file() or path.name == "evidence_allocation.json":
            continue
        rel = path.relative_to(family_dir).as_posix()
        if "evidence/" not in rel.replace("\\", "/"):
            continue
        lowered = rel.lower().replace("-", "_")
        if "r_plus" in lowered or "oracle" in lowered:
            continue
        for channel, terms in heuristics.items():
            if any(term in lowered for term in terms):
                files[channel].add(rel)
    return {channel: sorted(values) for channel, values in files.items()}


def _collect_declared_files(value: Any) -> list[str]:
    if isinstance(value, str) and re.search(r"\.[A-Za-z0-9]+$", value):
        return [value]
    if isinstance(value, list):
        files: list[str] = []
        for item in value:
            files.extend(_collect_declared_files(item))
        return files
    if isinstance(value, dict):
        files = []
        for item in value.values():
            files.extend(_collect_declared_files(item))
        return files
    return []


def parse_evidence_mix(
    family_dir: Path,
    drift_spec: dict[str, Any] | None,
    summary: dict[str, Any] | None,
    overrides: dict[str, Any],
    family_id: str,
) -> dict[str, dict[str, Any]]:
    allocation_path, allocation_data = find_evidence_allocation(family_dir)
    percentages = parse_percentages(allocation_data, drift_spec, summary, overrides, family_id)
    files = find_evidence_files(family_dir, allocation_path, allocation_data)
    delivery_overrides = overrides.get(family_id, {}).get("evidence_delivery", {})
    allocation_delivery = allocation_data.get("delivery") if isinstance(allocation_data, dict) else {}

    evidence: dict[str, dict[str, Any]] = {}
    for channel in CHANNELS:
        pct = percentages.get(channel, 0)
        delivery = None
        if pct > 0:
            delivery = delivery_overrides.get(channel)
            if not delivery and isinstance(allocation_delivery, dict):
                raw_delivery = allocation_delivery.get(channel)
                if raw_delivery:
                    delivery = str(raw_delivery)
        evidence[channel] = {
            "percentage": pct,
            "present": pct > 0,
            "delivery": delivery,
            "files": files.get(channel, []),
        }
    return evidence


def extract_drift_summary(family_id: str, drift_spec: dict[str, Any] | None, overrides: dict[str, Any]) -> str:
    family_overrides = overrides.get(family_id, {})
    if family_overrides.get("drift_summary"):
        return family_overrides["drift_summary"]
    if drift_spec:
        for key in ("physical_event", "drift_summary", "summary", "description"):
            text = extract_text(drift_spec.get(key))
            if text:
                return trim_text(text, 220)
    return "No drift summary available."


def normalize_task(
    family_id: str,
    task: dict[str, Any],
    ordinal: int,
    source_file: str,
    overrides: dict[str, Any],
) -> dict[str, Any]:
    task_id = extract_task_id(task, family_id, ordinal)
    slice_name = extract_task_slice(task)
    instruction = extract_instruction(task)
    detail: dict[str, Any] = {}
    detail_fields = (
        "instruction",
        "question",
        "initial_state",
        "initial_config",
        "semantic_goal",
        "obligation_support",
        "stale_damage",
        "expected_behavior",
        "expected_behavior_under_stale_skill",
        "retention_property",
        "constraints",
        "tests",
        "source",
        "source_task",
    )
    for key in detail_fields:
        if key in task and key not in HIDDEN_DETAIL_KEYS:
            detail[key] = task[key]

    return {
        "id": task_id,
        "slice": slice_name,
        "description": make_task_description(family_id, task, slice_name, overrides),
        "instruction": instruction,
        "source_file": source_file,
        "details": detail,
    }


def load_sibling_summary(family_dir: Path) -> dict[str, Any] | None:
    matches = sorted(family_dir.rglob("sibling_summary.json"))
    if not matches:
        return None
    summary = load_optional_json(matches[0])
    return summary if isinstance(summary, dict) else None


def validate_family(family: dict[str, Any], allow_incomplete: bool = False) -> list[str]:
    warnings: list[str] = []
    if family["task_count"] == 0:
        message = f"{family['id']} has zero tasks"
        if allow_incomplete:
            warnings.append(message)
        else:
            raise ValueError(message)
    if not family.get("plan"):
        message = f"{family['id']} has no execution plan"
        if allow_incomplete:
            warnings.append(message)
        else:
            raise ValueError(message)

    task_ids = [task["id"] for task in family["tasks"]]
    if len(task_ids) != len(set(task_ids)):
        raise ValueError(f"{family['id']} has duplicate task IDs")

    total = sum(family["evidence"][channel]["percentage"] for channel in CHANNELS)
    if total != 100:
        message = f"{family['id']} evidence percentages sum to {total}, not 100"
        if allow_incomplete:
            warnings.append(message)
        else:
            raise ValueError(message)

    for channel in CHANNELS:
        item = family["evidence"][channel]
        if item["present"] and not item.get("delivery"):
            message = f"{family['id']} {channel} is present but has no delivery description"
            if allow_incomplete:
                warnings.append(message)
            else:
                raise ValueError(message)
    return warnings
