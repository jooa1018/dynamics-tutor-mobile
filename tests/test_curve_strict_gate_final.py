from __future__ import annotations

import pytest

from dynamics_core.feedback import build_diagnosis
from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy
from dynamics_core.scope_limits import assess_information_sufficiency, question_wizard_for_text


def diagnose(problem: str):
    features = analyze_text(problem, "")
    rec = recommend_strategy(features, "자동 추정")
    diag = build_diagnosis(problem, "", "자동 추정", features, rec, enable_ai_assist=False)
    bp = diag.blueprint
    app = "\n".join(getattr(bp, "applicable_equations", []) or getattr(bp, "governing_equations", []))
    blocked = "\n".join(getattr(bp, "not_applicable_equations", []))
    text = "\n".join([
        getattr(diag.problem_model, "problem_type", ""),
        getattr(bp, "title", ""),
        app,
        blocked,
        "\n".join(getattr(bp, "cautions", [])),
        "\n".join(getattr(bp, "ambiguity_notes", [])),
        "\n".join(getattr(bp, "next_steps", [])),
    ])
    return diag, bp, app, blocked, text


@pytest.mark.parametrize("problem, missing_needles, forbidden_needles", [
    (
        "A car moves on a banked curve. Find maximum speed.",
        ["반지름", "경사각", "정지마찰계수"],
        ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
    ),
    (
        "A car moves on a flat curve. Find maximum speed.",
        ["반지름", "정지마찰계수"],
        ["v_max = √(μ_s g R)", "μ_s ≥ v²/(gR)"],
    ),
    (
        "자동차가 경사진 커브를 돈다. 최대속도를 구하라.",
        ["반지름", "경사각", "정지마찰계수"],
        ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
    ),
    (
        "자동차가 평평한 커브를 돈다. 최대속도를 구하라.",
        ["반지름", "정지마찰계수"],
        ["v_max = √(μ_s g R)", "μ_s ≥ v²/(gR)"],
    ),
    (
        "A car turns on a curve. Find speed.",
        ["평평한", "경사진", "반지름", "마찰"],
        ["v_max = √(μ_s g R)", "tanθ = v²/(gR)"],
    ),
    (
        "A vehicle travels around a circular road. Find maximum speed.",
        ["평평한", "경사진", "반지름", "마찰"],
        ["v_max = √(μ_s g R)", "μ_s ≥ v²/(gR)"],
    ),
])
def test_curve_keyword_only_inputs_are_insufficient(problem, missing_needles, forbidden_needles):
    info = assess_information_sufficiency(problem)
    assert info.status == "insufficient"
    assert info.detected_family == "커브 주행"
    diag, bp, app, blocked, text = diagnose(problem)
    assert "정보 부족" in diag.problem_model.problem_type
    assert app.strip() == ""
    assert getattr(bp, "forbidden_formula_guard_applied", False)
    assert getattr(bp, "consistency_check_passed", False)
    for needle in missing_needles:
        assert needle in text
    for formula in forbidden_needles:
        assert formula not in app
    assert "커브 주행 원운동 문제 후보" in text


@pytest.mark.parametrize("problem, expected", [
    (
        "반지름 R인 평평한 원형 도로에서 정지마찰계수 μ_s일 때, 자동차가 미끄러지기 직전 최대 속도를 구하라.",
        "μ_s ≥ v²/(gR)",
    ),
    (
        "A car moves on a flat curve of radius R with coefficient of static friction μ_s. Find the maximum speed before slipping.",
        "μ_s ≥ v²/(gR)",
    ),
    (
        "반지름 R, 경사각 θ인 마찰 없는 경사진 커브에서 설계속도를 구하라.",
        "tanθ = v²/(gR)",
    ),
    (
        "A car travels on a frictionless banked curve of radius R and bank angle θ. Find the design speed.",
        "tanθ = v²/(gR)",
    ),
    (
        "반지름 R, 경사각 θ, 정지마찰계수 μ_s가 주어진 경사진 커브에서 최대속도를 구하라.",
        "N cosθ - f sinθ = mg",
    ),
    (
        "A car travels on a banked curve of radius R and angle θ with coefficient of static friction μ_s. Find the maximum speed before slipping.",
        "N cosθ - f sinθ = mg",
    ),
])
def test_curve_inputs_with_required_conditions_can_show_formulas(problem, expected):
    info = assess_information_sufficiency(problem)
    assert info.status == "sufficient"
    diag, bp, app, blocked, text = diagnose(problem)
    assert app.strip()
    assert expected in app
    assert "정보 부족" not in diag.problem_model.problem_type


def test_curve_question_wizard_lists_curve_specific_conditions():
    questions = "\n".join(question_wizard_for_text("A car moves on a banked curve. Find maximum speed."))
    for needle in ["평평", "경사", "반지름", "정지마찰계수", "경사각", "최대속도", "미끄러지기 직전"]:
        assert needle in questions
