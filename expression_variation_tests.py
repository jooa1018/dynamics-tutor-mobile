"""
표현 변형 견고성 회귀 테스트.
실행: python expression_variation_tests.py

검증 목표:
- 같은 물리 상황을 자연스럽게 다르게 표현해도 같은 전문가 템플릿으로 분류한다.
- 적용식(applicable_equations)과 비적용식(not_applicable_equations)을 영역별로 검증한다.
- 금지식이 전체 출력에 등장하더라도 적용식 영역에 있으면 실패, 비적용/주의 영역이면 허용한다.
"""
from __future__ import annotations

from typing import Iterable, Sequence

from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy
from dynamics_core.feedback import build_diagnosis


def diagnose(problem: str):
    features = analyze_text(problem)
    rec = recommend_strategy(features, "자동 추정")
    return build_diagnosis(problem, "", "자동 추정", features, rec)


def joined(items: Iterable[str]) -> str:
    return "\n".join(str(x) for x in items)


def assert_in_area(problem: str, area: Sequence[str], fragments: Iterable[str], label: str) -> None:
    text = joined(area)
    missing = [frag for frag in fragments if frag not in text]
    assert not missing, f"{label}: missing {missing}\nproblem={problem}\narea=\n{text}"


def assert_not_in_area(problem: str, area: Sequence[str], fragments: Iterable[str], label: str) -> None:
    text = joined(area)
    bad = [frag for frag in fragments if frag in text]
    assert not bad, f"{label}: forbidden fragments found {bad}\nproblem={problem}\narea=\n{text}"


def check_case(case: dict) -> None:
    d = diagnose(case["problem"])
    bp = d.blueprint
    problem = case["problem"]
    if "type_contains" in case:
        assert case["type_contains"] in d.problem_model.problem_type, f"type mismatch: {d.problem_model.problem_type}\nproblem={problem}"
    assert_in_area(problem, bp.applicable_equations, case.get("must_applicable", []), "applicable_equations")
    assert_not_in_area(problem, bp.applicable_equations, case.get("forbidden_applicable", []), "applicable_equations")
    assert_in_area(problem, bp.not_applicable_equations, case.get("must_not_applicable", []), "not_applicable_equations")
    assert_in_area(problem, bp.cautions, case.get("must_caution", []), "cautions")
    assert_in_area(problem, bp.auxiliary_equations, case.get("must_auxiliary", []), "auxiliary_equations")
    assert_in_area(problem, bp.suppressed_templates, case.get("must_suppress", []), "suppressed_templates")
    assert_in_area(problem, bp.ambiguity_notes, case.get("must_ambiguity", []), "ambiguity_notes")


EXPRESSION_VARIATION_CASES = [
    {
        "problem": "경사각 θ인 커브에서 자동차가 미끄러지지 않고 돌 수 있는 최대 속력을 구하라.",
        "type_contains": "최대속도",
        "must_applicable": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
        "forbidden_applicable": ["N = mg", "μ_s ≥ v²/(gR)", "tanθ = v²/(gR)"],
        "must_not_applicable": ["N = mg", "μ_s ≥ v²/(gR)", "tanθ = v²/(gR)"],
    },
    {
        "problem": "마찰이 있는 뱅크 커브에서 허용 가능한 최대 속력을 구하라.",
        "type_contains": "최대속도",
        "must_applicable": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
        "forbidden_applicable": ["N = mg", "μ_s ≥ v²/(gR)", "tanθ = v²/(gR)"],
    },
    {
        "problem": "마찰이 있는 경사 커브에서 아래로 미끄러지지 않는 최소 속력을 구하라.",
        "type_contains": "최소속도",
        "must_applicable": ["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"],
        "forbidden_applicable": ["N = mg", "μ_s ≥ v²/(gR)", "tanθ = v²/(gR)"],
    },
    {
        "problem": "줄에 매단 물체가 수평면에서 원을 그리며 회전하고 줄이 수직과 θ를 이룬다.",
        "type_contains": "원뿔진자",
        "must_applicable": ["T cosθ = mg", "T sinθ = mω²r"],
        "must_auxiliary": ["r = L sinθ"],
        "forbidden_applicable": ["ΣM_G = I_Gα"],
        "must_not_applicable": ["ΣM_G = I_Gα"],
    },
    {
        "problem": "끈에 매단 물체가 수평면에서 원을 그리며 돈다. 각도 기준은 그림에서 확인해야 한다.",
        "type_contains": "원뿔진자 가능성",
        "must_ambiguity": ["원뿔진자 가능성 있음"],
        "forbidden_applicable": ["ΣM_G = I_Gα"],
    },
    {
        "problem": "원통이 경사면을 미끄러지며 내려가고 회전도 한다.",
        "type_contains": "미끄럼",
        "must_applicable": ["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"],
        "forbidden_applicable": ["v_G = ωR", "a_G = αR"],
        "must_not_applicable": ["v_G = ωR", "a_G = αR"],
        "must_suppress": ["pure_rolling"],
    },
    {
        "problem": "원통이 rolling with slip 상태로 경사면을 내려간다.",
        "type_contains": "미끄럼",
        "must_applicable": ["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"],
        "forbidden_applicable": ["v_G = ωR", "a_G = αR"],
    },
    {
        "problem": "끈에 매단 물체가 수직 원운동을 한다. 가장 낮은 위치에서 장력을 구하라.",
        "type_contains": "최저점",
        "must_applicable": ["T - mg = mv²/R", "T = mg + mv²/R"],
        "forbidden_applicable": ["N - mg = mv²/R", "v_min = √(gR)"],
        "must_not_applicable": ["v_min = √(gR)"],
    },
    {
        "problem": "줄에 매단 물체가 vertical circle을 하고 bottom에서 tension을 구하라.",
        "type_contains": "최저점",
        "must_applicable": ["T - mg = mv²/R", "T = mg + mv²/R"],
        "forbidden_applicable": ["N - mg = mv²/R", "v_min = √(gR)"],
    },
    {
        "problem": "Block A is on a smooth horizontal table and connected to hanging block B over a pulley.",
        "type_contains": "수평면 블록",
        "must_applicable": ["f = 0", "T = m_Aa", "m_Bg - T = m_Ba"],
        "forbidden_applicable": ["f = μN_A", "T - f = m_Aa"],
        "must_not_applicable": ["f = μN_A", "T - f = m_Aa"],
    },
    {
        "problem": "질점의 위치가 r(t) = 3t i + 2t² j 로 주어진다. 속도와 가속도를 구하라.",
        "type_contains": "위치 함수",
        "must_applicable": ["r(t) = x(t)i + y(t)j", "v(t) = dr/dt", "a(t) = d²r/dt²"],
        "forbidden_applicable": ["e_r", "e_θ", "r theta_dot", "r theta_dot²"],
    },
    {
        "problem": "입자의 position vector r(t)=4t î + t² ĵ 로 주어진다.",
        "type_contains": "위치 함수",
        "must_applicable": ["r(t) = x(t)i + y(t)j", "v(t) = dr/dt", "a(t) = d²r/dt²"],
        "forbidden_applicable": ["e_r", "e_θ"],
    },
    {
        "problem": "총알이 회전판의 가장자리에 박힌 후 회전판과 함께 고정축을 중심으로 돈다.",
        "type_contains": "탄환-원판",
        "must_applicable": ["H_O(before) = H_O(after)", "m_bvr = I_totalω", "탄환이 박히면 강체와 함께 회전"],
        "must_caution": ["선운동량 보존"],
        "forbidden_applicable": ["m1v1i + m2v2i = m1v1f + m2v2f"],
        "must_not_applicable": ["m1v1i + m2v2i = m1v1f + m2v2f"],
    },
]


def test_expression_variation_cases() -> None:
    assert len(EXPRESSION_VARIATION_CASES) >= 8
    for case in EXPRESSION_VARIATION_CASES:
        check_case(case)


def run_all() -> None:
    test_expression_variation_cases()


if __name__ == "__main__":
    run_all()
    print("OK: expression variation tests passed — robust natural-language variants for final expert templates")
