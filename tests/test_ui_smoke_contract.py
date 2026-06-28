from __future__ import annotations

import re
from pathlib import Path

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
    unique_equation_sections,
)


def diagnose(problem: str, solution: str = ""):
    features = analyze_text(problem, solution)
    rec = recommend_strategy(features, "자동 추정")
    return features, rec, build_diagnosis(problem, solution, "자동 추정", features, rec, enable_ai_assist=False)


def test_example_library_all_examples_generate_student_cards():
    assert len(EXAMPLE_LIBRARY) >= 10
    expected_contexts = {
        "순수 구름": "pure_rolling",
        "미끄럼 동반 회전": "sliding_rotation",
        "원뿔진자": "conical_pendulum",
        "수직 원운동 장력": "vertical_circle_string",
        "수직 원운동 수직항력": "vertical_circle_track",
        "경사진 커브 최대속도": "banked_curve",
        "경사진 커브 최소속도": "banked_curve",
        "수평면 블록-도르래": "block_pulley",
        "위치벡터 미분": "cartesian_vector",
        "탄환-회전강체 충돌": "bullet_rotating_body_collision",
    }
    for label, problem in EXAMPLE_LIBRARY.items():
        _, _, diagnosis = diagnose(problem)
        payload = public_student_payload(diagnosis)
        ctx = choose_fbd_context(problem, diagnosis)
        assert ctx.kind == expected_contexts[label]
        assert payload["problem_type"]
        assert payload["fbd_forces"] or payload["coordinate_guide"]
        assert payload["applicable_equations"]
        assert payload["steps"]
        assert_no_student_debug_leak(payload)


def test_student_mode_debug_terms_are_not_in_public_payload():
    _, _, diagnosis = diagnose("A projectile strikes a hinged bar and sticks; determine angular speed after impact.")
    payload = public_student_payload(diagnosis)
    assert_no_student_debug_leak(payload)
    serialized = str(payload).lower()
    for forbidden in ["template_id", "raw json", "ai confidence", "cache hit", "fallback log", "openai_api_key"]:
        assert forbidden not in serialized


def test_app_source_debug_panel_is_gated_by_expert_mode():
    text = Path("app.py").read_text(encoding="utf-8")
    assert "학생 모드" in text and "전문가/디버그 모드" in text
    assert "if view_mode == \"전문가/디버그 모드\":" in text
    assert "render_debug_panel" in text
    # Student mode should use simple status labels rather than raw key/model details.
    assert "API 연결 상태" in text
    assert "API key 값은 화면과 로그에 표시하지 않습니다" in text


def test_fbd_context_frictionless_block_pulley_hides_friction_arrow():
    problem = "Block A lies on a friction-free table and is tied to hanging block B."
    _, _, diagnosis = diagnose(problem)
    ctx = choose_fbd_context(problem, diagnosis)
    assert ctx.kind == "block_pulley"
    assert ctx.show_friction is False
    assert "f = 0" in ctx.friction_label


def test_fbd_context_banked_curve_max_min_have_different_friction_direction():
    max_problem = "car on a sloped curve with friction, find highest speed before sliding up the bank"
    min_problem = "car on inclined curve, find minimum speed before sliding down"
    _, _, max_diag = diagnose(max_problem)
    _, _, min_diag = diagnose(min_problem)
    max_ctx = choose_fbd_context(max_problem, max_diag)
    min_ctx = choose_fbd_context(min_problem, min_diag)
    assert max_ctx.kind == min_ctx.kind == "banked_curve"
    assert max_ctx.banked_speed_case == "max"
    assert min_ctx.banked_speed_case == "min"
    assert max_ctx.friction_direction != min_ctx.friction_direction


def test_fbd_context_force_symbol_tension_and_normal_do_not_mix():
    _, _, string_diag = diagnose("줄에 매단 공이 수직 원운동을 한다. lowest에서 tension을 구하라.")
    string_ctx = choose_fbd_context("줄에 매단 공이 수직 원운동을 한다. lowest에서 tension을 구하라.", string_diag)
    assert string_ctx.kind == "vertical_circle_string"
    assert string_ctx.force_symbol == "T"

    _, _, rail_diag = diagnose("원형 레일의 최하점에서 수직항력을 구하라.")
    rail_ctx = choose_fbd_context("원형 레일의 최하점에서 수직항력을 구하라.", rail_diag)
    assert rail_ctx.kind == "vertical_circle_track"
    assert rail_ctx.force_symbol == "N"

    _, _, conflict_diag = diagnose("a bead on a vertical circular rail. tension at bottom?")
    conflict_ctx = choose_fbd_context("a bead on a vertical circular rail. tension at bottom?", conflict_diag)
    assert conflict_ctx.ambiguity_note


def test_export_markdown_html_and_equations_are_structured():
    problem = EXAMPLE_LIBRARY["원뿔진자"]
    _, _, diagnosis = diagnose(problem, "T cos theta = mg")
    md = build_markdown_export(problem, "T cos theta = mg", diagnosis)
    html = build_html_export(problem, "T cos theta = mg", diagnosis)
    eq = build_equations_only_export(diagnosis)
    assert "## 문제 유형" in md
    assert "## FBD / 좌표축" in md
    assert "## 적용식" in md
    assert "## 이 문제에서 쓰면 안 되는 식" in md
    assert "<!doctype html>" in html and "charset='utf-8'" in html
    assert "[적용식]" in eq and "[비적용식]" in eq
    assert "OPENAI_API_KEY" not in md + html + eq


def test_equation_sections_do_not_duplicate_same_equation():
    applicable, blocked = unique_equation_sections(["v_G = ωR"], ["v_G = ωR", "a_G = αR 적용 불가"])
    assert applicable == ["v_G = ωR"]
    assert "v_G = ωR" not in blocked
    assert "a_G = αR 적용 불가" in blocked


def test_records_save_search_favorite_delete_roundtrip(tmp_path):
    db = tmp_path / "records.sqlite3"
    rid = save_record(
        {
            "problem": "Cylinder rolls without slipping.",
            "solution": "",
            "goal": "가속도",
            "recommended": "순수 구름",
            "confidence": "0.95",
            "problem_type": "순수 구름 운동",
            "blueprint_equations": ["v_G = ωR", "a_G = αR"],
            "not_applicable_equations": [],
            "missing": [],
            "misconceptions": [],
            "favorite": False,
        },
        path=db,
    )
    records = list_records(path=db)
    assert len(records) == 1
    assert records[0]["applicable_equations"] == ["v_G = ωR", "a_G = αR"]
    set_favorite(rid, True, path=db)
    assert list_records(path=db)[0]["favorite"] is True
    delete_record(rid, path=db)
    assert list_records(path=db) == []


def test_friendly_error_messages_hide_raw_exceptions():
    for key in ["ai", "save", "export", "empty", "short"]:
        msg = friendly_error_message(key)
        assert "Traceback" not in msg
        assert "{exc}" not in msg
        assert "OPENAI_API_KEY" not in msg
        assert len(msg) > 5
