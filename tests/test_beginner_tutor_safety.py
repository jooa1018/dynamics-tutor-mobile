from __future__ import annotations

from pathlib import Path

from dynamics_core.feedback import build_diagnosis
from dynamics_core.parser import analyze_text
from dynamics_core.scope_limits import (
    assess_information_sufficiency,
    beginner_scope_summary,
    input_checklist_for_text,
)
from dynamics_core.strategy_engine import recommend_strategy
from dynamics_core.ui_helpers import equation_explanation, forbidden_explanation, beginner_first_equation


def diagnose(problem: str):
    features = analyze_text(problem, "")
    rec = recommend_strategy(features, "자동 추정")
    return build_diagnosis(problem, "", "자동 추정", features, rec, enable_ai_assist=False)


def test_ambiguous_figure_only_input_stops_recommendation():
    problem = "그림과 같은 시스템에서 가속도를 구하라."
    info = assess_information_sufficiency(problem)
    assert info.status == "insufficient"
    assert any("물체" in item or "마찰" in item for item in info.missing_items)
    diagnosis = diagnose(problem)
    assert "정보 부족" in diagnosis.problem_model.problem_type
    assert diagnosis.blueprint.applicable_equations == []
    assert diagnosis.blueprint.not_applicable_equations
    assert "추측" in "\n".join(diagnosis.blueprint.not_applicable_equations + diagnosis.blueprint.cautions)


def test_checklists_are_problem_family_specific():
    pulley_items = input_checklist_for_text("block over pulley with hanging mass")
    incline_items = input_checklist_for_text("block on incline")
    assert any("도르래" in x or "매달" in x for x in pulley_items)
    assert any("경사각" in x for x in incline_items)


def test_beginner_equation_explanations_are_directional_not_formula_only():
    text = equation_explanation("m_B g - T = m_B a")
    assert "아래" in text and "장력" in text and "ΣF" in text
    rolling = equation_explanation("v_G = ωR")
    assert "접촉점" in rolling and "미끄럼" in rolling
    bad = forbidden_explanation("v_G = ωR 적용 불가")
    assert "미끄럼" in bad or "순수 구름" in bad
    assert beginner_first_equation(["", "T - mg = mv²/R"]) == "T - mg = mv²/R"


def test_app_contains_beginner_mode_and_staged_learning_ui():
    text = Path("app.py").read_text(encoding="utf-8")
    for needle in [
        "입문자 모드",
        "render_beginner_result",
        "첫 번째로 세울 식",
        "직접 계산해볼 부분",
        "정보 부족 · 풀이 추천 중단",
    ]:
        assert needle in text


def test_beginner_scope_summary_sets_expectation():
    summary = "\n".join(beginner_scope_summary())
    assert "자동 정답" in summary
    assert "정보가 부족" in summary
    assert "그림" in summary
