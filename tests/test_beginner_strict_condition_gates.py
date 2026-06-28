from __future__ import annotations

from pathlib import Path

import pytest

from dynamics_core.feedback import build_diagnosis
from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy
from dynamics_core.scope_limits import assess_information_sufficiency, question_wizard_for_text
from dynamics_core.ui_helpers import equation_explanation
from dynamics_core.storage import save_record, list_records


def diagnose(problem: str):
    features = analyze_text(problem, "")
    rec = recommend_strategy(features, "자동 추정")
    diag = build_diagnosis(problem, "", "자동 추정", features, rec, enable_ai_assist=False)
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
        "\n".join(getattr(bp, "next_steps", [])),
    ])
    return diag, bp, app, blocked, all_text


@pytest.mark.parametrize("problem, family_needles, forbidden_needles", [
    ("블록이 경사면 위에 있다. 가속도를 구하라.", ["경사면", "마찰", "경사각"], ["ΣF_parallel = ma", "f = μN"]),
    ("원운동하는 물체의 장력을 구하라.", ["수평", "수직", "최저점", "최고점"], ["T - mg = mv²/R", "T + mg = mv²/R"]),
    ("원통이 굴러간다. 가속도를 구하라.", ["미끄럼", "접촉점"], ["v_G = ωR", "a_G = αR"]),
    ("A cylinder is rolling. Find acceleration.", ["미끄럼", "접촉점"], ["v_G = ωR", "a_G = αR"]),
    ("A car moves on a curve. Find maximum speed.", ["평평한", "경사진", "마찰계수", "반지름"], ["v_max = √(μ_s g R)", "tanθ = v²/(gR)"]),
    ("공이 원운동한다. 속도를 구하라.", ["반지름", "수평", "수직"], ["구심력을 FBD에 별도 힘으로 추가"]),
])
def test_keyword_only_problems_stop_formula_recommendation(problem, family_needles, forbidden_needles):
    info = assess_information_sufficiency(problem)
    assert info.status == "insufficient"
    diag, bp, app, blocked, all_text = diagnose(problem)
    assert "정보 부족" in diag.problem_model.problem_type
    assert app.strip() == ""
    assert getattr(bp, "forbidden_formula_guard_applied", False)
    assert getattr(bp, "consistency_check_passed", False)
    for needle in family_needles:
        assert needle in all_text
    for needle in forbidden_needles:
        assert needle in blocked


def test_explicit_frictionless_incline_can_show_specific_equation():
    problem = "마찰 없는 경사각 θ의 경사면 위에서 블록이 아래로 미끄러진다. 가속도를 구하라."
    info = assess_information_sufficiency(problem)
    assert info.status == "sufficient"
    diag, bp, app, blocked, all_text = diagnose(problem)
    assert "mg sinθ = ma" in app
    assert "a = g sinθ" in app
    assert "f = μN" not in app


@pytest.mark.parametrize("problem", [
    "원통이 미끄러지지 않고 굴러간다.",
    "A cylinder rolls without slipping.",
    "A disk rolls without slipping down an incline.",
])
def test_explicit_pure_rolling_allowed(problem):
    info = assess_information_sufficiency(problem)
    assert info.status == "sufficient"
    diag, bp, app, blocked, all_text = diagnose(problem)
    assert "순수 구름" in all_text
    assert "v_G = ωR" in app
    assert "a_G = αR" in app
    assert "적용식으로 사용 불가" not in app


@pytest.mark.parametrize("problem", [
    "원통이 미끄러지며 굴러간다.",
    "A cylinder is rolling while slipping.",
    "A disk slips as it rolls.",
])
def test_sliding_rotation_blocks_pure_rolling_equations(problem):
    diag, bp, app, blocked, all_text = diagnose(problem)
    assert "미끄럼" in all_text
    assert "ΣF = ma_G" in app
    assert "ΣM_G = I_Gα" in app
    assert "v_G = ωR" not in app
    assert "a_G = αR" not in app
    assert "v_G = ωR" in blocked
    # Repeated same-meaning warnings should be collapsed for beginner UI.
    assert blocked.count("v_G = ωR") == 1
    assert blocked.count("a_G = αR") == 1


@pytest.mark.parametrize("problem, expected", [
    ("줄에 매단 공이 수직 원운동을 한다. 최저점에서 장력을 구하라.", "T - mg = mv²/R"),
    ("줄에 매단 공이 수직 원운동을 한다. 최고점에서 장력을 구하라.", "mg + T = mv²/R"),
    ("반지름 R인 평평한 원형 도로에서 정지마찰계수 μ_s일 때, 자동차가 미끄러지기 직전 최대 속도를 구하라.", "μ_s ≥ v²/(gR)"),
])
def test_clear_circular_or_curve_cases_still_show_equations(problem, expected):
    info = assess_information_sufficiency(problem)
    assert info.status == "sufficient"
    diag, bp, app, blocked, all_text = diagnose(problem)
    assert app.strip()
    assert expected in app


def test_equation_explanation_patterns_are_beginner_friendly():
    assert "수직방향" in equation_explanation("N_A = m_Ag")
    assert "장력" in equation_explanation("T = m_Aa")
    assert "마찰력" in equation_explanation("f = μN")
    assert "토크" in equation_explanation("ΣM_G = I_Gα")


def test_question_wizard_is_family_specific():
    incline_questions = "\n".join(question_wizard_for_text("블록이 경사면 위에 있다. 가속도를 구하라."))
    pulley_questions = "\n".join(question_wizard_for_text("블록과 매달린 추가 도르래로 연결되어 있다."))
    assert "경사각" in incline_questions and "마찰" in incline_questions
    assert "도르래" in pulley_questions and "가속도" in pulley_questions


def test_storage_auto_wrong_reason_tags(tmp_path: Path):
    db = tmp_path / "records.sqlite3"
    rid = save_record({
        "problem": "원통이 굴러간다. 가속도를 구하라.",
        "problem_type": "정보 부족: 추가 조건 필요",
        "not_applicable_equations": ["v_G = ωR : no slip/without slipping 조건 확인 전 사용 금지"],
        "missing": ["접촉점 미끄럼 여부 확인 필요"],
        "wrong_reasons": [],
    }, path=db)
    records = list_records(path=db)
    assert rid >= 1
    assert records[0]["wrong_reasons"], records[0]
    assert any("구름" in x or "FBD" in x or "조건" in x for x in records[0]["wrong_reasons"])
