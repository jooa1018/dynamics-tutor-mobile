"""
4차 복합 템플릿 회귀 테스트.
실행: python fourth_regression_tests.py

핵심 원칙:
- applicable_equations: 이 문제에서 실제로 적용할 식만 들어가야 함
- not_applicable_equations/cautions: 쓰면 안 되는 식 또는 조건부 식이 설명과 함께 들어갈 수 있음
- suppressed_templates: 왜 일반 템플릿을 배제했는지 추적 가능해야 함
"""
from __future__ import annotations

from typing import Iterable, List, Sequence

from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy
from dynamics_core.feedback import build_diagnosis


def diagnose(problem: str, goal: str = "자동 추정"):
    features = analyze_text(problem)
    rec = recommend_strategy(features, goal)
    return build_diagnosis(problem, "", goal, features, rec)


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
    d = diagnose(case["problem"], case.get("goal", "자동 추정"))
    bp = d.blueprint
    problem = case["problem"]
    if "type_contains" in case:
        assert case["type_contains"] in d.problem_model.problem_type, f"type mismatch: {d.problem_model.problem_type}\nproblem={problem}"
    assert_in_area(problem, bp.applicable_equations, case.get("must_applicable", []), "applicable_equations")
    assert_not_in_area(problem, bp.applicable_equations, case.get("forbidden_applicable", []), "applicable_equations")
    assert_in_area(problem, bp.not_applicable_equations, case.get("must_not_applicable", []), "not_applicable_equations")
    assert_in_area(problem, bp.cautions, case.get("must_caution", []), "cautions")
    assert_in_area(problem, bp.suppressed_templates, case.get("must_suppress", []), "suppressed_templates")
    assert_in_area(problem, bp.ambiguity_notes, case.get("must_ambiguity", []), "ambiguity_notes")


COMPLEX_CASES: List[dict] = [
    {
        "problem": "질량 10 kg인 블록 A가 수평면 위에 있고, 질량 5 kg인 물체 B가 도르래에 매달려 있다. 수평면의 마찰계수는 0.2이다. 가속도와 장력을 구하라.",
        "type_contains": "수평면 블록",
        "must_applicable": ["T - f = m_Aa", "N_A = m_Ag", "f = μN_A", "m_Bg - T = m_Ba"],
        "forbidden_applicable": ["m_Ag - T = m_Aa", "m1g - T = m1a"],
        "must_not_applicable": ["m_Ag - T = m_Aa"],
        "must_suppress": ["ideal_atwood"],
    },
    {
        "problem": "질량 m인 블록이 각도 θ인 경사면 위에 있고, 줄로 매달린 질량 M과 도르래로 연결되어 있다. 마찰계수 μ가 있을 때 가속도를 구하라.",
        "type_contains": "경사면 블록",
        "must_applicable": ["N = mg cosθ", "f = μN", "T - mg sinθ - f = ma", "Mg - T = Ma"],
        "forbidden_applicable": ["m1g - T = m1a"],
        "must_caution": ["성분 분해"],
        "must_suppress": ["ideal_atwood"],
    },
    {
        "problem": "관성모멘트 I인 질량 있는 도르래에 두 물체가 연결되어 있고 줄은 미끄러지지 않는다. 두 물체의 가속도를 구하라.",
        "type_contains": "질량 있는 도르래",
        "must_applicable": ["(T1 - T2)R = Iα", "a = αR"],
        "forbidden_applicable": ["T1 = T2", "같은 줄의 장력은 같다"],
        "must_not_applicable": ["T1 = T2"],
        "must_suppress": ["ideal_pulley"],
    },
    {
        "problem": "움직도르래에 매달린 하중을 줄로 끌어올린다. 하중의 가속도를 구하라.",
        "type_contains": "움직도르래",
        "must_applicable": ["2T - mg = ma_load", "a_free = 2a_load"],
        "forbidden_applicable": ["|a1| = |a2|"],
        "must_not_applicable": ["|a1| = |a2|"],
    },
    {
        "problem": "자동차가 반지름 R인 평평한 커브를 속도 v로 돈다. 미끄러지지 않기 위한 최소 마찰계수를 구하라.",
        "type_contains": "평평한 커브",
        "must_applicable": ["N = mg", "f_s = mv²/R", "μ_s ≥ v²/(gR)"],
        "forbidden_applicable": ["N cosθ = mg"],
    },
    {
        "problem": "자동차가 반지름 R인 경사진 커브를 마찰 없이 속도 v로 돈다. 필요한 경사각을 구하라.",
        "type_contains": "경사진 커브",
        "must_applicable": ["N cosθ = mg", "N sinθ = mv²/R", "tanθ = v²/(gR)"],
        "forbidden_applicable": ["N = mg", "μ_s ≥ v²/(gR)"],
        "must_not_applicable": ["N = mg", "μ_s ≥ v²/(gR)"],
        "must_suppress": ["flat_curve"],
    },
    {
        "problem": "질량 m인 물체가 원뿔진자 운동을 한다. 줄의 장력과 각속도를 구하라.",
        "type_contains": "원뿔진자",
        "must_applicable": ["T cosθ = mg", "T sinθ = mω²r"],
        "forbidden_applicable": ["ΣM_G = I_Gα"],
        "must_not_applicable": ["ΣM_G = I_Gα"],
    },
    {
        "problem": "질량 m인 물체가 반지름 R인 수직 원형 트랙의 최고점에서 떨어지지 않기 위한 최소 속도를 구하라.",
        "type_contains": "수직 원운동",
        "must_applicable": ["mg + N = mv²/R", "N = 0", "v_min = √(gR)"],
        "forbidden_applicable": ["N = mg"],
    },
    {
        "problem": "반지름 R인 원통이 미끄러지지 않고 경사면을 굴러 내려간다. 속도를 구하라.",
        "type_contains": "순수 구름",
        "must_applicable": ["mgh = 1/2mv_G²", "v_G = ωR", "a_G = αR"],
        "forbidden_applicable": ["f_k = μ_kN"],
    },
    {
        "problem": "반지름 R인 원통이 거친 경사면을 미끄러지며 굴러 내려간다. 속도를 구하라.",
        "type_contains": "미끄럼",
        "must_applicable": ["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"],
        "forbidden_applicable": ["v_G = ωR", "a_G = αR"],
        "must_not_applicable": ["v_G = ωR", "a_G = αR"],
        "must_suppress": ["pure_rolling"],
    },
    {
        "problem": "입자의 위치가 x=t², y=t³로 주어진다. 속도와 가속도를 구하라.",
        "type_contains": "위치 함수",
        "must_applicable": ["v(t) = dr/dt", "a(t) = d²r/dt²", "dx/dt", "d²x/dt²"],
        "forbidden_applicable": ["v = v0 + at", "s = v0t + 1/2at²"],
        "must_not_applicable": ["v = v0 + at", "s = v0t"],
    },
    {
        "problem": "힘 F = 3x² N이 x=0부터 x=2m까지 작용한다. 속도를 구하라.",
        "type_contains": "위치 의존 힘",
        "must_applicable": ["W = ∫ F(x) dx", "W = ΔT", "∫_{x1}^{x2} F(x) dx"],
        "forbidden_applicable": ["W = Fs"],
        "must_not_applicable": ["W = Fs"],
    },
    {
        "problem": "힘 F(t)가 시간에 따라 변한다. 0초부터 2초까지의 충격량과 속도 변화를 구하라.",
        "type_contains": "시간 의존 힘",
        "must_applicable": ["J = ∫_{t1}^{t2} F(t) dt", "J = Δp", "∫F(t)dt = m(v₂ - v₁)"],
        "forbidden_applicable": ["J = FΔt"],
    },
    {
        "problem": "길이 L인 막대가 벽과 바닥 사이에서 미끄러진다. A점 속도가 주어질 때 B점 속도를 구하라.",
        "type_contains": "벽-바닥 순간중심",
        "must_applicable": ["v_A = ω r_A/IC", "v_B = ω r_B/IC", "v_B = v_A + ω × r_B/A"],
        "forbidden_applicable": ["ΣF = ma_G", "ΣM_G = I_Gα"],
        "must_not_applicable": ["ΣF = ma_G", "ΣM_G = I_Gα"],
    },
    {
        "problem": "핀 P가 회전하는 막대의 슬롯을 따라 미끄러진다. 상대속도식을 세워라.",
        "type_contains": "슬롯/핀",
        "must_applicable": ["v_B = v_A + ω × r_B/A", "슬롯 방향 상대속도"],
        "forbidden_applicable": ["ΣF = ma_G만"],
    },
    {
        "problem": "탄환이 핀으로 고정된 막대 끝에 박힌다. 충돌 직후 각속도를 구하라.",
        "type_contains": "탄환-막대",
        "must_applicable": ["H_O(before) = H_O(after)", "m_b v r = I_total ω"],
        "forbidden_applicable": ["m1v1i + m2v2i = m1v1f + m2v2f"],
        "must_not_applicable": ["m1v1i + m2v2i = m1v1f + m2v2f"],
        "must_suppress": ["one_dimensional"],
    },
    {
        "problem": "질점이 중심 O 주위에서 움직이고 외부 모멘트가 0이다. 각운동량 보존을 이용하라.",
        "type_contains": "각운동량",
        "must_applicable": ["ΣM_O = dH_O/dt", "H_O1 = H_O2", "H_O = r × mv"],
        "forbidden_applicable": ["m1v1i + m2v2i"],
    },
    {
        "problem": "두 물체가 1차원에서 충돌한다. 반발계수 e가 주어졌을 때 충돌 후 속도를 구하라.",
        "type_contains": "충돌",
        "must_applicable": ["m1v1i + m2v2i = m1v1f + m2v2f", "e = (v2f - v1f)/(v1i - v2i)"],
        "forbidden_applicable": ["운동에너지 보존"],
    },
    {
        "problem": "원판이 고정축 O 주위로 회전한다. 각가속도를 구하라.",
        "type_contains": "고정축",
        "must_applicable": ["ΣM_O = I_Oα", "ω² = ω0² + 2αθ"],
        "forbidden_applicable": ["순수 병진운동"],
    },
    {
        "problem": "강체 일반 평면운동에서 질량중심 가속도와 각가속도를 구하라.",
        "type_contains": "일반 평면운동",
        "must_applicable": ["ΣF_x = m a_Gx", "ΣF_y = m a_Gy", "ΣM_G = I_Gα"],
        "forbidden_applicable": ["순수 병진운동"],
    },
]

AMBIGUITY_CASE = {
    "problem": "두 물체가 도르래로 연결되어 있다.",
    "type_contains": "정보 부족",
    "must_applicable": [],
    "forbidden_applicable": ["m1g - T = m1a", "T - m2g = m2a"],
    "must_not_applicable": ["m1g - T = m1a", "T - m2g = m2a"],
    "must_ambiguity": ["물체 배치 정보가 부족"],
}


def test_complex_case_count_and_structured_areas() -> None:
    assert len(COMPLEX_CASES) == 20
    for case in COMPLEX_CASES:
        check_case(case)


def test_ambiguous_problem_does_not_force_template() -> None:
    check_case(AMBIGUITY_CASE)


def run_all() -> None:
    test_complex_case_count_and_structured_areas()
    test_ambiguous_problem_does_not_force_template()


if __name__ == "__main__":
    run_all()
    print("OK: fourth regression tests passed — 20 complex cases, ambiguity handling, and area-aware forbidden-equation checks")
