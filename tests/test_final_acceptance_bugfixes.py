from __future__ import annotations

from dynamics_core.feedback import build_diagnosis
from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy


def diagnose(problem: str):
    f = analyze_text(problem)
    r = recommend_strategy(f, "자동 추정")
    return build_diagnosis(problem, "", "자동 추정", f, r, enable_ai_assist=False)


def joined(items):
    return "\n".join(items)


def test_without_slipping_is_pure_rolling_not_sliding_rotation():
    d = diagnose("cylinder rolls without slipping down incline.")
    app = joined(d.blueprint.applicable_equations)
    na = joined(d.blueprint.not_applicable_equations)
    assert "순수 구름" in d.problem_model.problem_type
    assert "v_G = ωR" in app
    assert "a_G = αR" in app
    assert "미끄럼을 동반" not in d.problem_model.problem_type
    assert "v_G = ωR 적용 불가" not in na
    assert "a_G = αR 적용 불가" not in na


def test_wheel_rolls_without_slipping_is_pure_rolling():
    d = diagnose("wheel rolls without slipping.")
    app = joined(d.blueprint.applicable_equations)
    assert "순수 구름" in d.problem_model.problem_type
    assert "v_G = ωR" in app
    assert "a_G = αR" in app


def test_wheel_rolls_but_skids_is_sliding_rotation():
    d = diagnose("wheel rolls but skids.")
    app = joined(d.blueprint.applicable_equations)
    na = joined(d.blueprint.not_applicable_equations)
    assert "미끄럼" in d.problem_model.problem_type
    assert "v_G = ωR" not in app
    assert "a_G = αR" not in app
    assert "v_G = ωR" in na
    assert "a_G = αR" in na


def test_bottom_tension_short_query_prefers_T_not_N_only():
    d = diagnose("바닥점의 장력은?")
    app = joined(d.blueprint.applicable_equations)
    assert "T - mg = mv²/R" in app
    assert "T = mg + mv²/R" in app
    assert "N - mg = mv²/R" not in app
    assert "N = mg + mv²/R" not in app


def test_lowest_tension_mixed_language_prefers_T():
    d = diagnose("lowest에서 tension?")
    app = joined(d.blueprint.applicable_equations)
    assert "T - mg = mv²/R" in app
    assert "T = mg + mv²/R" in app
    assert "N - mg = mv²/R" not in app


def test_vertical_circle_lowest_tension_uses_bottom_string_template():
    d = diagnose("줄에 매단 공이 수직 원운동을 한다. lowest에서 tension을 구하라.")
    app = joined(d.blueprint.applicable_equations)
    assert "최저점" in d.problem_model.problem_type
    assert "T - mg = mv²/R" in app
    assert "T = mg + mv²/R" in app
    assert "N - mg = mv²/R" not in app


def test_projectile_remains_in_pivoted_rod_uses_angular_momentum():
    p = "a projectile hits and remains in a rod pivoted at one end; find angular velocity just after collision."
    d = diagnose(p)
    app = joined(d.blueprint.applicable_equations)
    na_cautions = joined(d.blueprint.not_applicable_equations + d.blueprint.cautions)
    assert "탄환" in d.problem_model.problem_type or "투사체" in d.problem_model.problem_type or "각운동량" in d.problem_model.problem_type
    assert "H_O(before) = H_O(after)" in app
    assert "m_b v r = I_totalω" in app
    assert "선운동량" in na_cautions
    assert "포물선" not in d.problem_model.problem_type


def test_string_angle_with_vertical_bob_revolves_is_conical():
    d = diagnose("string makes 30 degrees with vertical while bob revolves in a circle.")
    app = joined(d.blueprint.applicable_equations)
    assert "원뿔진자" in d.problem_model.problem_type
    assert "T cosθ = mg" in app
    assert "T sinθ = mω²r" in app
    assert "r = L sinθ" in app
    assert "ΣM_G = I_Gα" not in app


def test_negligible_friction_table_pulley_is_frictionless_block():
    d = diagnose("block on table, friction is negligible, tied to hanging mass.")
    app = joined(d.blueprint.applicable_equations)
    assert "수평면 블록" in d.problem_model.problem_type
    assert "f = 0" in app
    assert "T = m_Aa" in app
    assert "m_Bg - T = m_Ba" in app
    assert "f = μN_A" not in app


def test_polished_horizontal_table_is_frictionless_candidate_not_friction_present():
    d = diagnose("a block sits on a polished horizontal table connected over a pulley to a hanging mass.")
    app = joined(d.blueprint.applicable_equations)
    assert "수평면 블록" in d.problem_model.problem_type
    assert "f = 0" in app
    assert "f = μN_A" not in app
    assert "마찰 있는" not in d.problem_model.problem_type
