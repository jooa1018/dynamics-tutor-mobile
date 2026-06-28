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
    ])
    return diag, bp, app, not_app, all_text


CASES = [
    {
        "problem": "The contact point has slip while the disk rolls.",
        "must_all": ["미끄럼", "접촉점"],
        "must_app": ["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"],
        "must_not_app": ["v_G = ωR", "a_G = αR"],
        "must_not_all": ["순수 구름 운동\n"],
        "semantic": {"slip_present": True, "explicit_pure_rolling": False},
    },
    {
        "problem": "원통이 스키딩하며 굴러간다.",
        "must_all": ["미끄럼"],
        "must_app": ["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"],
        "must_not_app": ["v_G = ωR", "a_G = αR"],
        "semantic": {"slip_present": True, "explicit_pure_rolling": False},
    },
    {
        "problem": "a bob on a string moves along a conical trajectory",
        "must_all": ["원뿔진자"],
        "must_app": ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"],
        "must_not_app": ["ΣM_G = I_Gα"],
        "semantic": {"conical_explicit": True},
    },
    {
        "problem": "a particle tied to a string describes a cone",
        "must_all": ["원뿔진자"],
        "must_app": ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"],
        "must_not_app": ["ΣM_G = I_Gα"],
        "semantic": {"conical_explicit": True},
    },
    {
        "problem": "경사진 곡선 도로에서 최대 허용 속력, μ_s",
        "must_all": ["경사진 커브", "최대속도"],
        "must_app": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
        "must_not_app": ["N = mg", "μ_s ≥ v²/(gR)"],
        "semantic": {"banked_curve": True, "max_speed": True},
    },
    {
        "problem": "경사진 곡선 도로에서 최소 허용 속력, μ_s",
        "must_all": ["경사진 커브", "최소속도"],
        "must_app": ["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"],
        "must_not_app": ["N = mg", "μ_s ≥ v²/(gR)"],
        "semantic": {"banked_curve": True, "min_speed": True},
    },
    {
        "problem": "particle position is equal to (3t, 2t^2), find velocity",
        "must_all": ["위치 함수"],
        "must_app": ["r(t) = x(t)i + y(t)j", "v(t) = dr/dt"],
        "must_not_app": ["e_r", "e_θ", "theta_dot"],
        "semantic": {"cartesian_position_vector": True, "polar_motion": False},
    },
    {
        "problem": "the particle’s coordinates are <3t, 2t^2>; compute v",
        "must_all": ["위치 함수"],
        "must_app": ["r(t) = x(t)i + y(t)j", "v(t) = dr/dt"],
        "must_not_app": ["e_r", "e_θ", "theta_dot"],
        "semantic": {"cartesian_position_vector": True, "polar_motion": False},
    },
]


@pytest.mark.parametrize("case", CASES)
def test_final_user_requested_nl_residuals(case):
    sem = semantic_flags(case["problem"])
    for attr, expected in case.get("semantic", {}).items():
        assert getattr(sem, attr) is expected, f"semantic flag {attr} mismatch for {case['problem']}: {sem}"

    diag, bp, app, not_app, all_text = diagnose(case["problem"])
    assert getattr(bp, "forbidden_formula_guard_applied", False), case["problem"]
    assert getattr(bp, "consistency_check_passed", False), case["problem"]
    assert app.strip(), f"applicable equations must not be empty for {case['problem']}\n{all_text}"

    for needle in case.get("must_all", []):
        assert needle in all_text, f"{needle!r} missing from output for {case['problem']}\n{all_text}"
    for needle in case.get("must_app", []):
        assert needle in app, f"{needle!r} missing from applicable equations for {case['problem']}\nAPP={app}\nALL={all_text}"
    for needle in case.get("must_not_app", []):
        assert needle not in app, f"{needle!r} must not be in applicable equations for {case['problem']}\nAPP={app}"
    for needle in case.get("must_not_all", []):
        assert needle not in all_text, f"{needle!r} must not appear in output for {case['problem']}\nALL={all_text}"
