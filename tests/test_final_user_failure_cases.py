from __future__ import annotations

from dynamics_core.feedback import build_diagnosis
from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy


def diagnose(problem: str):
    f = analyze_text(problem)
    r = recommend_strategy(f, "자동 추정")
    return build_diagnosis(problem, "", "자동 추정", f, r)


def joined(items):
    return "\n".join(items)


def test_banked_curve_limiting_speed_with_friction_is_not_frictionless_design_speed_only():
    d = diagnose("뱅크 커브에서 limiting speed를 구하라. friction이 있다.")
    bp = d.blueprint
    assert "마찰 있는 경사진 커브" in d.problem_model.problem_type
    assert "tanθ = v²/(gR)" not in joined(bp.applicable_equations)
    assert "N = mg" not in joined(bp.applicable_equations)
    assert bp.ambiguity_notes or "최대속도" in d.problem_model.problem_type or "최소속도" in d.problem_model.problem_type


def test_banked_road_upper_limit_speed_uses_friction_max_template():
    d = diagnose("마찰 있는 banked road에서 upper limit of speed를 구하라.")
    app = joined(d.blueprint.applicable_equations)
    assert "마찰 있는 경사진 커브 최대속도" in d.problem_model.problem_type
    assert "N cosθ - f sinθ = mg" in app
    assert "N sinθ + f cosθ = mv²/R" in app
    assert "f = μ_sN" in app
    assert "μ_s ≥ v²/(gR)" not in app


def test_conical_pendulum_table_parallel_circle_variant():
    d = diagnose("실 끝의 질점이 테이블과 평행한 원궤도를 돈다. 실은 연직과 θ.")
    app = joined(d.blueprint.applicable_equations)
    assert "원뿔진자" in d.problem_model.problem_type
    assert "T cosθ = mg" in app
    assert "T sinθ = mω²r" in app
    assert "ΣM_G = I_Gα" not in app


def test_conical_pendulum_cone_shape_candidate_variant():
    d = diagnose("줄에 매달린 구슬이 원뿔꼴로 움직인다.")
    assert "원뿔진자" in d.problem_model.problem_type or any("원뿔진자" in x for x in d.blueprint.ambiguity_notes + d.blueprint.cautions)
    assert "ΣM_G = I_Gα" not in joined(d.blueprint.applicable_equations)


def test_sliding_rotation_contact_point_slips():
    d = diagnose("cylinder rotates but the contact point slips.")
    app = joined(d.blueprint.applicable_equations)
    na = joined(d.blueprint.not_applicable_equations)
    assert "미끄럼" in d.problem_model.problem_type
    assert "ΣF = ma_G" in app
    assert "ΣM_G = I_Gα" in app
    assert "v_G = ωR" not in app
    assert "a_G = αR" not in app
    assert "v_G = ωR" in na


def test_sliding_rotation_rolls_but_skids():
    d = diagnose("wheel rolls but skids.")
    app = joined(d.blueprint.applicable_equations)
    assert "미끄럼" in d.problem_model.problem_type
    assert "v_G = ωR" not in app
    assert "a_G = αR" not in app


def test_vertical_circle_bottom_rope_variant():
    d = diagnose("줄에 매단 공이 수직 원운동을 한다. 하단에서 장력을 구하라.")
    app = joined(d.blueprint.applicable_equations)
    assert "최저점" in d.problem_model.problem_type
    assert "T - mg = mv²/R" in app
    assert "T = mg + mv²/R" in app
    assert "N - mg" not in app


def test_frictionless_table_negligible_friction_variant():
    d = diagnose("Block A is on a table with negligible friction connected to hanging B by pulley.")
    app = joined(d.blueprint.applicable_equations)
    assert "수평면 블록" in d.problem_model.problem_type
    assert "f = 0" in app
    assert "T = m_Aa" in app
    assert "m_Bg - T = m_Ba" in app
    assert "f = μN_A" not in app


def test_cartesian_position_vector_rvec_variant():
    d = diagnose("r⃗(t)=3t i + 2t^2 j 로 주어진다. 속도와 가속도는?")
    app = joined(d.blueprint.applicable_equations)
    assert "위치 함수" in d.problem_model.problem_type or "직교좌표" in d.problem_model.problem_type
    assert "v(t) = dr/dt" in app
    assert "a(t) = d²r/dt²" in app
    assert "e_r" not in app and "e_θ" not in app


def test_projectile_embeds_wheel_fixed_axle_is_angular_momentum_not_projectile_motion():
    d = diagnose("projectile embeds in a wheel and they rotate together about a fixed axle.")
    app = joined(d.blueprint.applicable_equations)
    assert "회전강체" in d.problem_model.problem_type or "각운동량" in d.problem_model.problem_type
    assert "H_O(before) = H_O(after)" in app
    assert "포물선" not in d.problem_model.problem_type
