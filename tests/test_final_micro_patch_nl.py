from __future__ import annotations

import pytest

from dynamics_core.feedback import build_diagnosis
from dynamics_core.parser import analyze_text
from dynamics_core.semantic_normalizer import semantic_flags
from dynamics_core.strategy_engine import recommend_strategy


def diagnose(problem: str):
    features = analyze_text(problem)
    rec = recommend_strategy(features, "자동 추정")
    diag = build_diagnosis(problem, "", "자동 추정", features, rec, enable_ai_assist=False)
    bp = diag.blueprint
    app = "\n".join(getattr(bp, "applicable_equations", []) or bp.governing_equations)
    not_app = "\n".join(getattr(bp, "not_applicable_equations", []))
    all_text = "\n".join([
        diag.problem_model.problem_type,
        bp.title,
        app,
        not_app,
        "\n".join(getattr(bp, "cautions", [])),
        "\n".join(getattr(bp, "ambiguity_notes", [])),
        "\n".join(getattr(bp, "application_conditions", [])),
        "\n".join(getattr(bp, "coordinate_guide", [])),
    ])
    return diag, bp, app, not_app, all_text


FINAL_MICRO_PATCH_CASES = [
    {
        "problem": "There is slipping at the point of contact as the cylinder rolls.",
        "semantic": {"slip_present": True, "explicit_pure_rolling": False},
        "expected": ["미끄럼"],
        "must_app": ["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"],
        "must_not_app": ["v_G = ωR", "a_G = αR"],
        "must_not_all": ["순수 구름 운동\n"],
        "not_app": ["v_G = ωR", "a_G = αR"],
    },
    {
        "problem": "the rolling disk has slip at the contact point.",
        "semantic": {"slip_present": True, "explicit_pure_rolling": False},
        "expected": ["미끄럼"],
        "must_app": ["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"],
        "must_not_app": ["v_G = ωR", "a_G = αR"],
        "not_app": ["v_G = ωR", "a_G = αR"],
    },
    {
        "problem": "no slip exists at the contact point while the wheel rolls.",
        "semantic": {"slip_present": False, "explicit_pure_rolling": True},
        "expected": ["순수 구름"],
        "must_app": ["v_G = ωR", "a_G = αR"],
        "must_not_app": ["f_k = μ_kN", "적용 불가"],
        "must_not_all": ["미끄럼을 동반한 구름 운동", "v_G = ωR 적용 불가", "a_G = αR 적용 불가"],
    },
    {
        "problem": "there is no slip at the point of contact as the cylinder rolls.",
        "semantic": {"slip_present": False, "explicit_pure_rolling": True},
        "expected": ["순수 구름"],
        "must_app": ["v_G = ωR", "a_G = αR"],
        "must_not_app": ["f_k = μ_kN", "적용 불가"],
        "must_not_all": ["미끄럼을 동반한 구름 운동", "v_G = ωR 적용 불가", "a_G = αR 적용 불가"],
    },
    {
        "problem": "the disk has no point-of-contact slip while rolling.",
        "semantic": {"slip_present": False, "explicit_pure_rolling": True},
        "expected": ["순수 구름"],
        "must_app": ["v_G = ωR", "a_G = αR"],
        "must_not_app": ["f_k = μ_kN", "적용 불가"],
        "must_not_all": ["미끄럼을 동반한 구름 운동", "v_G = ωR 적용 불가", "a_G = αR 적용 불가"],
    },
    {
        "problem": "bob on cord follows a cone-shaped trajectory",
        "semantic": {"conical_explicit": True},
        "expected": ["원뿔진자"],
        "must_app": ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"],
        "must_not_app": ["ΣM_G = I_Gα"],
    },
    {
        "problem": "mass attached to string moves in a cone shaped path",
        "semantic": {"conical_explicit": True},
        "expected": ["원뿔진자"],
        "must_app": ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"],
        "must_not_app": ["ΣM_G = I_Gα"],
    },
    {
        "problem": "끈이 기울어진 채 물체가 수평 원을 그린다.",
        "semantic": {"conical_structural": True},
        "expected": ["원뿔진자"],
        "must_app": ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"],
        "must_not_app": ["ΣM_G = I_Gα"],
    },
    {
        "problem": "inclined road curve minimum permissible speed with friction",
        "semantic": {"banked_curve": True, "min_speed": True, "friction_present": True},
        "expected": ["경사진 커브", "최소속도"],
        "must_app": ["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"],
        "must_not_app": ["N = mg", "μ_s ≥ v²/(gR)"],
    },
    {
        "problem": "banked curve minimum allowed velocity with static friction",
        "semantic": {"banked_curve": True, "min_speed": True, "friction_present": True},
        "expected": ["경사진 커브", "최소속도"],
        "must_app": ["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"],
        "must_not_app": ["N = mg", "μ_s ≥ v²/(gR)"],
    },
    {
        "problem": "canted turn lower permissible velocity with coefficient of friction",
        "semantic": {"banked_curve": True, "min_speed": True, "friction_present": True},
        "expected": ["경사진 커브", "최소속도"],
        "must_app": ["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"],
        "must_not_app": ["N = mg", "μ_s ≥ v²/(gR)"],
    },
    {
        "problem": "커브가 경사져 있고 마찰이 있을 때 최대 허용 속도",
        "semantic": {"banked_curve": True, "max_speed": True, "friction_present": True},
        "expected": ["경사진 커브", "최대속도"],
        "must_app": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
        "must_not_app": ["N = mg", "μ_s ≥ v²/(gR)"],
    },
    {
        "problem": "커브가 경사져 있고 마찰이 있을 때 최소 허용 속도",
        "semantic": {"banked_curve": True, "min_speed": True, "friction_present": True},
        "expected": ["경사진 커브", "최소속도"],
        "must_app": ["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"],
        "must_not_app": ["N = mg", "μ_s ≥ v²/(gR)"],
    },
    {
        "problem": "the particle coords are <3t, 2t^2>; find velocity",
        "semantic": {"cartesian_position_vector": True, "polar_motion": False},
        "expected": ["위치 함수"],
        "must_app": ["r(t) = x(t)i + y(t)j", "v(t) = dr/dt"],
        "must_not_app": ["e_r", "e_θ", "theta_dot"],
    },
    {
        "problem": "the coordinates of the particle are (3t, 2t^2), find v and a",
        "semantic": {"cartesian_position_vector": True, "polar_motion": False},
        "expected": ["위치 함수"],
        "must_app": ["r(t) = x(t)i + y(t)j", "v(t) = dr/dt", "a(t) = d²r/dt²"],
        "must_not_app": ["e_r", "e_θ", "theta_dot"],
    },
    {
        "problem": "A block on a smooth horizontal plane is connected to a hanging block over a pulley.",
        "semantic": {"frictionless": True, "horizontal_table": True, "hanging_mass": True, "pulley": True},
        "expected": ["수평면 블록", "매달린"],
        "must_app": ["f = 0", "T = m_Aa", "m_Bg - T = m_Ba"],
        "must_not_app": ["f = μN_A", "T - f = m_Aa"],
    },
]


@pytest.mark.parametrize("case", FINAL_MICRO_PATCH_CASES)
def test_final_acceptance_micro_patch_cases(case):
    sem = semantic_flags(case["problem"])
    for attr, expected in case.get("semantic", {}).items():
        assert getattr(sem, attr) is expected, f"semantic flag {attr} mismatch for {case['problem']}: {sem}"

    diag, bp, app, not_app, all_text = diagnose(case["problem"])
    assert getattr(bp, "forbidden_formula_guard_applied", False), case["problem"]
    assert getattr(bp, "consistency_check_passed", False), case["problem"]
    assert app.strip(), f"applicable equations must not be empty for {case['problem']}\n{all_text}"

    for needle in case.get("expected", []):
        assert needle in all_text, f"{needle!r} missing from output for {case['problem']}\n{all_text}"
    for needle in case.get("must_app", []):
        assert needle in app, f"{needle!r} missing from applicable equations for {case['problem']}\nAPP={app}\nALL={all_text}"
    for needle in case.get("must_not_app", []):
        assert needle not in app, f"{needle!r} must not be applicable for {case['problem']}\nAPP={app}"
    for needle in case.get("not_app", []):
        assert needle in not_app, f"{needle!r} missing from not-applicable equations for {case['problem']}\nNOT={not_app}\nALL={all_text}"
    for needle in case.get("must_not_all", []):
        assert needle not in all_text, f"{needle!r} should not appear for {case['problem']}\nALL={all_text}"
