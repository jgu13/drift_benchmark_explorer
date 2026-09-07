"""Build the static Drift Benchmark Explorer site."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path
from typing import Any

from parsers import (
    CHANNELS,
    discover_family_dirs,
    extract_drift_summary,
    extract_task_list,
    find_drift_spec,
    find_execution_plan,
    find_task_file,
    load_json_or_jsonl,
    load_optional_json,
    load_sibling_summary,
    natural_family_key,
    normalize_task,
    parse_evidence_mix,
    validate_family,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DRIFT_WEB_ROOT = Path(__file__).resolve().parent
DEFAULT_SITE_DIR = DRIFT_WEB_ROOT / "site"
DEFAULT_OVERRIDES = DRIFT_WEB_ROOT / "family_overrides.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Drift Benchmark Explorer static site.")
    parser.add_argument(
        "--root",
        action="append",
        type=Path,
        help="Benchmark root to inspect. Can be passed more than once.",
    )
    parser.add_argument("--site-dir", type=Path, default=DEFAULT_SITE_DIR, help="Output site directory.")
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES, help="Family metadata overrides JSON.")
    parser.add_argument("--allow-incomplete", action="store_true", help="Warn instead of failing for incomplete families.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    roots = args.root or [
        PROJECT_ROOT / "data" / "A_drift_benchmark",
        PROJECT_ROOT / "data" / "B_drift_benchmark",
        PROJECT_ROOT / "data" / "C_drift_benchmark",
        PROJECT_ROOT / "data" / "D_drift_benchmark",
    ]
    roots = [root.resolve() for root in roots]
    site_dir = args.site_dir.resolve()
    overrides = load_optional_json(args.overrides.resolve()) or {}

    prepare_generated_dirs(site_dir)
    families = []
    warnings: list[str] = []
    for family_dir in discover_family_dirs(roots):
        family = build_family(family_dir.resolve(), site_dir, overrides)
        incomplete = family["task_count"] == 0 or not family.get("plan")
        warnings.extend(validate_family(family, allow_incomplete=args.allow_incomplete or incomplete))
        families.append(family)

    families.sort(key=lambda family: natural_family_key(family["id"]))
    index = {
        "roots": [str(root) for root in roots if root.exists()],
        "families": families,
    }
    data_path = site_dir / "data" / "benchmark_index.json"
    data_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Discovered {len(families)} families")
    for family in families:
        plan_name = family["plan"]["filename"] if family.get("plan") else "missing plan"
        task_source = family["task_source"]["path"] if family.get("task_source") else "missing tasks"
        evidence = ", ".join(f"{channel}={family['evidence'][channel]['percentage']}%" for channel in CHANNELS)
        print(f"- {family['id']}: {family['task_count']} tasks, {evidence}, plan={plan_name}, tasks={task_source}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    print(f"Wrote {data_path}")


def prepare_generated_dirs(site_dir: Path) -> None:
    for subdir in (
        site_dir / "data",
        site_dir / "assets" / "plans",
        site_dir / "assets" / "evidence",
    ):
        if subdir.exists():
            shutil.rmtree(subdir)
        subdir.mkdir(parents=True, exist_ok=True)


def build_family(family_dir: Path, site_dir: Path, overrides: dict[str, Any]) -> dict[str, Any]:
    family_id = family_dir.name
    family_overrides = overrides.get(family_id, {})
    drift_spec = find_drift_spec(family_dir)
    summary = load_sibling_summary(family_dir)
    plan_path = find_execution_plan(family_dir)
    task_path = find_task_file(family_dir)

    tasks: list[dict[str, Any]] = []
    task_source = None
    if task_path:
        raw_tasks = load_json_or_jsonl(task_path)
        source_file = task_path.relative_to(family_dir).as_posix()
        tasks = [
            normalize_task(family_id, task, ordinal, source_file, overrides)
            for ordinal, task in enumerate(extract_task_list(raw_tasks), start=1)
        ]
        task_source = {"path": source_file, "format": task_path.suffix.lstrip(".")}

    evidence = parse_evidence_mix(family_dir, drift_spec, summary, overrides, family_id)
    copy_evidence_assets(family_dir, site_dir, family_id, evidence)

    plan = None
    if plan_path:
        plan = copy_plan_asset(plan_path, site_dir, family_id)

    if "status_label" in family_overrides:
        status_label = family_overrides["status_label"]
    else:
        status_label = _status_from(summary) or _status_from(drift_spec) or "Unknown"
    family = {
        "id": family_id,
        "title": family_overrides.get("title", family_id),
        "platform": infer_platform(family_id, family_overrides),
        "mechanism": family_overrides.get("mechanism", ""),
        "status_label": status_label,
        "drift_summary": extract_drift_summary(family_id, drift_spec, overrides),
        "task_count": len(tasks),
        "source_path": str(family_dir),
        "task_source": task_source,
        "plan": plan,
        "evidence": evidence,
        "tasks": tasks,
        "paired_family": family_overrides.get("paired_family"),
        "family_notes": family_overrides.get("family_notes", []),
        "files_manifest": build_files_manifest(family_dir),
    }
    return family


def infer_platform(family_id: str, family_overrides: dict[str, Any]) -> str:
    if family_overrides.get("platform"):
        return family_overrides["platform"]
    defaults = {
        "A": "ALFWorld",
        "B": "SkillLearn",
        "C": "BFCL",
        "D": "OSWorld",
    }
    return defaults.get(family_id[:1], "Unknown")


def _status_from(data: dict[str, Any] | None) -> str | None:
    if not data:
        return None
    status = data.get("status")
    if not status:
        return None
    return str(status).replace("_", " ").title()


def copy_plan_asset(plan_path: Path, site_dir: Path, family_id: str) -> dict[str, str]:
    markdown = plan_path.read_text(encoding="utf-8")
    md_asset = site_dir / "assets" / "plans" / f"{family_id}.md"
    html_asset = site_dir / "assets" / "plans" / f"{family_id}.html"
    md_asset.write_text(markdown, encoding="utf-8")
    html_asset.write_text(markdown_to_html(markdown), encoding="utf-8")
    return {
        "filename": plan_path.name,
        "asset_path": f"assets/plans/{family_id}.md",
        "html_asset_path": f"assets/plans/{family_id}.html",
    }


def copy_evidence_assets(family_dir: Path, site_dir: Path, family_id: str, evidence: dict[str, dict[str, Any]]) -> None:
    destination_root = site_dir / "assets" / "evidence" / family_id
    for channel in CHANNELS:
        for rel in evidence[channel]["files"]:
            source = family_dir / rel
            if not source.exists():
                continue
            destination = destination_root / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


def build_files_manifest(family_dir: Path) -> list[dict[str, str]]:
    visible_terms = (
        "drift_spec.json",
        "siblings.json",
        "siblings.jsonl",
        "sibling_summary.json",
        "task.json",
        "README.md",
        "skill_r_minus.md",
        "evidence/",
        "validation/",
        "grader_spec.json",
        "source_task.md",
    )
    hidden_terms = (
        "gold_",
        "r_plus_oracle",
        "possible_answer",
        "graph_truth",
        "__pycache__",
    )
    manifest = []
    for path in sorted(family_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(family_dir).as_posix()
        lowered = rel.lower()
        if any(term in lowered for term in hidden_terms):
            continue
        if any(term.lower() in lowered for term in visible_terms):
            manifest.append({"path": rel, "kind": path.suffix.lstrip(".") or "file"})
    return manifest


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None
    in_code = False
    code_lines: list[str] = []
    index = 0

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            output.append(f"<p>{inline_markdown(' '.join(paragraph))}</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            output.append(f"</{list_type}>")
            list_type = None

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                output.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines = []
                in_code = False
            else:
                flush_paragraph()
                close_list()
                in_code = True
                code_lines = []
            index += 1
            continue

        if in_code:
            code_lines.append(line)
            index += 1
            continue

        if not stripped:
            flush_paragraph()
            close_list()
            index += 1
            continue

        if is_table_start(lines, index):
            flush_paragraph()
            close_list()
            table_lines = [lines[index]]
            index += 2
            while index < len(lines) and "|" in lines[index] and lines[index].strip():
                table_lines.append(lines[index])
                index += 1
            output.append(render_table(table_lines))
            continue

        if stripped.startswith("#"):
            hashes = len(stripped) - len(stripped.lstrip("#"))
            if 1 <= hashes <= 6 and stripped[hashes : hashes + 1] == " ":
                flush_paragraph()
                close_list()
                level = min(hashes, 4)
                text = stripped[hashes:].strip()
                output.append(f"<h{level}>{inline_markdown(text)}</h{level}>")
                index += 1
                continue

        unordered = re_match_unordered(stripped)
        ordered = re_match_ordered(stripped)
        if unordered or ordered:
            flush_paragraph()
            desired = "ul" if unordered else "ol"
            if list_type != desired:
                close_list()
                output.append(f"<{desired}>")
                list_type = desired
            item_text = unordered or ordered or ""
            output.append(f"<li>{inline_markdown(item_text)}</li>")
            index += 1
            continue

        paragraph.append(stripped)
        index += 1

    flush_paragraph()
    close_list()
    if in_code:
        output.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
    return "\n".join(output) + "\n"


def re_match_unordered(stripped: str) -> str | None:
    if stripped.startswith(("- ", "* ")):
        return stripped[2:].strip()
    return None


def re_match_ordered(stripped: str) -> str | None:
    parts = stripped.split(maxsplit=1)
    if len(parts) == 2 and parts[0].rstrip(".").isdigit() and parts[0].endswith("."):
        return parts[1].strip()
    return None


def is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines) or "|" not in lines[index]:
        return False
    separator = lines[index + 1].strip()
    if "|" not in separator:
        return False
    compact = separator.replace("|", "").replace(":", "").replace("-", "").strip()
    return compact == ""


def render_table(table_lines: list[str]) -> str:
    rows = [split_table_row(line) for line in table_lines]
    if not rows:
        return ""
    header, body = rows[0], rows[1:]
    thead = "<thead><tr>" + "".join(f"<th>{inline_markdown(cell)}</th>" for cell in header) + "</tr></thead>"
    tbody_rows = []
    for row in body:
        tbody_rows.append("<tr>" + "".join(f"<td>{inline_markdown(cell)}</td>" for cell in row) + "</tr>")
    return "<table>" + thead + "<tbody>" + "".join(tbody_rows) + "</tbody></table>"


def split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = escaped.replace("`", "&#96;")
    return escaped


if __name__ == "__main__":
    main()
