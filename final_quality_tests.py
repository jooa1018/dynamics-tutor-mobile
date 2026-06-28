"""
최종 품질 보정 테스트.
실행: python final_quality_tests.py

검증 목표:
- 적용식(applicable_equations)에는 실제 적용 가능한 식만 둔다.
- 비적용식(not_applicable_equations)과 주의사항(cautions)은 별도 영역에서 검증한다.
- 4차 이후 남은 7개 조건 분기 보정 사항을 고정 회귀 테스트로 보호한다.
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


FINAL_CORRECTION_CASES = [
    {
        "problem": "마찰 없는 수평면 위 블록 A와 매달린 물체 B가 도르래로 연결되어 있다. 가속도와 장력을 구하라.",
        "type_contains": "수평면 블록",
        "must_applicable": ["f = 0", "T = m_Aa", "m_Bg - T = m_Ba"],
        "forbidden_applicable": ["f = μN_A", "T - f = m_Aa"],
        "must_not_applicable": ["f = μN_A", "T - f = m_Aa"],
    },
    {
        "problem": "매끈한 경사면 위 블록 A가 도르래를 통해 매달린 물체 B와 연결되어 있다. 가속도와 장력을 구하라.",
        "type_contains": "경사면 블록",
        "must_applicable": ["f = 0", "N = mg cosθ", "T - mg sinθ = ma", "Mg - T = Ma"],
        "forbidden_applicable": ["f = μN = μmg cosθ"],
        "must_not_applicable": ["f = μN = μmg cosθ"],
    },
    {
        "problem": "마찰계수 μ가 주어졌지만 마찰을 무시한다. 수평면 위 블록 A와 매달린 물체 B가 도르래로 연결되어 있다.",
        "type_contains": "수평면 블록",
        "must_applicable": ["f = 0", "T = m_Aa"],
        "forbidden_applicable": ["f = μN_A", "T - f = m_Aa"],
        "must_not_applicable": ["f = μN_A"],
    },
    {
        "problem": "마찰이 있는 경사진 커브에서 자동차의 최대속도를 구하라.",
        "type_contains": "최대속도",
        "must_applicable": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
        "forbidden_applicable": ["N = mg", "μ_s ≥ v²/(gR)", "tanθ = v²/(gR)"],
        "must_not_applicable": ["N = mg", "μ_s ≥ v²/(gR)", "tanθ = v²/(gR)"],
    },
    {
        "problem": "마찰이 있는 경사진 커브에서 자동차가 아래로 미끄러지지 않는 최소속도를 구하라.",
        "type_contains": "최소속도",
        "must_applicable": ["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"],
        "forbidden_applicable": ["N = mg", "μ_s ≥ v²/(gR)", "tanθ = v²/(gR)"],
        "must_not_applicable": ["N = mg", "μ_s ≥ v²/(gR)", "tanθ = v²/(gR)"],
    },
    {
        "problem": "길이 L인 줄에 매단 질점이 수평 원운동을 하며 줄은 연직선과 각도 θ를 이룬다. 각속도를 구하라.",
        "type_contains": "원뿔진자",
        "must_applicable": ["T cosθ = mg", "T sinθ = mω²r"],
        "must_auxiliary": ["r = L sinθ"],
        "forbidden_applicable": ["ΣM_G = I_Gα"],
        "must_not_applicable": ["ΣM_G = I_Gα"],
    },
    {
        "problem": "원통이 경사면에서 미끄러져 내려가면서 동시에 회전한다. 마찰계수 μ_k가 주어질 때 가속도를 구하라.",
        "type_contains": "미끄럼",
        "must_applicable": ["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"],
        "forbidden_applicable": ["v_G = ωR", "a_G = αR"],
        "must_not_applicable": ["v_G = ωR", "a_G = αR"],
        "must_suppress": ["pure_rolling"],
    },
    {
        "problem": "입자의 위치벡터가 r(t)=t² i + t³ j 이다. t=2초에서 속도와 가속도를 구하라.",
        "type_contains": "위치 함수",
        "must_applicable": ["r(t) = x(t)i + y(t)j", "v(t) = dr/dt", "a(t) = d²r/dt²"],
        "forbidden_applicable": ["e_r", "e_θ", "r theta_dot", "r theta_dot²"],
        "must_not_applicable": ["v = v0 + at"],
    },
    {
        "problem": "탄환이 원판 가장자리에 박힌 뒤 원판이 고정축 주위로 회전한다. 충돌 직후 각속도를 구하라.",
        "type_contains": "탄환-원판",
        "must_applicable": ["H_O(before) = H_O(after)", "m_bvr = I_totalω"],
        "must_caution": ["선운동량 보존"],
        "forbidden_applicable": ["m1v1i + m2v2i = m1v1f + m2v2f"],
        "must_not_applicable": ["m1v1i + m2v2i = m1v1f + m2v2f"],
    },
    {
        "problem": "줄에 매단 물체가 수직 원운동을 한다. 최저점에서 장력을 구하라.",
        "type_contains": "최저점",
        "must_applicable": ["T - mg = mv²/R", "T = mg + mv²/R"],
        "forbidden_applicable": ["v_min = √(gR)", "최소 조건: T = 0"],
        "must_not_applicable": ["v_min = √(gR)", "최고점"],
    },
    {
        "problem": "줄에 매단 물체가 수직 원운동을 한다. 최고점에서 떨어지지 않기 위한 최소속도를 구하라.",
        "type_contains": "최고점",
        "must_applicable": ["mg + T = mv²/R", "최소 조건: T = 0", "v_min = √(gR)"],
        "forbidden_applicable": ["T - mg = mv²/R"],
        "must_not_applicable": ["T - mg = mv²/R"],
    },
    {
        "problem": "수직 원운동 중 임의 각도 θ에서 줄의 장력을 구하라.",
        "type_contains": "임의 각도",
        "must_applicable": ["T - mg cosθ = mv²/R", "ΣF_t = ma_t"],
        "forbidden_applicable": ["v_min = √(gR)", "N = mg"],
        "must_not_applicable": ["v_min = √(gR)", "N = mg"],
    },
]


def test_final_correction_cases() -> None:
    assert len(FINAL_CORRECTION_CASES) == 12
    for case in FINAL_CORRECTION_CASES:
        check_case(case)


def run_all() -> None:
    test_final_correction_cases()


if __name__ == "__main__":
    run_all()
    print("OK: final quality tests passed — 7 final condition-branch corrections with area-aware checks")
