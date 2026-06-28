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
        "\n".join(getattr(bp, "coordinate_guide", [])),
        "\n".join(getattr(bp, "application_conditions", [])),
    ])
    return diag, bp, app, not_app, all_text


ONTOLOGY_REGRESSION_CASES = [
    {
        "problem": "A disk rolls without skidding down the incline.",
        "expected_problem_type": "순수 구름",
        "must_include": ["v_G = ωR", "a_G = αR"],
        "must_not_app": ["적용 불가", "f_k = μ_kN"],
        "must_not_all": ["미끄럼을 동반한 구름 운동"],
        "rolling_mode": "pure_rolling",
    },
    {
        "problem": "The wheel is not slipping as it rolls.",
        "expected_problem_type": "순수 구름",
        "must_include": ["v_G = ωR", "a_G = αR"],
        "must_not_app": ["적용 불가"],
        "rolling_mode": "pure_rolling",
    },
    {
        "problem": "The cylinder slips while rolling down the plane.",
        "expected_problem_type": "미끄럼",
        "must_include": ["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"],
        "must_not_app": ["v_G = ωR", "a_G = αR"],
        "must_include_not": ["v_G = ωR", "적용식으로 사용 불가"],
        "rolling_mode": "sliding_rotation",
    },
    {
        "problem": "The cylinder rolls, but there is slip at the contact point.",
        "expected_problem_type": "미끄럼",
        "must_include": ["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"],
        "must_not_app": ["v_G = ωR", "a_G = αR"],
        "rolling_mode": "sliding_rotation",
    },
    {
        "problem": "The wheel is rolling but not slipping.",
        "expected_problem_type": "순수 구름",
        "must_include": ["v_G = ωR", "a_G = αR"],
        "must_not_app": ["적용 불가"],
        "rolling_mode": "pure_rolling",
    },
    {
        "problem": "vehicle on a slanted curve with static friction, fastest speed before sliding outward",
        "expected_problem_type": "경사진 커브 최대속도",
        "must_include": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
        "must_not_app": ["N = mg", "μ_s ≥ v²/(gR)", "v_G = ωR"],
    },
    {
        "problem": "마찰 있는 뱅크 도로에서 최고 속력",
        "expected_problem_type": "경사진 커브 최대속도",
        "must_include": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
    },
    {
        "problem": "마찰 있는 뱅크 도로에서 최저 속력",
        "expected_problem_type": "경사진 커브 최소속도",
        "must_include": ["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"],
    },
    {
        "problem": "경사진 커브에서 가장 큰 속력은? μ_s가 주어짐",
        "expected_problem_type": "경사진 커브 최대속도",
        "must_include": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
        "must_not_app": ["N = mg", "μ_s ≥ v²/(gR)"],
    },
    {
        "problem": "경사진 도로 커브에서 가장 작은 속력은? 마찰계수 있음",
        "expected_problem_type": "경사진 커브 최소속도",
        "must_include": ["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"],
    },
    {
        "problem": "자동차가 경사진 커브에서 바깥쪽으로 미끄러지기 직전의 속력",
        "expected_problem_type": "경사진 커브 최대속도",
        "must_include": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
        "must_not_app": ["v_G = ωR", "a_G = αR"],
    },
    {
        "problem": "자동차가 경사진 커브에서 안쪽으로 미끄러지기 직전의 속력",
        "expected_problem_type": "경사진 커브 최소속도",
        "must_include": ["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"],
    },
    {
        "problem": "bob tied to a cord moves like a cone",
        "expected_problem_type": "원뿔진자",
        "must_include": ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"],
        "must_not_app": ["ΣM_G = I_Gα"],
    },
    {
        "problem": "끈과 수직선이 각도를 이루며 물체가 수평 원운동한다",
        "expected_problem_type": "원뿔진자",
        "must_include": ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"],
        "must_not_app": ["ΣM_G = I_Gα"],
    },
    {
        "problem": "r vector equals 3t i-hat plus 2t^2 j-hat, compute acceleration",
        "expected_problem_type": "위치 함수",
        "expected_coordinate_system": "직교좌표",
        "must_include": ["r(t) = x(t)i + y(t)j", "v(t) = dr/dt", "a(t) = d²r/dt²"],
        "must_not_app": ["e_r", "e_θ", "theta_dot"],
    },
    {
        "problem": "particle has position (3t, 2t^2), find velocity",
        "expected_problem_type": "위치 함수",
        "expected_coordinate_system": "직교좌표",
        "must_include": ["r(t) = x(t)i + y(t)j", "v(t) = dr/dt", "a(t) = d²r/dt²"],
        "must_not_app": ["e_r", "e_θ"],
    },
]


@pytest.mark.parametrize("case", ONTOLOGY_REGRESSION_CASES)
def test_domain_ontology_expression_groups(case):
    diag, bp, app, not_app, all_text = run_case(case["problem"])
    assert getattr(bp, "forbidden_formula_guard_applied", False), f"guard flag missing for {case['problem']}"
    assert getattr(bp, "consistency_check_passed", False), f"consistency flag missing for {case['problem']}"
    assert app.strip(), f"applicable equations must not be empty for {case['problem']}\n{all_text}"
    assert case["expected_problem_type"] in all_text, f"expected type {case['expected_problem_type']} missing\n{all_text}"
    if coord := case.get("expected_coordinate_system"):
        assert coord in all_text, f"coordinate system {coord} missing\n{all_text}"
    for needle in case.get("must_include", []):
        assert needle in app or needle in all_text, f"{needle!r} missing for {case['problem']}\nAPP={app}\nALL={all_text}"
    for needle in case.get("must_include_not", []):
        assert needle in not_app, f"{needle!r} missing from not_applicable for {case['problem']}\nNOT={not_app}"
    for needle in case.get("must_not_app", []):
        assert needle not in app, f"{needle!r} should not be applicable for {case['problem']}\nAPP={app}"
    for needle in case.get("must_not_all", []):
        assert needle not in all_text, f"{needle!r} should not appear for {case['problem']}\nALL={all_text}"
