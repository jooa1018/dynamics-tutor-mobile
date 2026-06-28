from __future__ import annotations

import pytest

from dynamics_core.feedback import build_diagnosis
from dynamics_core.parser import analyze_text
from dynamics_core.semantic_normalizer import semantic_flags
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


DOC_CODE_ALIGNMENT_CASES = [
    {
        "problem": "A wheel rolls without any skidding down a ramp.",
        "expected_problem_type": "순수 구름",
        "expected_rolling_mode": "pure_rolling",
        "must_include_app": ["v_G = ωR", "a_G = αR"],
        "must_not_app": ["적용 불가", "f_k = μ_kN"],
        "must_not_all": ["미끄럼을 동반한 구름 운동", "미끄러짐이 있는데 v=ωR"],
    },
    {
        "problem": "The disk rolls and does not skid.",
        "expected_problem_type": "순수 구름",
        "expected_rolling_mode": "pure_rolling",
        "must_include_app": ["v_G = ωR", "a_G = αR"],
        "must_not_app": ["적용 불가"],
        "must_not_all": ["미끄럼을 동반한 구름 운동"],
    },
    {
        "problem": "The disk does not skid while rolling.",
        "expected_problem_type": "순수 구름",
        "expected_rolling_mode": "pure_rolling",
        "must_include_app": ["v_G = ωR", "a_G = αR"],
        "must_not_app": ["적용 불가"],
    },
    {
        "problem": "원반이 skid 없이 굴러간다.",
        "expected_problem_type": "순수 구름",
        "expected_rolling_mode": "pure_rolling",
        "must_include_app": ["v_G = ωR", "a_G = αR"],
        "must_not_app": ["적용 불가"],
    },
    {
        "problem": "mass on a string traces a conical path",
        "expected_problem_type": "원뿔진자",
        "must_include_app": ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"],
        "must_not_app": ["ΣM_G = I_Gα"],
    },
    {
        "problem": "a bob attached to a string sweeps out a cone",
        "expected_problem_type": "원뿔진자",
        "must_include_app": ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"],
        "must_not_app": ["ΣM_G = I_Gα"],
    },
    {
        "problem": "car on an inclined roadway curve, upper speed limit with static friction",
        "expected_problem_type": "경사진 커브 최대속도",
        "must_include_app": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
        "must_not_app": ["N = mg", "μ_s ≥ v²/(gR)", "v_G = ωR"],
    },
    {
        "problem": "sloped turn maximum permissible velocity with mu_s",
        "expected_problem_type": "경사진 커브 최대속도",
        "must_include_app": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
        "must_not_app": ["N = mg", "μ_s ≥ v²/(gR)"],
    },
    {
        "problem": "bead on circular track at lower most point find normal force",
        "expected_problem_type": "수직 원운동 최저점",
        "expected_force_symbol": "N",
        "must_include_app": ["N - mg = mv²/R", "N = mg + mv²/R"],
        "must_not_app": ["T - mg = mv²/R", "N - mg cosθ = mv²/R"],
    },
    {
        "problem": "원형 트랙 제일 아래에서 법선반력",
        "expected_problem_type": "수직 원운동 최저점",
        "expected_force_symbol": "N",
        "must_include_app": ["N - mg = mv²/R", "N = mg + mv²/R"],
        "must_not_app": ["T - mg = mv²/R", "N - mg cosθ = mv²/R"],
    },
    {
        "problem": "particle position equals (3t, 2t^2); compute acceleration",
        "expected_problem_type": "위치 함수",
        "expected_coordinate_system": "cartesian",
        "must_include_app": ["r(t) = x(t)i + y(t)j", "v(t) = dr/dt", "a(t) = d²r/dt²"],
        "must_not_app": ["e_r", "e_θ", "theta_dot"],
    },
]


@pytest.mark.parametrize("case", DOC_CODE_ALIGNMENT_CASES)
def test_docs_glossary_examples_match_runtime_output(case):
    diag, bp, app, not_app, all_text = run_case(case["problem"])
    sem = semantic_flags(case["problem"])
    assert getattr(bp, "forbidden_formula_guard_applied", False), case["problem"]
    assert getattr(bp, "consistency_check_passed", False), case["problem"]
    assert app.strip(), f"applicable equations must not be empty for {case['problem']}\n{all_text}"
    assert case["expected_problem_type"] in all_text, f"expected {case['expected_problem_type']} missing\n{all_text}"

    if case.get("expected_rolling_mode") == "pure_rolling":
        assert sem.explicit_pure_rolling and not sem.slip_present
    if case.get("expected_coordinate_system") == "cartesian":
        assert sem.cartesian_position_vector and not sem.polar_motion
    if case.get("expected_force_symbol") == "N":
        assert "N" in app and "T - mg" not in app

    for needle in case.get("must_include_app", []):
        assert needle in app, f"{needle!r} missing from applicable equations for {case['problem']}\nAPP={app}\nALL={all_text}"
    for needle in case.get("must_not_app", []):
        assert needle not in app, f"{needle!r} should not be applicable for {case['problem']}\nAPP={app}"
    for needle in case.get("must_not_all", []):
        assert needle not in all_text, f"{needle!r} should not appear for {case['problem']}\nALL={all_text}"


def test_pure_rolling_outputs_do_not_contain_contradictory_slip_warning():
    pure_cases = [
        "A wheel rolls without any skidding down a ramp.",
        "The disk rolls and does not skid.",
        "The disk does not skid while rolling.",
        "원반이 skid 없이 굴러간다.",
    ]
    contradictory = [
        "미끄러짐이 있는데 v=ωR",
        "미끄러짐이 있는데 v_G = ωR",
        "미끄럼이 있으면 v_G = ωR 사용 불가",
        "v_G = ωR 적용 불가",
        "a_G = αR 적용 불가",
    ]
    for problem in pure_cases:
        _, bp, app, not_app, all_text = run_case(problem)
        for phrase in contradictory:
            assert phrase not in all_text, f"contradictory pure-rolling warning {phrase!r} in {problem}\n{all_text}"
        assert "v_G = ωR" in app and "a_G = αR" in app
