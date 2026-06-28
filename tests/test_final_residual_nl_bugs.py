from __future__ import annotations

import pytest

from dynamics_core.feedback import build_diagnosis
from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy


def run_case(problem: str):
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


RESIDUAL_CASES = [
    {
        "problem": "Cylinder rolls without any slipping down the ramp.",
        "all_must": ["순수 구름"],
        "app_must": ["v_G = ωR", "a_G = αR"],
        "app_must_not": ["적용 불가"],
        "all_must_not": ["미끄럼을 동반한 구름 운동"],
    },
    {
        "problem": "The cylinder is rolling while slipping on the plane.",
        "all_must": ["미끄럼"],
        "app_must": ["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"],
        "app_must_not": ["v_G = ωR", "a_G = αR"],
        "not_must": ["v_G = ωR", "적용식으로 사용 불가"],
    },
    {
        "problem": "The cylinder rolls and slips down an incline.",
        "all_must": ["미끄럼"],
        "app_must": ["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"],
        "app_must_not": ["v_G = ωR", "a_G = αR"],
    },
    {
        "problem": "원통이 미끄러지지 않고 회전하며 내려간다.",
        "all_must": ["순수 구름"],
        "app_must": ["v_G = ωR", "a_G = αR"],
        "app_must_not": ["적용 불가"],
    },
    {
        "problem": "원통이 접촉점에서 미끄러지지 않는다.",
        "all_must": ["순수 구름"],
        "app_must": ["v_G = ωR", "a_G = αR"],
        "app_must_not": ["적용 불가"],
    },
    {
        "problem": "car on a sloped curve with friction, find highest speed before sliding up the bank",
        "all_must": ["경사진 커브", "최대속도"],
        "app_must": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
        "app_must_not": ["N = mg", "μ_s ≥ v²/(gR)"],
    },
    {
        "problem": "마찰계수가 있는 경사 도로 커브에서 최고 속도",
        "all_must": ["경사진 커브", "최대속도"],
        "app_must": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
    },
    {
        "problem": "마찰계수가 있는 경사 도로 커브에서 최저 속도",
        "all_must": ["경사진 커브", "최소속도"],
        "app_must": ["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"],
    },
    {
        "problem": "inclined road curve maximum allowable velocity",
        "expect_insufficient": True,
        "all_must": ["정보 부족", "커브 주행", "반지름", "정지마찰계수", "경사각"],
        "app_must": [],
        "app_must_not": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN", "N = mg", "μ_s ≥ v²/(gR)"],
    },
    {
        "problem": "끈에 달린 물체가 원뿔 운동을 한다.",
        "all_must": ["원뿔진자"],
        "app_must": ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"],
        "app_must_not": ["ΣM_G = I_Gα"],
    },
    {
        "problem": "원형 레일의 최하점에서 수직항력",
        "all_must": ["수직 원운동", "최저점", "수직항력"],
        "app_must": ["N - mg = mv²/R", "N = mg + mv²/R"],
        "app_must_not": ["T - mg = mv²/R"],
    },
]


@pytest.mark.parametrize("case", RESIDUAL_CASES)
def test_final_residual_natural_language_bugs(case):
    _, bp, app, not_app, all_text = run_case(case["problem"])
    if case.get("expect_insufficient"):
        assert not app.strip(), f"insufficient case should not show formulas for {case['problem']}\nAPP={app}\nALL={all_text}"
    else:
        assert app.strip(), f"applicable_equations must not be empty for {case['problem']}\nALL={all_text}"
    for needle in case.get("app_must", []):
        assert needle in app, f"{needle!r} missing from applicable_equations for {case['problem']}\nAPP={app}\nALL={all_text}"
    for needle in case.get("not_must", []):
        assert needle in not_app, f"{needle!r} missing from not_applicable_equations for {case['problem']}\nNOT={not_app}"
    for needle in case.get("all_must", []):
        assert needle in all_text, f"{needle!r} missing from final output for {case['problem']}\nALL={all_text}"
    for needle in case.get("app_must_not", []):
        assert needle not in app, f"{needle!r} should not be in applicable_equations for {case['problem']}\nAPP={app}"
    for needle in case.get("all_must_not", []):
        assert needle not in all_text, f"{needle!r} should not be in final output for {case['problem']}\nALL={all_text}"
