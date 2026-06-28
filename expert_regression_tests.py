"""
3차 전문가 템플릿 회귀 테스트.
실행: python expert_regression_tests.py

구성:
- REPRESENTATIVE_CASES: 대학 동역학 대표 유형 100개
- COUNTEREXAMPLE_CASES: 자연어 오진 방지 반례 50개
- EQUATION_SKELETON_CASES: 핵심 방정식 골격 직접 검증
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy
from dynamics_core.feedback import build_diagnosis


def diagnose(problem: str, goal: str = "자동 추정"):
    f = analyze_text(problem)
    r = recommend_strategy(f, goal)
    return build_diagnosis(problem, "", goal, f, r)


def all_output(problem: str, goal: str = "자동 추정") -> str:
    d = diagnose(problem, goal)
    m = d.problem_model
    bp = d.blueprint
    parts: List[str] = [
        m.problem_type,
        *m.analysis_targets,
        *m.known_quantities,
        *m.motion_state,
        *m.forces_present,
        *m.forces_ignored,
        *m.constraints,
        *m.conservation_conditions,
        *m.coordinate_systems,
        *m.allowed_methods,
        *m.risky_methods,
        *bp.fbd_forces,
        *bp.coordinate_guide,
        *bp.governing_equations,
        *bp.auxiliary_equations,
        *bp.application_conditions,
        *bp.next_steps,
        *bp.warnings,
        *bp.interpretation_checks,
    ]
    return "\n".join(parts)


def assert_contains(problem: str, fragments: Iterable[str], goal: str = "자동 추정") -> None:
    joined = all_output(problem, goal)
    missing = [frag for frag in fragments if frag not in joined]
    assert not missing, f"Missing {missing} for problem: {problem}\n--- output ---\n{joined}"


def assert_cues(problem: str, true_cues: Iterable[str] = (), false_cues: Iterable[str] = ()) -> None:
    f = analyze_text(problem)
    for cue in true_cues:
        assert f.cues[cue] is True, f"{problem}: expected cue {cue}=True, active={[k for k,v in f.cues.items() if v]}"
    for cue in false_cues:
        assert f.cues[cue] is False, f"{problem}: expected cue {cue}=False, active={[k for k,v in f.cues.items() if v]}"


CATEGORY_BASES: List[Tuple[str, List[str], str]] = [
    ("입자가 등가속도로 3초 동안 5 m 이동한다. 최종 속도를 구하라.", ["v = v0 + at", "v² = v0² + 2as"], "속도"),
    ("차가 직선 도로에서 일정한 가속도로 움직인다. 시간과 변위로 속도를 구하라.", ["s = v0t + 1/2at²"], "속도"),
    ("공이 포물선 운동을 하도록 속도 v0, 각도 theta로 발사된다. 비행 시간을 구하라.", ["y = y0 + v0sinθ · t - 1/2gt²", "최고점: v_y = 0"], "시간"),
    ("공기저항을 무시하고 공을 던진다. 포물선 운동의 도달거리를 구하라.", ["x = x0 + v0cosθ · t"], "위치/변위"),
    ("공기저항이 속도에 비례한다. 질량 m인 물체를 수평으로 던졌을 때 운동을 분석하라.", ["m dv_x/dt = -c v_x", "m dv_y/dt = -mg - c v_y"], "자동 추정"),
    ("공기저항이 속도의 제곱에 비례한다. 투사체 운동방정식을 세워라.", ["속도 제곱 비례 저항", "m dv_y/dt = -mg - c v v_y"], "자동 추정"),
    ("경사면 위 질량 m인 블록의 가속도를 구하라.", ["ΣF_parallel", "ΣF_perpendicular"], "가속도"),
    ("마찰 있는 경사면에서 거리 s를 미끄러진 뒤 속도를 구하라.", ["f = μN", "mg sinθ"], "속도"),
    ("마찰이 없는 경사면에서 높이 h만큼 내려온 물체의 속도를 구하라.", ["mgh = 1/2mv²", "수직항력은 이동 방향에 수직"], "속도"),
    ("스프링에 연결된 블록이 압축량 x에서 출발한다. 마찰 없이 속도를 구하라.", ["T1 + V1 + W_nc = T2 + V2"], "속도"),
    ("질량 m1과 m2가 줄과 도르래로 연결되어 있다. 가속도와 장력을 구하라.", ["m1g - T = m1a", "T - m2g = m2a", "같은 줄의 장력은 같다"], "장력/마찰력"),
    ("관성모멘트 I인 도르래에 두 물체가 연결되어 있다. 줄은 미끄러지지 않는다.", ["T1 ≠ T2", "(T1 - T2)R = Iα", "a = αR"], "가속도"),
    ("자동차가 반지름 R인 평평한 커브를 속도 v로 돈다. 최소 마찰계수를 구하라.", ["N = mg", "f_s = mv²/R", "μ_s ≥ v²/(gR)"], "장력/마찰력"),
    ("질량 m인 물체가 반지름 R인 수직 원형 트랙의 최고점에서 떨어지지 않기 위한 최소 속도를 구하라.", ["최고점: mg + N = mv²/R", "v_min = √(gR)"], "접촉 유지 조건"),
    ("입자가 곡률반지름 ρ인 경로를 따라 움직인다. 법선방향 가속도를 구하라.", ["a_n = v²/ρ", "ΣF_n = m v²/ρ"], "가속도"),
    ("입자가 r=2t, theta=t²로 움직인다. 가속도를 구하라.", ["v = r_dot e_r + r theta_dot e_theta", "a = (r_ddot - r theta_dot²)e_r"], "가속도"),
    ("비보존력의 일이 작용한다. 최종 속도를 구하라.", ["T1 + V1 + W_nc = T2 + V2"], "속도"),
    ("질량 m인 물체에 충격량이 작용한다. 속도 변화를 구하라.", ["J = ∫F dt = Δp", "J = m(v2 - v1)"], "속도"),
    ("두 물체가 1차원에서 충돌한다. 반발계수 e가 주어졌을 때 충돌 후 속도를 구하라.", ["m1v1i + m2v2i = m1v1f + m2v2f", "e = (v2f - v1f)/(v1i - v2i)"], "충돌 후 속도"),
    ("질점이 중심 O 주위에서 움직이고 외부 모멘트가 0이다. 각운동량 보존을 이용하라.", ["H_O1 = H_O2", "질점: H_O = r × mv"], "자동 추정"),
    ("원판이 고정축 O 주위로 회전한다. 각가속도를 구하라.", ["ΣM_O = I_Oα", "ω² = ω0² + 2αθ"], "각속도/각가속도"),
    ("원통이 미끄러지지 않고 굴러 내려간다. 속도를 구하라.", ["mgh = 1/2mv_G² + 1/2I_Gω²", "v_G = ωR", "a_G = αR"], "속도"),
    ("막대 AB가 일반 평면운동하며 상대속도식으로 B점을 구하라.", ["v_B = v_A + ω × r_B/A", "a_B = a_A + α × r_B/A"], "속도"),
    ("막대 AB가 움직이며 A점 속도가 주어져 있다. 순간중심을 이용하여 B점 속도를 구하라.", ["v_A = ω r_A/IC", "v_B = ω r_B/IC", "순간중심 IC"], "속도"),
    ("막대 AB가 회전하지 않고 병진운동한다. 속도를 구하라.", ["회전 없음: α = 0", "ΣF = ma_G만 사용"], "속도"),
]

VARIANT_SUFFIXES = [
    " 기본 방정식 골격을 제시하라.",
    " 자유물체도와 좌표계를 함께 설명하라.",
    " 적용 조건과 주의점을 포함하라.",
    " 풀이 순서를 단계별로 정리하라.",
]

REPRESENTATIVE_CASES: List[Tuple[str, List[str], str]] = []
for base, fragments, goal in CATEGORY_BASES:
    for suffix in VARIANT_SUFFIXES:
        REPRESENTATIVE_CASES.append((base + suffix, fragments, goal))

COUNTEREXAMPLE_CASES: List[Tuple[str, Tuple[str, ...], Tuple[str, ...]]] = [
    ("매끈한 테이블 위에서 블록이 움직인다.", ("no_friction",), ("tension", "friction")),
    ("매끄러운 면 위에서 물체가 움직인다.", ("no_friction",), ("friction",)),
    ("마찰계수 μ가 0.2로 주어졌지만 수평면은 매끄럽다고 가정한다.", ("no_friction",), ("friction",)),
    ("마찰을 무시한다.", ("no_friction",), ("friction",)),
    ("마찰은 고려하지 않는다.", ("no_friction",), ("friction",)),
    ("마찰력은 작용하지 않는다.", ("no_friction",), ("friction",)),
    ("frictionless smooth surface 위에서 운동한다.", ("no_friction",), ("friction",)),
    ("neglect friction and find the speed.", ("no_friction",), ("friction",)),
    ("ignore friction in this problem.", ("no_friction",), ("friction",)),
    ("속도를 구하라.", tuple(), ("rigid_body",)),
    ("가속도를 구하여라.", tuple(), ("rigid_body",)),
    ("구할 값은 속도이다.", tuple(), ("rigid_body",)),
    ("momentum is conserved.", ("momentum",), ("torque",)),
    ("linear momentum 보존을 이용하라.", ("momentum",), ("torque",)),
    ("momentum before and after impact를 비교하라.", ("momentum",), ("torque",)),
    ("탄성 충돌이 아니며 외력이 작용한다.", ("collision",), ("spring",)),
    ("완전탄성 충돌에서 속도를 구하라.", ("collision",), ("spring",)),
    ("비탄성 충돌 후 속도를 구하라.", ("collision",), ("spring",)),
    ("공이 벽에 충돌하지 않고 접근한다. 운동량을 구하라.", ("no_collision", "momentum"), ("collision",)),
    ("아직 충돌하지 않았다. 현재 운동량을 구하라.", ("no_collision", "momentum"), ("collision",)),
    ("충돌하기 전 속도를 구하라.", ("no_collision",), ("collision",)),
    ("충돌 전 운동량을 구하라.", ("no_collision", "momentum"), ("collision",)),
    ("before collision, find momentum.", ("no_collision", "momentum"), ("collision",)),
    ("approaching without impact, find momentum.", ("no_collision", "momentum"), ("collision",)),
    ("공기저항을 무시한다.", ("no_air_resistance",), ("air_resistance",)),
    ("공기저항 없음 조건이다.", ("no_air_resistance",), ("air_resistance",)),
    ("공기저항을 무시하지 않는다.", ("air_resistance",), ("no_air_resistance",)),
    ("공기저항이 속도에 비례한다.", ("air_resistance",), ("no_air_resistance",)),
    ("저항력은 kv이다.", ("air_resistance",), tuple()),
    ("drag force is not negligible.", ("air_resistance",), ("no_air_resistance",)),
    ("막대가 회전하지 않고 병진운동한다.", ("no_rotation", "translation_only"), ("rotation", "rolling")),
    ("막대가 회전 없이 움직인다.", ("no_rotation",), ("rotation",)),
    ("각속도는 0이다.", ("no_rotation",), ("rotation",)),
    ("pure translation of the bar.", ("no_rotation", "translation_only"), ("rotation",)),
    ("m=5 kg인 물체가 3 m를 이동한다.", ("mass", "distance"), tuple()),
    ("5 kg의 물체가 움직인다.", ("mass",), tuple()),
    ("5 kg짜리 물체에 힘이 작용한다.", ("mass", "force"), tuple()),
    ("10 N의 힘이 작용한다.", ("force",), tuple()),
    ("3 m를 이동한다.", ("distance",), ("mass",)),
    ("2 m/s로 운동한다.", tuple(), ("distance",)),
    ("30 rad/s로 회전한다.", ("rotation",), tuple()),
    ("입자가 r=2t, theta=t^2로 움직인다.", ("polar",), tuple()),
    ("입자가 r(t), θ(t)로 주어진다.", ("polar",), tuple()),
    ("theta_dot이 주어진 극좌표 문제이다.", ("polar",), tuple()),
    ("질량 있는 도르래의 관성모멘트 I가 주어진다.", ("pulley_connected", "torque"), tuple()),
    ("질량 없는 도르래와 같은 줄이다.", ("pulley_connected",), tuple()),
    ("미끄러지지 않고 구른다.", ("rolling",), ("no_rotation",)),
    ("미끄러진다. v=ωR인지 판단하라.", ("sliding",), ("rolling",)),
    ("원형 트랙의 반지름 R은 경로 반지름이다.", ("circular",), tuple()),
    ("반지름 R인 원통 자체가 있다.", ("rigid_body",), ("circular",)),
]

EQUATION_SKELETON_CASES = [
    ("질량 m1과 m2가 줄과 도르래로 연결되어 있다. 가속도와 장력을 구하라.", ["m1g - T = m1a", "T - m2g = m2a", "같은 줄의 장력은 같다", "가속도 크기는 같다"], "장력/마찰력"),
    ("관성모멘트 I인 도르래에 두 물체가 연결되어 있다. 줄은 미끄러지지 않는다.", ["T1 ≠ T2", "(T1 - T2)R = Iα", "a = αR"], "가속도"),
    ("자동차가 반지름 R인 평평한 커브를 속도 v로 돈다. 최소 마찰계수를 구하라.", ["N = mg", "f_s = mv²/R", "f_s ≤ μ_sN", "μ_s ≥ v²/(gR)"], "장력/마찰력"),
    ("입자가 r=2t, theta=t²로 움직인다. 가속도를 구하라.", ["v = r_dot e_r + r theta_dot e_theta", "a = (r_ddot - r theta_dot²)e_r"], "가속도"),
    ("원통이 미끄러지지 않고 굴러 내려간다.", ["v_G = ωR", "a_G = αR", "mgh = 1/2mv_G² + 1/2I_Gω²"], "속도"),
]


def test_representative_case_count_and_fragments() -> None:
    assert len(REPRESENTATIVE_CASES) == 100
    for problem, fragments, goal in REPRESENTATIVE_CASES:
        assert_contains(problem, fragments, goal)


def test_counterexample_case_count_and_cues() -> None:
    assert len(COUNTEREXAMPLE_CASES) == 50
    for problem, true_cues, false_cues in COUNTEREXAMPLE_CASES:
        assert_cues(problem, true_cues, false_cues)


def test_core_equation_skeletons() -> None:
    for problem, fragments, goal in EQUATION_SKELETON_CASES:
        assert_contains(problem, fragments, goal)


def run_all() -> None:
    test_representative_case_count_and_fragments()
    test_counterexample_case_count_and_cues()
    test_core_equation_skeletons()


if __name__ == "__main__":
    run_all()
    print("OK: expert regression tests passed — 100 representative cases, 50 counterexamples, and equation skeleton checks")
