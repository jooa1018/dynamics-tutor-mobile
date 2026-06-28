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


ROBUST_CASES = [
    # pure rolling / sliding rotation
    {
        "problem": "A cylinder rolls down an incline without slip.",
        "all_must": ["순수 구름"],
        "app_must": ["v_G = ωR", "a_G = αR"],
        "app_must_not": ["적용 불가", "f_k = μ_kN"],
        "all_must_not": ["미끄럼을 동반한 구름 운동"],
    },
    {
        "problem": "ball rolls on a rough incline, no slip occurs.",
        "all_must": ["순수 구름"],
        "app_must": ["v_G = ωR", "a_G = αR"],
        "app_must_not": ["적용 불가"],
        "all_must_not": ["미끄럼을 동반한 구름 운동"],
    },
    {
        "problem": "ball rolls on rough incline; slipping does not occur.",
        "all_must": ["순수 구름"],
        "app_must": ["v_G = ωR", "a_G = αR"],
        "app_must_not": ["적용 불가"],
    },
    {
        "problem": "wheel rolls with slip down the incline.",
        "all_must": ["미끄럼"],
        "app_must": ["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"],
        "app_must_not": ["v_G = ωR", "a_G = αR"],
        "not_must": ["v_G = ωR", "적용식으로 사용 불가"],
    },
    {
        "problem": "wheel rolls but slips at the point of contact.",
        "all_must": ["미끄럼"],
        "app_must": ["ΣF = ma_G", "ΣM_G = I_Gα"],
        "app_must_not": ["v_G = ωR", "a_G = αR"],
        "not_must": ["v_G = ωR", "a_G = αR"],
    },
    {
        "problem": "원반이 미끄럼을 가지고 구른다.",
        "all_must": ["미끄럼"],
        "app_must": ["ΣF = ma_G", "ΣM_G = I_Gα"],
        "app_must_not": ["v_G = ωR", "a_G = αR"],
    },
    {
        "problem": "원통이 경사면에서 slip하며 굴러간다.",
        "all_must": ["미끄럼"],
        "app_must": ["ΣF = ma_G", "ΣM_G = I_Gα"],
        "app_must_not": ["v_G = ωR", "a_G = αR"],
    },
    # bullet / rotating rigid body collision
    {
        "problem": "a projectile strikes a hinged bar and sticks; determine angular speed after impact.",
        "all_must": ["탄환", "회전강체", "각운동량"],
        "app_must": ["H_O(before) = H_O(after)", "m_b v r = I_totalω"],
        "app_must_not": ["x = x0", "m1v1i + m2v2i"],
        "not_must": ["선운동량"],
    },
    {
        "problem": "투사체가 피벗된 막대에 충돌하여 붙는다. 충돌 후 각속도를 구하라.",
        "all_must": ["탄환", "각운동량"],
        "app_must": ["H_O(before) = H_O(after)", "m_b v r = I_totalω"],
        "app_must_not": ["m1v1i + m2v2i"],
    },
    # cartesian vector / polar split
    {
        "problem": "r vector = 3t i + 2t^2 j, find velocity and acceleration",
        "all_must": ["위치 함수", "직교좌표"],
        "app_must": ["r(t) = x(t)i + y(t)j", "v(t) = dr/dt", "a(t) = d²r/dt²"],
        "app_must_not": ["e_r", "e_θ", "theta_dot"],
    },
    {
        "problem": "r=3t i + 2t^2 j but theta is mentioned in another sentence",
        "all_must": ["직교좌표"],
        "app_must": ["v(t) = dr/dt", "a(t) = d²r/dt²"],
        "app_must_not": ["e_r", "e_θ"],
    },
    {
        "problem": "position is <3t, 2t^2>; find acceleration",
        "all_must": ["위치 함수"],
        "app_must": ["v(t) = dr/dt", "a(t) = d²r/dt²"],
        "app_must_not": ["e_r", "e_θ"],
    },
    {
        "problem": "입자 위치가 r=(3t,2t^2)이다. v,a를 구하라.",
        "all_must": ["위치 함수"],
        "app_must": ["v(t) = dr/dt", "a(t) = d²r/dt²"],
        "app_must_not": ["e_r", "e_θ"],
    },
    # conical pendulum
    {
        "problem": "a stone tied to a string moves in a horizontal circle making angle theta with vertical.",
        "all_must": ["원뿔진자"],
        "app_must": ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"],
        "app_must_not": ["ΣM_G = I_Gα"],
    },
    {
        "problem": "a mass attached to a cord moves in a circle with the cord inclined from vertical.",
        "all_must": ["원뿔진자"],
        "app_must": ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"],
        "app_must_not": ["ΣM_G = I_Gα"],
    },
    # vertical circle
    {
        "problem": "a ball attached to a cord moves in a vertical loop. find tension at the bottom.",
        "all_must": ["수직 원운동", "최저점"],
        "app_must": ["T - mg = mv²/R", "T = mg + mv²/R"],
        "app_must_not": ["N - mg"],
    },
    {
        "problem": "a bead on a vertical circular rail. tension at bottom?",
        "all_must": ["충돌", "확인 필요"],
        "app_must": ["N - mg = mv²/R", "T - mg = mv²/R"],
        "all_must_not": [],
    },
    # banked curve
    {
        "problem": "car on inclined curve, find minimum speed before sliding down.",
        "all_must": ["경사진 커브", "최소속도"],
        "app_must": ["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"],
        "app_must_not": ["N = mg", "μ_s ≥ v²/(gR)", "tanθ = v²/(gR)"],
    },
    {
        "problem": "banked curve with coefficient of static friction, maximum safe speed",
        "all_must": ["경사진 커브", "최대속도"],
        "app_must": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
        "app_must_not": ["N = mg", "μ_s ≥ v²/(gR)", "tanθ = v²/(gR)"],
    },
    {
        "problem": "car travels on a banked curve with friction. maximum velocity before slipping outward",
        "all_must": ["경사진 커브", "최대속도"],
        "app_must": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
        "app_must_not": ["v_G = ωR", "a_G = αR", "μ_s ≥ v²/(gR)"],
    },
    {
        "problem": "마찰 있는 경사진 곡선도로의 허용 최대 속도.",
        "all_must": ["경사진 커브", "최대속도"],
        "app_must": ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
    },
    {
        "problem": "경사각 theta인 커브에서 아래로 미끄러지지 않는 최소 speed.",
        "all_must": ["경사진 커브", "최소속도"],
        "app_must": ["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"],
        "app_must_not": ["tanθ = v²/(gR)"],
    },
    # frictionless table/pulley block
    {
        "problem": "Block A lies on a friction-free table and is tied to hanging block B.",
        "all_must": ["수평면 블록", "매달린"],
        "app_must": ["f = 0", "T = m_Aa", "m_Bg - T = m_Ba"],
        "app_must_not": ["f = μN_A", "T - f = m_Aa"],
    },
    {
        "problem": "Block A is on a rough table but friction is neglected, connected to hanging B.",
        "all_must": ["수평면 블록", "매달린"],
        "app_must": ["f = 0", "T = m_Aa", "m_Bg - T = m_Ba"],
        "app_must_not": ["f = μN_A", "T - f = m_Aa"],
    },
    {
        "problem": "테이블 위의 블록과 매달린 추, 마찰은 없다.",
        "all_must": ["수평면 블록", "매달린"],
        "app_must": ["f = 0", "T = m_Aa", "m_Bg - T = m_Ba"],
        "app_must_not": ["f = μN_A"],
    },
    {
        "problem": "friction-free table with mu=0.2, hanging mass.",
        "all_must": ["수평면 블록", "마찰"],
        "app_must": ["f = 0", "T = m_Aa", "m_Bg - T = m_Ba"],
        "app_must_not": ["f = μN_A"],
    },
    # loop the loop / contact
    {
        "problem": "object slides from height h then enters a loop, find minimum height to maintain contact",
        "all_must": ["최고점", "접촉 유지"],
        "app_must": ["N = 0", "mg = mv²/R", "v_min = √(gR)"],
    },
    {
        "problem": "원형 트랙 꼭대기에서 접촉을 유지하는 최소 속력.",
        "all_must": ["최고점", "접촉 유지"],
        "app_must": ["N = 0", "mg = mv²/R", "v_min = √(gR)"],
    },
    {
        "problem": "loop-the-loop minimum height frictionless",
        "all_must": ["최고점", "접촉 유지"],
        "app_must": ["N = 0", "mg = mv²/R", "v_min = √(gR)", "f = 0"],
    },
]


@pytest.mark.parametrize("case", ROBUST_CASES)
def test_final_student_expression_robustness(case):
    _, bp, app, not_app, all_text = run_case(case["problem"])
    assert app.strip(), f"applicable_equations must not be empty for: {case['problem']}"
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
