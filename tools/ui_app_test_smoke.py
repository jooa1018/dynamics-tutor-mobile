from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ["PYTHONPATH"] = str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")


def run_app_test() -> dict:
    try:
        from streamlit.testing.v1 import AppTest
    except Exception as exc:
        return {
            "streamlit_apptest": "skipped_missing_streamlit",
            "reason": type(exc).__name__,
            "student_mode_default": "not_run",
            "example_button_click": "not_run",
            "diagnosis_button_click": "not_run",
            "debug_mode_available": "not_run",
            "raw_exception_visible": False,
        }

    at = AppTest.from_file(str(ROOT / "app.py"))
    at.run(timeout=20)
    result = {
        "streamlit_apptest": "passed",
        "beginner_mode_default": False,
        "example_button_click": False,
        "diagnosis_button_click": False,
        "debug_mode_available": False,
        "raw_exception_visible": False,
    }
    if at.radio and at.radio[0].value in {"입문자 모드", "학생 모드"}:
        result["beginner_mode_default"] = True
    labels = [b.label for b in at.button]
    if "순수 구름" in labels:
        idx = labels.index("순수 구름")
        at.button[idx].click().run(timeout=20)
        result["example_button_click"] = bool(at.text_area and "without" in (at.text_area[0].value or ""))
    labels = [b.label for b in at.button]
    if "진단 실행" in labels:
        idx = labels.index("진단 실행")
        at.button[idx].click().run(timeout=30)
        result["diagnosis_button_click"] = len(at.error) == 0
    if at.radio and "전문가/디버그 모드" in at.radio[0].options:
        result["debug_mode_available"] = True
    rendered = "\n".join(str(x.value) for x in at.markdown) + "\n" + "\n".join(str(x.value) for x in at.error)
    result["raw_exception_visible"] = "Traceback" in rendered or "OPENAI_API_KEY=" in rendered
    if not all(v is True for k, v in result.items() if k not in {"streamlit_apptest", "raw_exception_visible"}):
        raise AssertionError(result)
    if result["raw_exception_visible"]:
        raise AssertionError("raw exception or API key leaked")
    return result


if __name__ == "__main__":
    DOCS.mkdir(exist_ok=True)
    result = run_app_test()
    (DOCS / "UI_APPTEST_RESULT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
