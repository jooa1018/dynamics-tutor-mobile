from __future__ import annotations

from pathlib import Path

from dynamics_core.feedback import build_diagnosis
from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy
from dynamics_core.calculators import (
    block_pulley_frictionless,
    centripetal_acceleration,
    convert_common_units,
    incline_acceleration,
    vertical_circle_force,
)
from dynamics_core.storage import save_record, list_records
from dynamics_core.mobile_support import classify_problem_difficulty, review_due_by_miss_count


def diagnose(problem: str, solution: str = ""):
    features = analyze_text(problem, solution)
    rec = recommend_strategy(features, "자동 추정")
    diag = build_diagnosis(problem, solution, "자동 추정", features, rec, enable_ai_assist=False)
    bp = diag.blueprint
    app = "\n".join(getattr(bp, "applicable_equations", []) or getattr(bp, "governing_equations", []))
    blocked = "\n".join(getattr(bp, "not_applicable_equations", []))
    all_text = "\n".join([
        diag.problem_model.problem_type,
        bp.title,
        app,
        blocked,
        "\n".join(getattr(bp, "cautions", [])),
        "\n".join(getattr(bp, "ambiguity_notes", [])),
    ])
    return diag, bp, app, blocked, all_text


def test_block_pulley_never_contains_conical_formulas():
    p = "마찰 없는 수평면 위 블록 A와 매달린 블록 B가 질량 없는 줄과 도르래로 연결되어 있다. 가속도와 장력을 구하라."
    diag, bp, app, blocked, all_text = diagnose(p)
    assert "블록" in diag.problem_model.problem_type and "매달" in diag.problem_model.problem_type
    assert "T = m_Aa" in app
    assert "m_Bg - T = m_Ba" in app
    for bad in ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"]:
        assert bad not in app
        assert bad not in all_text
    assert "원뿔진자" in all_text and "배제" in all_text


def test_conical_pendulum_still_outputs_conical_equations():
    p = "질량 m인 물체가 길이 L인 줄에 매달려 수직선과 각도 θ를 이루며 수평 원운동한다. 각속도를 구하라."
    diag, bp, app, blocked, all_text = diagnose(p)
    assert "원뿔진자" in diag.problem_model.problem_type
    assert "T cosθ = mg" in app
    assert "T sinθ = mω²r" in app
    assert "r = L sinθ" in app


def test_frictionless_student_solution_using_friction_is_flagged():
    p = "마찰 없는 수평면 위 블록 A와 매달린 블록 B가 줄로 연결되어 있다."
    s = "블록 A에는 마찰력이 있으므로 f = μN이다."
    diag, bp, app, blocked, all_text = diagnose(p, s)
    names = [x[0] for x in diag.misconception_hits]
    assert "마찰 없는 문제에서 마찰력 사용" in names
    assert any("마찰 없는 조건" in x[1] for x in diag.misconception_hits)


def test_frictionless_body_does_not_apply_friction_formula():
    p = "마찰 없는 수평면 위 물체가 힘 F를 받아 움직인다."
    diag, bp, app, blocked, all_text = diagnose(p)
    assert "f = 0" in app
    assert "f = μN" not in app


def test_sliding_rolling_forbids_pure_rolling_equations():
    p = "원판이 미끄러지며 움직인다."
    diag, bp, app, blocked, all_text = diagnose(p)
    assert "v_G = ωR" not in app
    assert "a_G = αR" not in app
    assert "적용식으로 사용 불가" in blocked or "사용 금지" in blocked


def test_banked_curve_with_radius_and_mu_can_show_symbolic_theta_formulas():
    p = "자동차가 반지름 R인 경사진 도로를 마찰계수 μ로 돈다. 최대 속도를 구하라."
    diag, bp, app, blocked, all_text = diagnose(p)
    assert "경사진 커브" in diag.problem_model.problem_type
    assert "N cosθ - f sinθ = mg" in app
    assert "N sinθ + f cosθ = mv²/R" in app
    assert "f = μ_sN" in app
    assert "N = mg" not in app


def test_block_pulley_numeric_helper_and_explanatory_formula():
    result = block_pulley_frictionless(2.0, 3.0)
    assert result.ok
    assert abs(result.values["a"] - 3.0 * 9.81 / 5.0) < 1e-9
    assert "T = m_A a" in result.formula
    assert any("마찰 없는" in x for x in result.assumptions)


def test_beginner_calculators_and_unit_conversions():
    assert incline_acceleration(30.0, frictionless=True).ok
    assert centripetal_acceleration(0.3, speed=20.0).ok
    assert vertical_circle_force(1.0, 3.0, 2.0, position="bottom").ok
    converted = convert_common_units("질량 500 g인 물체가 72 km/h로 반지름 30 cm에서 120 rpm 회전한다.")
    assert "500 g = 0.5 kg" in converted
    assert "72 km/h = 20 m/s" in converted
    assert "30 cm = 0.3 m" in converted
    assert any("120 rpm" in x and "rad/s" in x for x in converted)


def test_storage_auto_wrong_reasons_include_beginner_tags(tmp_path: Path):
    db = tmp_path / "study.sqlite3"
    rid = save_record({
        "problem": "마찰 없는 면이지만 f = μN을 썼다.",
        "problem_type": "수평면 블록 문제",
        "not_applicable_equations": ["f = μN : 마찰 없음에서는 사용 금지"],
        "missing": ["조건 누락"],
        "misconceptions": ["마찰 없는 문제에서 마찰력 사용"],
        "wrong_reasons": [],
    }, path=db)
    record = list_records(path=db)[0]
    assert record["wrong_reasons"]
    assert "조건 누락" in record["wrong_reasons"]
    assert "금지식 사용" in record["wrong_reasons"]


def test_review_schedule_and_difficulty_helpers():
    assert review_due_by_miss_count(1)
    assert review_due_by_miss_count(4)
    level, reason = classify_problem_difficulty("수평면 위 블록과 매달린 물체가 도르래로 연결되어 있다.")
    assert level == "Level 2"
    assert "두 물체" in reason

from dataclasses import dataclass
from dynamics_core.ui_helpers import (
    choose_fbd_context,
    assert_no_student_debug_leak,
    equation_explanation,
    forbidden_explanation,
    friendly_error_message,
    to_jsonable,
)
from dynamics_core.calculators import solve_constant_acceleration, projectile_motion, circular_min_speed, collision_1d, rolling_speed_from_height


@dataclass
class DummyData:
    x: int


def test_ui_helper_explanation_branches_and_contexts():
    assert choose_fbd_context("rail at bottom tension?").ambiguity_note
    assert choose_fbd_context("A ball on a vertical loop, tension at bottom").kind == "vertical_circle_string"
    assert choose_fbd_context("원형 레일의 최하점에서 수직항력").force_symbol == "N"
    assert choose_fbd_context("A cylinder rolls without slipping").rolling_mode == "pure_rolling"
    assert choose_fbd_context("A cylinder is rolling while slipping").rolling_mode == "sliding_rotation"
    assert choose_fbd_context("rough table with hanging mass").show_friction is True
    assert choose_fbd_context("block on table with hanging mass").kind == "block_pulley"
    assert choose_fbd_context("block on incline").kind == "incline"
    assert "수직항력" in equation_explanation("f = μN")
    assert "회전" in equation_explanation("ΣM_G = I_Gα")
    assert "고정점 O" in equation_explanation("H_O(before) = H_O(after)")
    assert "운동에너지" in forbidden_explanation("운동에너지 보존 단독 적용 금지")
    assert "구심력" in forbidden_explanation("구심력을 FBD에 별도 힘처럼 추가 금지")
    assert "문제를 입력" in friendly_error_message("empty")
    assert to_jsonable(DummyData(3))["x"] == 3
    try:
        assert_no_student_debug_leak({"template_id": "x"})
    except AssertionError as exc:
        assert "template_id" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("debug leak should have been detected")


def test_calculator_error_and_extra_branches():
    assert not solve_constant_acceleration({"t": -1}, "x").ok
    assert solve_constant_acceleration({"u": 0, "a": 2, "t": 3}, "v").ok
    assert not projectile_motion(1, 45, air_resistance=True).ok
    assert projectile_motion(10, -30).ok
    assert not circular_min_speed(0).ok
    assert collision_1d(1, 0, 1, 0, 2).warnings
    assert not rolling_speed_from_height(1, 3).ok
    assert not block_pulley_frictionless(-1, 2).ok
    assert not incline_acceleration(100).ok
    assert not centripetal_acceleration(1).ok
    assert centripetal_acceleration(2, omega=3).ok
    assert not vertical_circle_force(1, 1, 1, position="middle").ok
    assert vertical_circle_force(1, 1, 10, position="top").warnings
