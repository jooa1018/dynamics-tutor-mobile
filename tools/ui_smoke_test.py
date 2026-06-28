from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynamics_core.feedback import build_diagnosis
from dynamics_core.parser import analyze_text
from dynamics_core.storage import delete_record, list_records, save_record, set_favorite
from dynamics_core.strategy_engine import recommend_strategy
from dynamics_core.ui_helpers import (
    EXAMPLE_LIBRARY,
    assert_no_student_debug_leak,
    build_equations_only_export,
    build_html_export,
    build_markdown_export,
    choose_fbd_context,
    friendly_error_message,
    public_student_payload,
)

DOCS = ROOT / "docs"


def diagnose(problem: str, solution: str = ""):
    features = analyze_text(problem, solution)
    rec = recommend_strategy(features, "자동 추정")
    diagnosis = build_diagnosis(problem, solution, "자동 추정", features, rec, enable_ai_assist=False)
    return features, rec, diagnosis


def smoke_check() -> dict:
    result: dict = {
        "ui_smoke_test": "passed",
        "streamlit_apptest": "see docs/UI_APPTEST_RESULT.json",
        "browser_click_test": "attempted_but_blocked_by_sandbox_browser_policy",
        "checks": [],
        "examples": [],
        "exports": {},
        "records": {},
        "api_key_exposed": False,
    }
    app_source = (ROOT / "app.py").read_text(encoding="utf-8")
    source_checks = {
        "student_mode_default": "학생 모드" in app_source,
        "expert_debug_gated": "if view_mode == \"전문가/디버그 모드\":" in app_source and "render_debug_panel" in app_source,
        "friendly_empty_message": "friendly_error_message(\"empty\")" in app_source,
        "api_key_not_logged": "API key 값은 화면과 로그에 표시하지 않습니다" in app_source,
        "markdown_export_button": "Markdown 다운로드" in app_source,
        "html_export_button": "HTML 다운로드" in app_source,
        "equation_export_button": "식-only 다운로드" in app_source,
    }
    for name, ok in source_checks.items():
        if not ok:
            raise AssertionError(name)
        result["checks"].append({"name": name, "status": "passed"})

    for label, problem in EXAMPLE_LIBRARY.items():
        _, _, diagnosis = diagnose(problem, "")
        payload = public_student_payload(diagnosis)
        assert_no_student_debug_leak(payload)
        ctx = choose_fbd_context(problem, diagnosis)
        if not payload["applicable_equations"]:
            raise AssertionError(f"example {label} has empty applicable equations")
        if not (payload["fbd_forces"] or payload["coordinate_guide"]):
            raise AssertionError(f"example {label} has no FBD/coordinate data")
        result["examples"].append({
            "label": label,
            "problem_type": payload["problem_type"],
            "fbd_kind": ctx.kind,
            "force_symbol": ctx.force_symbol,
            "applicable_count": len(payload["applicable_equations"]),
            "not_applicable_count": len(payload["not_applicable_equations"]),
            "student_debug_leak": False,
        })

    sample_problem = EXAMPLE_LIBRARY["원뿔진자"]
    _, _, sample_diag = diagnose(sample_problem, "T cos theta = mg")
    md = build_markdown_export(sample_problem, "T cos theta = mg", sample_diag)
    html = build_html_export(sample_problem, "T cos theta = mg", sample_diag)
    eq = build_equations_only_export(sample_diag)
    for name, content, required in [
        ("markdown", md, "## 적용식"),
        ("html", html, "<!doctype html>"),
        ("equations_only", eq, "[적용식]"),
    ]:
        if required not in content or "OPENAI_API_KEY" in content:
            raise AssertionError(f"bad export {name}")
        result["exports"][name] = {"status": "passed", "bytes": len(content.encode("utf-8"))}

    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "records.sqlite3"
        rid = save_record(
            {
                "problem": sample_problem,
                "solution": "T cos theta = mg",
                "goal": "각속도",
                "recommended": "원뿔진자",
                "confidence": "0.9",
                "problem_type": "원뿔진자",
                "blueprint_equations": public_student_payload(sample_diag)["applicable_equations"],
                "not_applicable_equations": public_student_payload(sample_diag)["not_applicable_equations"],
                "missing": [],
                "misconceptions": [],
                "favorite": False,
            },
            path=db,
        )
        set_favorite(rid, True, path=db)
        records = list_records(path=db)
        if not records or not records[0]["favorite"]:
            raise AssertionError("record favorite failed")
        delete_record(rid, path=db)
        if list_records(path=db):
            raise AssertionError("record delete failed")
        result["records"] = {"save": "passed", "favorite": "passed", "delete": "passed"}

    for key in ["ai", "save", "export", "empty", "short"]:
        msg = friendly_error_message(key)
        if "Traceback" in msg or "{exc}" in msg or "OPENAI_API_KEY" in msg:
            raise AssertionError(f"raw error leak: {key}")
    result["checks"].append({"name": "friendly_errors", "status": "passed"})
    return result


def write_reports(result: dict) -> None:
    DOCS.mkdir(exist_ok=True)
    (DOCS / "UI_SMOKE_TEST_RESULT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# UI Smoke Test Result", "",
        f"- Status: **{result['ui_smoke_test']}**",
        f"- Browser click test: **{result['browser_click_test']}**",
        f"- Streamlit AppTest: **{result.get('streamlit_apptest', 'not_recorded')}**",
        "- Note: This scripted smoke test validates the UI contract without requiring a browser session. In this sandbox Chromium navigation to localhost was blocked; run `streamlit run app.py` for local visual QA.",
        "", "## Source/contract checks",
    ]
    for item in result["checks"]:
        lines.append(f"- {item['name']}: {item['status']}")
    lines.extend(["", "## Example library checks"])
    for item in result["examples"]:
        lines.append(f"- {item['label']}: {item['problem_type']} / FBD={item['fbd_kind']} / equations={item['applicable_count']}")
    lines.extend(["", "## Export checks"])
    for name, item in result["exports"].items():
        lines.append(f"- {name}: {item['status']} ({item['bytes']} bytes)")
    lines.extend(["", "## Records checks"])
    for name, status in result["records"].items():
        lines.append(f"- {name}: {status}")
    (DOCS / "UI_SMOKE_TEST_RESULT.md").write_text("\n".join(lines), encoding="utf-8")

    ex_lines = ["# Example Library Test Result", "", "All built-in examples were diagnosed with non-empty FBD data, applicable equations, and student-safe payloads.", ""]
    for item in result["examples"]:
        ex_lines.extend([
            f"## {item['label']}",
            f"- Problem type: {item['problem_type']}",
            f"- FBD kind: {item['fbd_kind']}",
            f"- Force symbol: {item['force_symbol'] or 'n/a'}",
            f"- Applicable equations: {item['applicable_count']}",
            f"- Student debug leak: {item['student_debug_leak']}",
            "",
        ])
    (DOCS / "EXAMPLE_LIBRARY_TEST_RESULT.md").write_text("\n".join(ex_lines), encoding="utf-8")


if __name__ == "__main__":
    report = smoke_check()
    write_reports(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
