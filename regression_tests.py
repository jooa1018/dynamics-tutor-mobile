"""
2차 재작업판 핵심 회귀 테스트.
실행: python regression_tests.py

테스트 범위:
- 한국어 부분문자열/부정 표현 오진 방지
- 대표 동역학 유형별 추천 전략
- 문제 구조화/풀이 골격 생성
- 계산기 입력 검증
"""
from __future__ import annotations

from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy
from dynamics_core.feedback import build_diagnosis
from dynamics_core.calculators import (
    circular_min_speed,
    collision_1d,
    energy_speed_from_height,
    projectile_motion,
    rolling_speed_from_height,
    solve_constant_acceleration,
)


def primary(problem: str, goal: str = "자동 추정"):
    f = analyze_text(problem, "")
    r = recommend_strategy(f, goal)
    return r.primary, f, r


def diagnosis(problem: str, goal: str = "자동 추정"):
    p, f, r = primary(problem, goal)
    return build_diagnosis(problem, "", "자동 추정", f, r)


def assert_any(texts, needle: str):
    joined = "\n".join(texts)
    assert needle in joined, f"'{needle}' not found in: {joined}"


def test_false_positive_and_negation_regressions():
    f = analyze_text("매끈한 테이블 위에서 블록이 움직인다.")
    assert f.cues["no_friction"] is True
    assert f.cues["friction"] is False
    assert f.cues["tension"] is False

    f = analyze_text("속도를 구하라.")
    assert f.cues["rigid_body"] is False

    f = analyze_text("momentum is conserved.")
    assert f.cues["momentum"] is True
    assert f.cues["torque"] is False

    f = analyze_text("마찰이 없는 경사면에서 물체가 미끄러진다.")
    assert f.cues["no_friction"] is True
    assert f.cues["friction"] is False

    p, f, _ = primary("막대 AB가 홈을 따라 운동한다. 순간중심을 이용해 B점의 속도를 구하라.", "속도")
    assert f.cues["instant_center"] is True
    assert f.cues["impulse"] is False
    assert p in {"상대속도/순간중심", "강체 평면운동", "복합 풀이"}

    f = analyze_text("물체가 3 m 이동한 뒤 속도를 구하라.")
    assert f.cues["distance"] is True
    assert f.cues["mass"] is False

    f = analyze_text("마찰계수 μ가 0.2이지만 이번 문제에서는 마찰을 무시한다. 속도를 구하라.")
    assert f.cues["no_friction"] is True
    assert f.cues["friction"] is False

    f = analyze_text("m=5 kg인 물체가 3 m를 이동한다. 속도를 구하라.")
    assert f.cues["mass"] is True
    assert f.cues["distance"] is True

    f = analyze_text("탄성 충돌이 아니며 외력이 작용한다. 운동량 보존을 쓸 수 있는가?")
    assert f.cues["momentum"] is True
    assert f.cues["spring"] is False

    f = analyze_text("공이 벽에 충돌하지 않고 접근한다. 운동량을 구하라.")
    assert f.cues["no_collision"] is True
    assert f.cues["collision"] is False
    assert f.cues["momentum"] is True

    f = analyze_text("공기저항을 무시하지 않는다. 포물선 운동의 도달거리를 구하라.")
    assert f.cues["air_resistance"] is True
    assert f.cues["no_air_resistance"] is False
    assert any("표준 포물선" in w for w in f.warnings)

    f = analyze_text("막대 AB가 회전하지 않고 병진운동한다. 속도를 구하라.")
    assert f.cues["translation_only"] is True
    assert f.cues["no_rotation"] is True
    assert f.cues["rotation"] is False


def test_korean_unit_particles():
    samples = [
        ("5 kg인 물체", "mass"),
        ("5 kg의 물체", "mass"),
        ("5 kg짜리 물체", "mass"),
        ("10 N의 힘", "force"),
        ("3 m를 이동", "distance"),
        ("30 rad/s로 회전", "rotation"),
    ]
    for text, cue in samples:
        f = analyze_text(text)
        assert f.cues[cue] is True, f"{text} should trigger {cue}"
    f = analyze_text("2 m/s로 운동한다.")
    assert f.cues["distance"] is False, "m/s 속도 단위의 m을 거리 m로 오진하면 안 됨"


def test_representative_strategy_cases():
    cases = [
        ("공이 지면에서 속도 20 m/s, 각도 30도로 발사된다. 최고 높이와 비행 시간을 구하라.", "시간", {"운동학"}),
        ("질량 5 kg인 물체가 마찰계수 0.2인 30도 경사면 위에 있다. 경사면 아래 방향 가속도를 구하라.", "가속도", {"뉴턴 제2법칙 F=ma", "복합 풀이"}),
        ("마찰 없는 경사면에서 물체가 높이 h만큼 내려와 바닥에서 속도를 구하라.", "속도", {"일-에너지 원리", "복합 풀이"}),
        ("작은 블록이 마찰 없는 트랙에서 높이 h부터 출발해 반지름 R인 원형 고리를 지난다. 꼭대기에서 떨어지지 않기 위한 최소 높이를 구하라.", "접촉 유지 조건", {"복합 풀이"}),
        ("질량 2 kg 물체가 정지한 3 kg 물체와 1차원 충돌한다. 반발계수 e=0.6일 때 충돌 후 속도를 구하라.", "충돌 후 속도", {"충격량-운동량"}),
        ("반지름 R인 원판이 미끄러지지 않고 경사면을 굴러 내려온다. 높이 h만큼 내려왔을 때 중심 속도를 구하라.", "속도", {"복합 풀이"}),
        ("반지름 R인 원판이 고정축 주위로 회전한다. 각가속도를 구하라.", "각속도/각가속도", {"강체 평면운동"}),
        ("질량 있는 도르래의 관성모멘트 I가 주어지고 줄이 미끄러지지 않는다. 두 물체의 가속도를 구하라.", "가속도", {"복합 풀이"}),
        ("입자가 곡률반지름 ρ인 경로를 따라 움직인다. 법선방향 가속도를 구하라.", "가속도", {"원운동 조건"}),
        ("A가 움직이는 차 위에서 B를 향해 공을 던진다. 상대속도를 구하라.", "속도", {"상대속도/순간중심"}),
        ("위치 x에 따라 변하는 힘 F(x)가 작용한다. 3 m 이동 후 속도를 구하라.", "속도", {"일-에너지 원리", "복합 풀이"}),
        ("평평한 커브를 도는 자동차의 최대 속도를 구하라. 마찰계수 μ가 주어진다.", "속도", {"원운동 조건", "복합 풀이"}),
        ("수직 원운동 꼭대기에서 줄이 팽팽하게 유지될 최소 속도를 구하라.", "접촉 유지 조건", {"원운동 조건"}),
        ("두 블록이 줄로 연결되어 도르래를 지난다. 장력을 구하라.", "장력/마찰력", {"뉴턴 제2법칙 F=ma", "복합 풀이"}),
        ("용수철에 연결된 블록이 압축량 x에서 출발한다. 마찰 없이 속도를 구하라.", "속도", {"일-에너지 원리"}),
        ("완전비탄성 충돌 후 두 물체가 함께 움직인다. 최종 속도를 구하라.", "충돌 후 속도", {"충격량-운동량"}),
        ("핀으로 고정된 막대가 중력 때문에 회전한다. 처음 각가속도를 구하라.", "각속도/각가속도", {"강체 평면운동"}),
        ("원통이 미끄러지면서 내려온다. v=ωR을 쓸 수 있는지 판단하라.", "속도", {"강체 평면운동", "복합 풀이", "운동학"}),
        ("극좌표 r과 θ가 시간 함수로 주어진다. 속도와 가속도를 구하라.", "가속도", {"운동학"}),
        ("각운동량 보존을 이용해 회전하는 물체의 각속도를 구하라.", "각속도/각가속도", {"강체 평면운동", "충격량-운동량", "복합 풀이"}),
    ]
    for problem, goal, expected_set in cases:
        actual, f, r = primary(problem, goal)
        assert actual in expected_set, f"expected one of {expected_set}, actual={actual}, cues={f.cues}, scores={r.scores}"


def test_problem_model_and_blueprint_generation():
    d = diagnosis("마찰이 없는 경사면 위에서 질량 5 kg인 물체가 높이 2 m에서 정지 상태로 출발한다. 아래쪽에서의 속도를 구하라.", "속도")
    assert "경사면" in d.problem_model.problem_type
    assert_any(d.problem_model.forces_ignored, "마찰")
    assert_any(d.problem_model.coordinate_systems, "경사면 평행")
    assert_any(d.blueprint.auxiliary_equations, "f = 0")
    assert any("mgh" in eq or "T1" in eq for eq in d.blueprint.governing_equations + d.blueprint.auxiliary_equations)

    d = diagnosis("평평한 커브를 도는 자동차가 미끄러지지 않을 최대 속도를 구하라. 마찰계수 μ가 주어진다.", "속도")
    assert_any(d.blueprint.governing_equations, "ΣF_n")
    assert_any(d.problem_model.forces_present, "마찰")

    d = diagnosis("반지름 R인 원판이 미끄러지지 않고 굴러 내려간다. 중심 속도를 구하라.", "속도")
    assert_any(d.problem_model.constraints, "v_G")
    assert_any(d.blueprint.governing_equations, "1/2I")

    d = diagnosis("막대 AB가 홈을 따라 운동한다. 순간중심을 이용해 B점의 속도를 구하라.", "속도")
    assert "상대속도" in d.problem_model.problem_type
    assert_any(d.blueprint.auxiliary_equations, "순간중심")

    d = diagnosis("공기저항을 무시하지 않는다. 포물선 운동의 도달거리를 구하라.", "위치/변위")
    assert_any(d.blueprint.warnings, "공기저항")

    d = diagnosis("막대 AB가 회전하지 않고 병진운동한다. 속도를 구하라.", "속도")
    assert d.problem_model.problem_type == "순수 병진운동"
    assert_any(d.problem_model.risky_methods, "ΣM")

    d = diagnosis("두 물체가 줄로 연결되어 도르래를 지난다. 가속도를 구하라.", "가속도")
    assert_any(d.problem_model.constraints, "가속도")
    assert_any(d.problem_model.forces_present, "장력")

    d = diagnosis("핀으로 고정된 막대가 회전한다. 각가속도를 구하라.", "각속도/각가속도")
    assert d.problem_model.problem_type == "강체 고정축 회전"
    assert_any(d.blueprint.governing_equations, "ΣM_O")

    d = diagnosis("완전탄성 충돌 후 속도를 구하라. 반발계수 e=1이다.", "충돌 후 속도")
    assert d.problem_model.problem_type == "충격량-운동량/충돌 문제"
    assert_any(d.blueprint.auxiliary_equations, "반발계수")

    d = diagnosis("극좌표에서 r=2t, θ=t²로 움직이는 입자의 가속도를 구하라.", "가속도")
    assert_any(d.problem_model.coordinate_systems, "e_r")
    assert_any(d.blueprint.governing_equations, "r̈")


def test_calculator_validation():
    assert not circular_min_speed(0, 9.81).ok
    assert not circular_min_speed(1, 0).ok
    assert not energy_speed_from_height(-1, 0, 9.81).ok
    assert not energy_speed_from_height(1, -0.1, 9.81).ok
    assert not collision_1d(0, 1, 1, 0, 0.5).ok
    assert collision_1d(1, 1, 1, 0, 1.2).ok and collision_1d(1, 1, 1, 0, 1.2).warnings
    assert not rolling_speed_from_height(1, -0.5, 9.81).ok
    assert not rolling_speed_from_height(1, 3.0, 9.81).ok
    assert not projectile_motion(10, 30, 0, 9.81, air_resistance=True).ok

    down = projectile_motion(10, -30, 2, 9.81)
    assert down.ok
    assert down.values["최고 높이"] == 2
    assert down.warnings

    ca = solve_constant_acceleration({"s": None, "u": 0, "v": None, "a": 2, "t": 3}, "v")
    assert ca.ok and abs(ca.values["v"][0] - 6) < 1e-9

    bad_time = solve_constant_acceleration({"s": None, "u": 0, "v": 10, "a": 2, "t": -3}, "s")
    assert not bad_time.ok

    bad = solve_constant_acceleration({"s": 100, "u": 0, "v": None, "a": 2, "t": 3}, "v")
    assert not bad.ok or bad.warnings


def run_all():
    test_false_positive_and_negation_regressions()
    test_korean_unit_particles()
    test_representative_strategy_cases()
    test_problem_model_and_blueprint_generation()
    test_calculator_validation()


if __name__ == "__main__":
    run_all()
    print("OK: all 2nd-rework regression tests passed")
