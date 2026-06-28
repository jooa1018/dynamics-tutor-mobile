"""
자연어 표현 정규화와 물리 상황 우선순위 회귀 테스트.

이 파일은 특정 한두 문장을 하드코딩하지 않고, 같은 물리 상황을 여러
표현으로 말했을 때 같은 구조화 출력이 나오는지 검사합니다.
검증은 전체 문자열이 아니라 applicable_equations / not_applicable_equations /
cautions / suppressed_templates 등 영역별로 수행합니다.
"""
from __future__ import annotations

import pytest

from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy
from dynamics_core.feedback import build_diagnosis


def diagnose(problem: str):
    features = analyze_text(problem)
    rec = recommend_strategy(features, "자동 추정")
    return build_diagnosis(problem, "", "자동 추정", features, rec)


def joined(items):
    return "\n".join(str(x) for x in items)


def assert_contains(area, fragments, problem, label):
    text = joined(area)
    missing = [x for x in fragments if x not in text]
    assert not missing, f"{label} missing={missing}\nproblem={problem}\narea=\n{text}"


def assert_excludes(area, fragments, problem, label):
    text = joined(area)
    bad = [x for x in fragments if x in text]
    assert not bad, f"{label} forbidden={bad}\nproblem={problem}\narea=\n{text}"


def check(problem, type_contains, must_applicable, forbidden_applicable=(), must_not_applicable=(), must_caution=(), must_ambiguity=()):
    d = diagnose(problem)
    bp = d.blueprint
    assert type_contains in d.problem_model.problem_type, f"type={d.problem_model.problem_type}\nproblem={problem}"
    assert_contains(bp.applicable_equations, must_applicable, problem, "applicable")
    assert_excludes(bp.applicable_equations, forbidden_applicable, problem, "applicable")
    assert_contains(bp.not_applicable_equations, must_not_applicable, problem, "not_applicable")
    assert_contains(bp.cautions, must_caution, problem, "cautions")
    assert_contains(bp.ambiguity_notes, must_ambiguity, problem, "ambiguity")


BANKED_MAX = [
    "경사각 θ인 커브에서 자동차가 미끄러지지 않고 돌 수 있는 최대 속력을 구하라.",
    "마찰이 있는 뱅크 커브에서 허용 가능한 최대 속력을 구하라.",
    "banked curve에서 maximum speed를 구하라. friction이 있다.",
    "경사진 커브에서 최대 속도 조건을 구하라. 마찰계수 μ가 있다.",
    "경사 커브에서 차가 미끄러지지 않는 최대속력을 구하라.",
    "기울어진 도로 커브에서 highest speed를 구하라. 정지마찰이 작용한다.",
    "경사각이 있는 커브에서 허용 최대 속도는 얼마인가? friction 있음.",
    "뱅크 커브에서 자동차가 위로 미끄러지기 직전 최대 속력을 구하라.",
    "경사진 커브에서 최대속도일 때 마찰 방향을 고려하여 식을 세워라.",
    "bank curve with friction: maximum allowable speed를 구하라.",
]
BANKED_MIN = [
    "마찰이 있는 경사 커브에서 아래로 미끄러지지 않는 최소 속력을 구하라.",
    "banked curve에서 minimum speed를 구하라. friction이 있다.",
    "경사진 커브에서 자동차의 최소 속도 조건을 구하라. 마찰계수 μ가 있다.",
    "뱅크 커브에서 아래로 미끄러지기 직전 최소속력을 구하라.",
    "경사각 θ인 커브에서 최저 허용 속력을 구하라. 정지마찰이 작용한다.",
    "기울어진 도로 커브에서 lowest speed를 구하라. friction 있음.",
    "경사 커브에서 최소 속력 조건을 구하라. 마찰이 있다.",
    "마찰 있는 banked curve에서 min speed를 구하라.",
    "경사진 커브에서 자동차가 아래쪽으로 미끄러지지 않는 최소 속도는?",
    "뱅크 커브에서 최소속도 한계식을 세워라. 마찰계수 μ_s가 있다.",
]
BANKED_FRICTIONLESS = [
    "마찰 없는 경사진 커브에서 필요한 경사각을 구하라.",
    "frictionless banked curve에서 설계속도 v를 구하라.",
    "경사각 θ인 커브를 마찰 없이 돈다. 속도 조건을 구하라.",
    "기울어진 도로에서 frictionless 조건일 때 tanθ 관계식을 구하라.",
    "마찰 없이 bank curve를 돌기 위한 경사각을 구하라.",
    "경사진 커브에서 마찰을 무시한다. 필요한 경사각은?",
    "뱅크 커브가 smooth라면 속도와 경사각 관계를 구하라.",
    "경사 커브에서 no friction일 때 자동차가 도는 조건을 구하라.",
    "마찰 없는 banked curve의 설계 속도를 구하라.",
    "경사진 커브에서 frictionless surface라고 가정한다. θ를 구하라.",
]


@pytest.mark.parametrize("problem", BANKED_MAX)
def test_banked_curve_max_variants(problem):
    check(problem, "최대속도", ["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"], ["N = mg", "μ_s ≥ v²/(gR)", "tanθ = v²/(gR)"], ["N = mg", "μ_s ≥ v²/(gR)"])


@pytest.mark.parametrize("problem", BANKED_MIN)
def test_banked_curve_min_variants(problem):
    check(problem, "최소속도", ["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"], ["N = mg", "μ_s ≥ v²/(gR)", "tanθ = v²/(gR)"], ["N = mg", "μ_s ≥ v²/(gR)"])


@pytest.mark.parametrize("problem", BANKED_FRICTIONLESS)
def test_banked_curve_frictionless_variants(problem):
    check(problem, "마찰 없는 경사진 커브", ["N cosθ = mg", "N sinθ = mv²/R", "tanθ = v²/(gR)"], ["N = mg", "μ_s ≥ v²/(gR)"])


CONICAL_FULL = [
    "줄에 매단 물체가 수평면에서 원을 그리며 회전하고 줄이 수직과 θ를 이룬다.",
    "줄 끝에 달린 공이 원뿔 모양으로 돈다. 각속도를 구하라.",
    "끈에 매단 질점이 수평 원운동을 하고 끈은 연직선과 각도 θ를 이룬다.",
    "실에 달린 구슬이 수평면에서 원을 그리며 돈다. 실이 수직선과 θ를 이룬다.",
    "로프에 매단 물체가 horizontal circle을 그리며 rope makes an angle with the vertical.",
    "string에 매단 mass moves in a horizontal circle and string makes an angle theta with the vertical.",
    "원뿔 형태로 도는 줄 끝의 공의 각속도를 구하라.",
    "원뿔 궤적을 그린다. 줄에 매단 물체의 장력과 각속도를 구하라.",
    "conical motion에서 줄에 매단 질점의 ω를 구하라.",
    "수평면에서 원을 그리며 도는 로프 끝 물체가 수직과 θ를 이룬다.",
    "줄에 매단 물체가 수평 원운동 중이고 연직선과 theta 각을 이룬다.",
    "끈에 매달린 공이 원을 그리며 돈다. 끈은 vertical과 θ를 이룬다.",
    "로프 끝 물체가 원뿔진자 운동을 한다.",
    "실 끝에 달린 공이 원뿔 모양으로 회전한다.",
    "string pendulum moves in a horizontal circle with angle θ from vertical.",
]
CONICAL_AMBIGUOUS = [
    "끈에 매단 물체가 수평면에서 원을 그리며 돈다. 각도 기준은 그림에서 확인해야 한다.",
    "줄에 달린 물체가 원을 그리며 돈다. 수평 원운동인지 확인하라.",
    "로프에 매단 공이 회전한다. 줄 각도와 수평 원운동 여부를 확인해야 한다.",
    "string에 매단 물체가 원운동한다. vertical angle 정보가 없다.",
    "실에 매달린 구슬이 원을 그리는 듯하다. 각도 기준을 확인하라.",
    "줄 끝 물체가 돌고 있다. 수평면에서 도는지 확인 필요.",
    "로프에 매달린 물체가 circular motion을 한다. angle 기준이 없다.",
    "끈에 달린 공이 원을 돈다. 수평 원운동 여부가 명확하지 않다.",
    "줄에 매단 질점이 회전한다. 원뿔진자인지 확인하라.",
    "rope attached mass rotates; need vertical angle information.",
    "줄에 달린 공의 각속도를 구하라. 각도 기준은 주어지지 않았다.",
    "끈 끝의 물체가 원형 경로를 움직인다. 수직과 각도 정보가 필요하다.",
    "실에 매단 물체가 도는 문제다. 원뿔진자 가능성을 검토하라.",
    "string mass circular motion, horizontal plane not stated.",
    "로프 끝의 물체가 회전한다. 수평 원운동인지 확인 필요.",
]


@pytest.mark.parametrize("problem", CONICAL_FULL)
def test_conical_full_variants(problem):
    check(problem, "원뿔진자", ["T cosθ = mg", "T sinθ = mω²r"], ["ΣM_G = I_Gα"], ["ΣM_G = I_Gα"])


@pytest.mark.parametrize("problem", CONICAL_AMBIGUOUS)
def test_conical_ambiguity_variants(problem):
    check(problem, "원뿔진자 가능성", [], ["ΣM_G = I_Gα"], ["ΣM_G = I_Gα"], must_ambiguity=["원뿔진자 가능성 있음"])


SLIP_ROLLING = [
    "원통이 경사면을 굴러 내려가지만 미끄럼이 발생한다.",
    "원통이 경사면에서 미끄러지며 돈다.",
    "원통이 경사면을 미끄러지며 내려가고 회전도 한다.",
    "원통이 미끄러지면서 돈다.",
    "원통이 미끄러지며 회전한다.",
    "원통이 구르면서 미끄러진다.",
    "원통이 굴러가지만 미끄러진다.",
    "원판이 rolling with slip 상태로 움직인다.",
    "원반이 sliding while rotating 한다.",
    "바퀴가 slips as it rotates.",
    "원통에서 slip occurs while rolling down the incline.",
    "원통이 not pure rolling 상태이다.",
    "cylinder rolls with slipping down an incline.",
    "disk slides while spinning.",
    "원통이 미끄럼을 동반한 회전을 한다.",
    "원판이 구르지만 slip이 있다.",
    "바퀴가 경사면에서 미끄럼이 있다.",
    "원통은 굴러 내려가지만 순수 구름은 아니다.",
    "cylinder is rolling but with slipping.",
    "원반이 미끄러져 내려가면서 동시에 회전한다.",
    "원통이 slip and rotate 한다.",
    "바퀴가 sliding and rotating 한다.",
    "원판이 미끄러지며 돈다.",
    "원통이 미끄러지면서 회전한다.",
    "원통이 굴러 내려가지만 미끄럼이 있다.",
    "wheel rolls down with slipping.",
    "cylinder slips as it rotates.",
    "원통이 경사면에서 미끄러짐을 동반한다.",
    "원판이 구르면서 미끄럼이 발생한다.",
    "원통이 구름 운동 중이지만 접점에서 slip이 발생한다.",
]


@pytest.mark.parametrize("problem", SLIP_ROLLING)
def test_slip_rolling_variants(problem):
    check(problem, "미끄럼", ["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"], ["v_G = ωR", "a_G = αR"], ["v_G = ωR", "a_G = αR"], ["v_G = ωR 적용 불가"])


VERTICAL_BOTTOM_STRING = [
    "로프에 묶인 공이 수직 원운동을 한다. 가장 아래에서 장력을 구하라.",
    "끈에 매단 물체가 수직 원운동을 한다. 가장 낮은 위치에서 장력을 구하라.",
    "줄에 매단 물체가 vertical circle을 하고 bottom에서 tension을 구하라.",
    "실에 달린 공이 수직 원을 돈다. 맨 아래에서 장력을 구하라.",
    "rope에 매단 물체가 vertical circle, at the bottom tension을 구하라.",
    "cord에 묶인 공의 lowest point 장력을 구하라.",
    "줄에 매단 공이 수직 원운동 중 아래쪽 지점에서 장력은?",
    "끈에 묶인 물체가 vertical circle bottom position에서 tension을 구한다.",
    "로프에 달린 구슬이 수직 원운동을 한다. 가장 아래점 장력을 구하라.",
    "string에 매단 mass의 bottom tension을 구하라.",
]
VERTICAL_TOP_STRING = [
    "줄에 매단 물체가 수직 원운동을 한다. 최고점에서 최소속도를 구하라.",
    "끈에 달린 공이 가장 위에서 떨어지지 않기 위한 속도를 구하라.",
    "rope mass vertical circle at the top minimum speed.",
    "실에 매단 공의 highest point 조건을 구하라.",
    "줄 문제에서 top position의 장력 조건을 세워라.",
    "수직 원운동 최고점에서 줄이 팽팽하기 위한 조건을 구하라.",
    "string vertical circle top condition을 구하라.",
    "로프에 매단 물체가 가장 위점에서 이탈하지 않는 조건.",
    "끈에 달린 구슬이 맨 위에서 최소 속도를 구하라.",
    "줄에 매달린 공이 at the top에서 tension 최소조건.",
]
VERTICAL_BOTTOM_TRACK = [
    "원형 트랙을 도는 물체가 가장 아래에서 수직항력을 구하라.",
    "레일 위 물체가 vertical circle bottom에서 normal force를 구하라.",
    "원형 궤도 최저점에서 N을 구하라.",
    "track의 lowest point에서 수직항력은?",
    "loop bottom position에서 normal reaction을 구하라.",
    "원형 고리 가장 아래점에서 수직항력 식을 세워라.",
    "레일을 따라 도는 물체의 맨 아래 N을 구하라.",
    "circular track at the bottom normal force.",
    "트랙 최저점 수직항력 문제.",
    "원형 트랙에서 가장 낮은 위치의 N을 구하라.",
]


@pytest.mark.parametrize("problem", VERTICAL_BOTTOM_STRING)
def test_vertical_circle_bottom_string_variants(problem):
    check(problem, "최저점", ["T - mg = mv²/R", "T = mg + mv²/R"], ["N - mg = mv²/R", "v_min = √(gR)"], ["v_min = √(gR)"])


@pytest.mark.parametrize("problem", VERTICAL_TOP_STRING)
def test_vertical_circle_top_string_variants(problem):
    check(problem, "최고점", ["mg + T = mv²/R", "v_min = √(gR)"], ["T - mg = mv²/R"])


@pytest.mark.parametrize("problem", VERTICAL_BOTTOM_TRACK)
def test_vertical_circle_bottom_track_variants(problem):
    check(problem, "최저점", ["N - mg = mv²/R", "N = mg + mv²/R"], ["T - mg = mv²/R", "v_min = √(gR)"], ["v_min = √(gR)"])


FRICTIONLESS_HORIZONTAL = [
    "Block A is on a frictionless table and connected to hanging block B over a pulley.",
    "Block A is on a smooth table and connected to hanging block B over a pulley.",
    "Block A is on a table with no friction and connected to hanging block B by a pulley.",
    "Block A is on a surface; ignore friction. It is connected to hanging block B over a pulley.",
    "smooth horizontal table 위의 블록 A와 매달린 블록 B가 도르래로 연결되어 있다.",
    "frictionless surface 위 블록 A가 hanging mass B와 pulley로 연결된다.",
    "마찰 없는 테이블 위 블록 A와 매달린 물체 B가 도르래로 연결되어 있다.",
    "매끄러운 수평면 위 블록 A와 매달린 물체 B가 도르래로 연결되어 있다.",
    "마찰을 무시하는 테이블 위 블록과 hanging block이 pulley로 연결된다.",
    "마찰계수 μ가 주어졌지만 마찰을 무시한다. 테이블 위 블록 A와 매달린 블록 B가 도르래로 연결된다.",
    "ignore friction: block A on table connected to hanging block B over pulley.",
    "neglect friction for block A on table connected to suspended block B by a pulley.",
    "Block A rests on a smooth surface and is connected over a pulley to hanging block B.",
    "마찰 없음: 수평면 블록 A와 매달린 B가 pulley로 연결.",
    "매끈한 탁자 위 블록 A와 매달린 물체 B가 줄과 도르래로 연결된다.",
]
FRICTION_PRESENT_HORIZONTAL = [
    "마찰계수 μ가 있는 수평면 위 블록 A와 매달린 물체 B가 도르래로 연결된다.",
    "rough table 위 block A connected to hanging block B over pulley.",
    "마찰이 있는 테이블 위 블록과 매달린 블록이 도르래로 연결되어 있다.",
    "운동마찰계수 μ_k가 주어진 수평면 블록-매달린 물체 문제.",
    "정지마찰이 작용하는 table의 block A와 hanging block B가 pulley로 연결된다.",
]
FRICTION_UNKNOWN_HORIZONTAL = [
    "테이블 위 블록 A와 매달린 물체 B가 도르래로 연결되어 있다.",
    "Block A is on a table and connected to hanging block B over a pulley.",
    "수평면 위 블록과 매달린 물체가 도르래로 연결된다. 마찰 조건은 주어지지 않았다.",
    "surface 위 block A와 hanging block B가 pulley로 연결된다.",
    "탁자 위 블록과 매달린 블록이 줄로 연결된다.",
    "table block and suspended block connected by pulley; friction not specified.",
    "블록 A가 테이블 위에 있고 B가 매달려 있다. 도르래로 연결됨.",
    "horizontal surface block connected to hanging mass over a pulley.",
    "테이블 위 물체와 매달린 물체 연결 문제. 가속도와 장력 구하기.",
    "pulley connects a block on a table and a hanging mass.",
]


@pytest.mark.parametrize("problem", FRICTIONLESS_HORIZONTAL)
def test_frictionless_horizontal_block_variants(problem):
    check(problem, "수평면 블록", ["f = 0", "T = m_Aa", "m_Bg - T = m_Ba"], ["f = μN_A", "T - f = m_Aa"], ["f = μN_A"])


@pytest.mark.parametrize("problem", FRICTION_PRESENT_HORIZONTAL)
def test_friction_present_horizontal_block_variants(problem):
    check(problem, "수평면 블록", ["f = μN_A = μm_Ag", "T - f = m_Aa", "m_Bg - T = m_Ba"], ["f = 0"])


@pytest.mark.parametrize("problem", FRICTION_UNKNOWN_HORIZONTAL)
def test_friction_unknown_horizontal_block_variants(problem):
    check(problem, "수평면 블록", ["T - f = m_Aa", "m_Bg - T = m_Ba"], [], must_ambiguity=["마찰 유무"])


CARTESIAN_POSITION = [
    r"질점의 위치는 r(t)=3t\hat{i}+2t^2\hat{j} 이다. 속도와 가속도는?",
    "질점의 위치가 r(t) = 3t i + 2t² j 로 주어진다. 속도와 가속도를 구하라.",
    "position vector r(t)=3t i + 2t^2 j. Find velocity and acceleration.",
    "입자의 위치벡터가 r(t)=t²î+t³ĵ 이다.",
    "r(t)=2t i - 5t^2 j 로 주어진 position vector의 v,a를 구하라.",
    "위치벡터 r(t)=4t i + t^3 j 에서 속도와 가속도.",
    "unit vector i and j components are given for r(t).",
    "i-hat, j-hat 성분 위치벡터가 주어졌다.",
    r"r(t)=t^2\hat{i}-t\hat{j} 위치벡터를 미분하라.",
    "질점의 위치가 벡터로 주어짐: r(t)=3t i+2t^2 j.",
    "x(t)=t^2, y(t)=t^3 로 주어진다. 속도와 가속도를 구하라.",
    "위치가 x=t^2, y=t^3로 주어진 입자 운동학.",
    "position vector in i and j directions is r(t)=t i + t² j.",
    "r(t)=3tî+2t²ĵ인 직교좌표 위치벡터.",
    "질점 위치벡터 r(t) = (3t)i + (2t^2)j.",
]
POLAR_POSITION = [
    "입자가 극좌표 r=2t, theta=t²로 움직인다. 가속도를 구하라.",
    "polar coordinate에서 r(t)=2t, θ(t)=t²이다.",
    "r(t), theta(t)가 주어진 극좌표 운동.",
    "e_r, e_θ 성분으로 속도와 가속도를 구하라.",
    "radial transverse coordinates에서 r과 theta가 주어진다.",
    "r=2t and theta=t^2 in polar coordinates.",
    "극좌표에서 r의 시간함수와 각도 θ가 시간에 따라 변함.",
    "r_dot과 theta_dot을 이용해 가속도를 구하라.",
    "particle has r(t)=2t and θ(t)=t^2.",
    "polar motion with radial/transverse components.",
    "r-theta 좌표에서 입자가 움직인다.",
    "r, θ 좌표계로 주어진 운동.",
    "theta(t)와 r(t)가 함께 주어진다.",
    "극좌표 속도식을 사용하라.",
    "e_theta 방향 가속도를 구하라.",
]


@pytest.mark.parametrize("problem", CARTESIAN_POSITION)
def test_cartesian_position_vector_variants(problem):
    check(problem, "위치 함수", ["r(t) = x(t)i + y(t)j", "v(t) = dr/dt", "a(t) = d²r/dt²"], ["극좌표 가속도식", "e_r", "e_θ"], ["극좌표 가속도식", "e_r, e_θ 기반 식"])


@pytest.mark.parametrize("problem", POLAR_POSITION)
def test_polar_not_misclassified_as_cartesian(problem):
    d = diagnose(problem)
    assert "위치 함수 기반" not in d.problem_model.problem_type, d.problem_model.problem_type
    text = joined(d.blueprint.applicable_equations + d.blueprint.auxiliary_equations + d.problem_model.constraints)
    assert ("e_r" in text or "e_θ" in text or "theta" in text or "θ" in text), text


BULLET_ROTATING_BODY = [
    "총알이 회전판의 가장자리에 박힌 후 회전판과 함께 고정축을 중심으로 돈다.",
    "탄환이 원판 가장자리에 박힌 뒤 원판이 고정축 주위로 회전한다.",
    "bullet sticks into the edge of a disk about a fixed axis.",
    "탄환이 막대 끝에 박힌다. 충돌 직후 각속도를 구하라.",
    "총알이 원반에 박혀서 함께 돈다. 고정축 기준 각속도를 구하라.",
    "bullet embedded in a wheel, find angular speed just after impact.",
    "탄환이 바퀴 가장자리에 박힌 후 함께 회전한다.",
    "총알이 진자막대에 박혀서 막대와 함께 돈다.",
    "bullet lodges in a rod pinned at O.",
    "탄환이 고정축 강체에 박힌다. 충돌 직후 ω를 구하라.",
    "총알이 회전판에 박힌 뒤 fixed axis around 회전한다.",
    "탄환이 원판 edge에 박힌 후 각속도를 구하라.",
    "bullet sticks into rotating body and they rotate together.",
    "총알이 막대에 박힌 후 막대와 함께 회전한다.",
    "탄환이 회전축이 있는 원반에 박힌다.",
    "bullet embedded at rim of disk; angular momentum about fixed axis.",
    "탄환이 바퀴에 박힌 뒤 함께 회전한다. 선운동량 보존 가능?",
    "총알이 회전강체에 박혀서 함께 돈다. 충돌 직후 각속도.",
    "bullet sticks into a bar about a fixed axis.",
    "탄환-원판 충돌에서 고정축 기준 각운동량 보존을 이용하라.",
    "총알이 회전판 rim에 박히고 함께 돈다.",
    "탄환이 원반 가장자리에 embedded 된다.",
    "bullet hits and lodges in a wheel on a fixed axis.",
    "총알이 막대 끝에 박혀서 핀 주위로 돈다.",
    "탄환이 회전판의 가장자리에 박힘. 각속도는?",
    "bullet is embedded in a pendulum rod; find ω after impact.",
    "탄환이 진자막대 끝에 박힌 뒤 회전한다.",
    "총알이 원판에 박힌다. 축 주위 회전 직후 각속도.",
    "bullet sticks into disk edge; fixed axis impulse problem.",
    "탄환이 고정축 원판 가장자리에 박힌 후 함께 회전한다.",
]


@pytest.mark.parametrize("problem", BULLET_ROTATING_BODY)
def test_bullet_rotating_body_collision_variants(problem):
    check(problem, "탄환", ["H_O(before) = H_O(after)", "m_b v r = I_total ω"], ["m1v1i + m2v2i = m1v1f + m2v2f"], ["선운동량 보존"])


def test_semantic_variation_case_counts():
    suites = {
        "banked_curve": BANKED_MAX + BANKED_MIN + BANKED_FRICTIONLESS,
        "conical_pendulum": CONICAL_FULL + CONICAL_AMBIGUOUS,
        "slip_rolling": SLIP_ROLLING,
        "vertical_circle": VERTICAL_BOTTOM_STRING + VERTICAL_TOP_STRING + VERTICAL_BOTTOM_TRACK,
        "horizontal_block_friction": FRICTIONLESS_HORIZONTAL + FRICTION_PRESENT_HORIZONTAL + FRICTION_UNKNOWN_HORIZONTAL,
        "position_vectors": CARTESIAN_POSITION + POLAR_POSITION,
        "bullet_rotating_body": BULLET_ROTATING_BODY,
    }
    too_small = {name: len(cases) for name, cases in suites.items() if len(cases) < 30}
    assert not too_small, f"Each semantic suite must have at least 30 cases: {too_small}"
