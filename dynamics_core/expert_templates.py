from __future__ import annotations

import re
from typing import Dict, Iterable, List

from .models import FeatureReport, ProblemModel, Recommendation, SolutionBlueprint
from .parser import normalize_text


def _uniq(items: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        if not item:
            continue
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _has(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def _extend_unique(target: List[str], items: Iterable[str]) -> None:
    target[:] = _uniq([*items, *target])


def _append_unique(target: List[str], items: Iterable[str]) -> None:
    target[:] = _uniq([*target, *items])


def _set_type(model: ProblemModel, problem_type: str) -> None:
    # More specific expert templates should replace broad labels.
    if problem_type:
        model.problem_type = problem_type


def apply_expert_templates(
    problem: str,
    model: ProblemModel,
    features: FeatureReport,
    rec: Recommendation,
    blueprint: SolutionBlueprint,
) -> SolutionBlueprint:
    """Inject representative dynamics problem skeletons.

    This is not a symbolic solver. It is a curated expert-template layer that turns
    common undergraduate dynamics patterns into concrete FBD, coordinate and
    equation skeletons. Templates deliberately include conditions and warnings so
    the app does not overclaim automatic solution ability.
    """
    text = normalize_text(problem)
    cues = features.cues

    # Template priority matters. Specific templates should run before broader ones.
    _template_massive_pulley(text, model, blueprint)
    _template_ideal_pulley(text, model, blueprint)
    _template_flat_curve(text, model, blueprint)
    _template_vertical_circle(text, model, blueprint)
    _template_drag_motion(text, model, blueprint, cues)
    _template_polar(text, model, blueprint, cues)
    _template_rolling(text, model, blueprint, cues)
    _template_instant_center(text, model, blueprint, cues)
    _template_collision_restitution(text, model, blueprint, cues)
    _template_angular_momentum(text, model, blueprint, cues)
    _template_incline_energy(text, model, blueprint, cues)
    _template_projectile(text, model, blueprint, cues)
    _template_fixed_axis(text, model, blueprint, cues)
    _template_straight_kinematics(text, model, blueprint, cues)
    _template_normal_tangent(text, model, blueprint, cues)
    _template_impulse(text, model, blueprint, cues)
    _template_translation_only(text, model, blueprint, cues)

    blueprint.fbd_forces = _uniq(blueprint.fbd_forces)
    blueprint.coordinate_guide = _uniq(blueprint.coordinate_guide)
    blueprint.governing_equations = _uniq(blueprint.governing_equations)
    blueprint.auxiliary_equations = _uniq(blueprint.auxiliary_equations)
    blueprint.application_conditions = _uniq(blueprint.application_conditions)
    blueprint.next_steps = _uniq(blueprint.next_steps)[:16]
    blueprint.warnings = _uniq(blueprint.warnings)
    blueprint.interpretation_checks = _uniq(blueprint.interpretation_checks)
    model.analysis_targets = _uniq(model.analysis_targets)
    model.forces_present = _uniq(model.forces_present)
    model.forces_ignored = _uniq(model.forces_ignored)
    model.constraints = _uniq(model.constraints)
    model.coordinate_systems = _uniq(model.coordinate_systems)
    model.allowed_methods = _uniq(model.allowed_methods)
    model.risky_methods = _uniq(model.risky_methods)
    model.conservation_conditions = _uniq(model.conservation_conditions)
    return blueprint


def _template_ideal_pulley(text: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    if not _has(text, r"도르래|pulley|줄로\s*연결|로프.*연결|connected"):
        return
    if _has(text, r"관성모멘트|질량\s*있는\s*도르래|무게\s*있는\s*도르래|massive\s+pulley|pulley\s+with\s+inertia|I\s*="):
        return
    _set_type(model, "연결된 물체/이상적 도르래 문제")
    _extend_unique(model.analysis_targets, ["물체 1", "물체 2"])
    _extend_unique(model.constraints, ["이상적 줄: 같은 줄의 장력은 같다", "늘어나지 않는 줄: 두 물체의 가속도 크기는 같다"])
    _extend_unique(model.coordinate_systems, ["무거운 쪽 물체의 실제 운동 방향을 +로 잡음", "다른 물체는 줄 구속조건에 맞춰 같은 크기의 a를 사용"])
    _extend_unique(model.allowed_methods, ["뉴턴 제2법칙 F=ma", "연립방정식"])
    _extend_unique(bp.fbd_forces, ["물체 1: 중력 m1g, 장력 T", "물체 2: 중력 m2g, 장력 T"])
    _extend_unique(bp.coordinate_guide, ["m1이 아래로 움직인다고 가정하면 m1의 아래 방향을 +", "m2는 위 방향을 +로 잡아 같은 a를 사용"])
    _extend_unique(bp.governing_equations, ["m1g - T = m1a", "T - m2g = m2a"])
    _extend_unique(bp.auxiliary_equations, ["같은 줄의 장력은 같다: T1 = T2 = T", "가속도 크기는 같다: |a1| = |a2| = a"])
    _extend_unique(bp.application_conditions, ["도르래와 줄의 질량을 무시하고, 도르래 마찰도 무시할 때 T1 = T2 가능"])
    _extend_unique(bp.next_steps, ["각 물체를 따로 떼어 FBD를 그린다.", "같은 줄이면 장력을 T로 둔다.", "가속도 크기가 같다는 구속조건으로 두 식을 연립한다.", "구한 a의 부호로 실제 운동 방향을 해석한다."])
    _extend_unique(bp.warnings, ["한 물체만 보면 장력을 제거할 수 없다.", "장력 방향을 반대로 잡아도 결과 부호로 해석하면 된다."])


def _template_massive_pulley(text: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    if not _has(text, r"도르래|pulley"):
        return
    if not _has(text, r"관성모멘트|질량\s*있는\s*도르래|무게\s*있는\s*도르래|massive\s+pulley|pulley\s+with\s+inertia|I\s*="):
        return
    _set_type(model, "질량 있는 도르래 문제")
    _extend_unique(model.analysis_targets, ["물체 1", "물체 2", "도르래"])
    _extend_unique(model.constraints, ["질량 있는 도르래에서는 일반적으로 T1 ≠ T2", "줄이 도르래에서 미끄러지지 않으면 a = αR"])
    _extend_unique(model.coordinate_systems, ["물체는 줄 방향", "도르래는 회전 양의 방향을 T1이 만드는 모멘트 방향으로 설정"])
    _extend_unique(model.risky_methods, ["질량 있는 도르래에서 T1 = T2라고 두는 것"])
    _extend_unique(bp.fbd_forces, ["물체 1: 중력 m1g, 장력 T1", "물체 2: 중력 m2g, 장력 T2", "도르래: 양쪽 장력 T1, T2, 축 반력"])
    _extend_unique(bp.coordinate_guide, ["무거운 쪽을 아래 방향 +로 가정", "도르래 회전 방향은 줄의 운동방향과 일치하도록 설정"])
    _extend_unique(bp.governing_equations, ["m1g - T1 = m1a", "T2 - m2g = m2a", "(T1 - T2)R = Iα"])
    _extend_unique(bp.auxiliary_equations, ["미끄럼 없음: a = αR", "질량 있는 도르래: T1 ≠ T2"])
    _extend_unique(bp.application_conditions, ["도르래 관성모멘트 I가 무시되지 않을 때", "줄이 도르래 위에서 미끄러지지 않을 때 a = αR 연결"])
    _extend_unique(bp.next_steps, ["두 물체와 도르래를 각각 따로 분석한다.", "양쪽 장력을 T1, T2로 다르게 둔다.", "도르래에 대해 모멘트 방정식을 세운다.", "a = αR로 병진식과 회전식을 연결한다."])
    _extend_unique(bp.warnings, ["질량 있는 도르래에서 양쪽 장력을 같게 두면 오답 가능성이 크다."])


def _template_flat_curve(text: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    if not (_has(text, r"평평한\s*커브|수평\s*커브|flat\s+curve|level\s+curve") or (_has(text, r"자동차|차|car") and _has(text, r"커브|curve"))):
        return
    _set_type(model, "평평한 커브의 원운동/마찰 문제")
    _extend_unique(model.analysis_targets, ["자동차"])
    _extend_unique(model.constraints, ["평평한 도로에서는 마찰력이 중심 방향 힘을 제공", "미끄러지기 직전 최소/최대 조건: f_s = μ_sN"])
    _extend_unique(model.coordinate_systems, ["중심 방향 n축", "수직 방향 y축"])
    _extend_unique(model.risky_methods, ["평평한 커브에서 수직항력이 구심력이라고 보는 것"])
    _extend_unique(bp.fbd_forces, ["중력 mg: 아래 방향", "수직항력 N: 위 방향", "정지마찰력 f_s: 곡률 중심 방향"])
    _extend_unique(bp.coordinate_guide, ["중심 방향을 n축 +로 설정", "수직 위쪽을 y축 +로 설정"])
    _extend_unique(bp.governing_equations, ["N = mg", "f_s = mv²/R", "f_s ≤ μ_sN", "mv²/R ≤ μ_smg", "μ_s ≥ v²/(gR)"])
    _extend_unique(bp.auxiliary_equations, ["최대 정지마찰: f_s,max = μ_sN", "구심가속도: a_n = v²/R"])
    _extend_unique(bp.application_conditions, ["도로가 기울어지지 않은 평평한 커브", "타이어가 미끄러지지 않는 정지마찰 한계"])
    _extend_unique(bp.next_steps, ["자동차의 FBD를 그린다.", "중심 방향 힘이 무엇인지 확인한다.", "평평한 도로에서는 마찰력이 구심력을 제공한다.", "mv²/R ≤ μ_smg를 세우고 μ_s에 대해 정리한다."])
    _extend_unique(bp.warnings, ["수직항력은 위쪽 힘이지 중심 방향 힘이 아니다.", "마찰이 부족하면 자동차는 바깥쪽으로 미끄러진다."])


def _template_vertical_circle(text: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    if not (_has(text, r"수직\s*원|원형\s*고리|원형\s*트랙|loop|vertical\s+circle|떨어지지|이탈하지|접촉\s*유지|최고점")):
        return
    if not _has(text, r"원|고리|트랙|loop|최고점|꼭대기|떨어지지|이탈하지"):
        return
    _set_type(model, "수직 원운동/접촉 유지 문제")
    _extend_unique(model.analysis_targets, ["원궤도 위 물체"])
    _extend_unique(model.constraints, ["최고점에서 중심 방향은 아래쪽", "떨어지지 않는 최소 조건은 N = 0 또는 T = 0"])
    _extend_unique(model.coordinate_systems, ["해당 지점에서 중심 방향을 +n으로 설정"])
    _extend_unique(bp.fbd_forces, ["최고점: 중력 mg는 중심 방향", "최고점: 수직항력 N 또는 장력 T도 중심 방향"])
    _extend_unique(bp.coordinate_guide, ["최고점에서는 아래쪽, 즉 원의 중심 방향을 +n으로 잡음"])
    _extend_unique(bp.governing_equations, ["최고점: mg + N = mv²/R", "최소 접촉 조건: N = 0", "mg = mv²/R", "v_min = √(gR)"])
    _extend_unique(bp.auxiliary_equations, ["필요하면 에너지식으로 최고점 속도 v를 구함"])
    _extend_unique(bp.application_conditions, ["트랙/줄이 물체를 밀거나 당길 수 있는 방향을 확인", "최소 속도는 접촉력이 0이 되는 경계 조건"])
    _extend_unique(bp.next_steps, ["관심 지점이 최고점인지 최저점인지 표시한다.", "중심 방향으로 실제 힘을 더한다.", "접촉 유지 한계에서는 N=0 또는 T=0을 둔다.", "필요하면 에너지식과 결합한다."])
    _extend_unique(bp.warnings, ["N < 0은 접촉력이 끌어당긴다는 뜻이므로 물리적으로 불가능하다."])


def _template_drag_motion(text: str, model: ProblemModel, bp: SolutionBlueprint, cues: Dict[str, bool]) -> None:
    if not (cues.get("air_resistance") or _has(text, r"공기\s*저항|저항력|drag|air\s+resistance|damping")):
        return
    _set_type(model, "저항력이 있는 운동")
    _extend_unique(model.forces_present, ["저항력 F_d: 속도 반대 방향"])
    _extend_unique(model.coordinate_systems, ["x방향과 y방향을 분리하되, 각 방향에 저항력 성분 포함"])
    _extend_unique(model.risky_methods, ["공기저항이 있는데 표준 포물선 공식 R = v0²sin2θ/g를 그대로 쓰는 것", "공기저항이 있는데 수평방향 가속도 0이라고 두는 것"])
    _extend_unique(bp.fbd_forces, ["중력 mg", "저항력 F_d = -cv 또는 F_d = -cv²"])
    _extend_unique(bp.coordinate_guide, ["x축: 수평 운동 방향", "y축: 위쪽 또는 아래쪽을 일관되게 설정"])
    if _has(text, r"속도에\s*비례|kv|cv\b|linear\s+drag"):
        _extend_unique(bp.governing_equations, ["m dv_x/dt = -c v_x", "m dv_y/dt = -mg - c v_y"])
        _extend_unique(bp.auxiliary_equations, ["속도 비례 저항: F_d = -cv"])
    elif _has(text, r"제곱|v\^2|v²|cv²|quadratic"):
        _extend_unique(bp.governing_equations, ["m dv_x/dt = -c v v_x", "m dv_y/dt = -mg - c v v_y"])
        _extend_unique(bp.auxiliary_equations, ["속도 제곱 비례 저항: F_d = -c|v|v"])
    else:
        _extend_unique(bp.governing_equations, ["ΣF = m dv/dt", "저항력 모델을 정한 뒤 성분별 미분방정식 구성"])
        _extend_unique(bp.auxiliary_equations, ["속도 비례: F_d = -cv", "속도 제곱 비례: F_d = -c|v|v"])
    _extend_unique(bp.application_conditions, ["공기저항을 고려하면 일반적으로 등가속도 운동이 아님"])
    _extend_unique(bp.next_steps, ["저항력 모델이 -cv인지 -cv²인지 확인한다.", "x, y 방향 운동방정식을 미분방정식으로 세운다.", "가능하면 해석해를 쓰고, 어려우면 수치해석이 필요하다."])
    _extend_unique(bp.warnings, ["공기저항이 있으면 수평방향 가속도가 0이 아닐 수 있다.", "표준 포물선 공식은 공기저항 무시 조건에서만 직접 적용한다."])


def _template_polar(text: str, model: ProblemModel, bp: SolutionBlueprint, cues: Dict[str, bool]) -> None:
    if not (cues.get("polar") or _has(text, r"극좌표|polar|r\s*=|theta\s*=|θ\s*=|r\(t\)|theta\(t\)|θ\(t\)|r_dot|theta_dot|e_r|e_θ")):
        return
    _set_type(model, "극좌표 운동")
    _extend_unique(model.analysis_targets, ["극좌표로 표현된 입자"])
    _extend_unique(model.coordinate_systems, ["e_r 방향", "e_θ 방향"])
    _extend_unique(model.constraints, ["r(t), θ(t)를 시간에 대해 미분해야 함"])
    _extend_unique(bp.fbd_forces, ["운동학 문제라면 FBD보다 r(t), θ(t) 미분이 우선"])
    _extend_unique(bp.coordinate_guide, ["e_r: 반지름 바깥 방향", "e_θ: θ가 증가하는 접선 방향"])
    _extend_unique(bp.governing_equations, ["v = r_dot e_r + r theta_dot e_theta", "a = (r_ddot - r theta_dot²)e_r + (r theta_ddot + 2r_dot theta_dot)e_theta"])
    _extend_unique(bp.auxiliary_equations, ["r_dot = dr/dt", "r_ddot = d²r/dt²", "theta_dot = dθ/dt", "theta_ddot = d²θ/dt²"])
    _extend_unique(bp.application_conditions, ["위치가 r, θ의 시간함수로 주어지는 평면 운동"])
    _extend_unique(bp.next_steps, ["r(t), theta(t)를 확인한다.", "r_dot, r_ddot, theta_dot, theta_ddot를 구한다.", "극좌표 속도식에 대입한다.", "극좌표 가속도식에 대입한다."])
    _extend_unique(bp.warnings, ["극좌표 가속도는 r을 두 번 미분하는 것만으로 끝나지 않는다.", "-r theta_dot²와 2r_dot theta_dot 항을 빠뜨리기 쉽다."])


def _template_rolling(text: str, model: ProblemModel, bp: SolutionBlueprint, cues: Dict[str, bool]) -> None:
    if not (cues.get("rolling") or _has(text, r"미끄러지지\s*않.*굴|굴러\s*내려|rolling|rolls\s+without\s+slipping")):
        return
    _set_type(model, "순수 구름 운동")
    _extend_unique(model.analysis_targets, ["구르는 강체의 질량중심 G"])
    _extend_unique(model.constraints, ["미끄러지지 않음: v_G = ωR", "미끄러지지 않음: a_G = αR"])
    _extend_unique(model.conservation_conditions, ["손실이 없으면 병진 운동에너지와 회전 운동에너지를 모두 포함"])
    _extend_unique(model.risky_methods, ["미끄러짐이 있는데 v_G = ωR을 쓰는 것"])
    _extend_unique(bp.fbd_forces, ["중력 mg", "수직항력 N", "정지마찰력 f_s"])
    _extend_unique(bp.coordinate_guide, ["질량중심 G의 병진방향", "회전 양의 방향"])
    _extend_unique(bp.governing_equations, ["mgh = 1/2mv_G² + 1/2I_Gω²", "v_G = ωR", "a_G = αR", "ΣM_G = I_Gα"])
    _extend_unique(bp.auxiliary_equations, ["원통: I_G = 1/2mR²", "구: I_G = 2/5mR²", "속도 계산 시 ω = v_G/R"])
    _extend_unique(bp.application_conditions, ["접점에서 미끄러지지 않는 순수 구름", "정지마찰은 접점에서 일을 하지 않는 경우가 많음"])
    _extend_unique(bp.next_steps, ["미끄러짐 여부를 먼저 확인한다.", "병진 에너지와 회전 에너지를 모두 포함한다.", "ω = v_G/R을 사용한다.", "물체 모양에 맞는 관성모멘트 I_G를 대입한다."])
    _extend_unique(bp.warnings, ["미끄러지면 v_G = ωR을 쓸 수 없다."])


def _template_instant_center(text: str, model: ProblemModel, bp: SolutionBlueprint, cues: Dict[str, bool]) -> None:
    if not (cues.get("instant_center") or _has(text, r"순간\s*중심|instantaneous\s+center|center\s+of\s+zero\s+velocity")):
        return
    _set_type(model, "강체 일반 평면운동/상대속도/순간중심 문제")
    _extend_unique(model.analysis_targets, ["강체 위 기준점 A", "관심점 B", "순간중심 IC"])
    _extend_unique(model.constraints, ["각 점의 속도 방향에 수직인 선들의 교점이 순간중심", "순간중심 기준으로 v = ωr"])
    _extend_unique(model.coordinate_systems, ["강체 평면 내 x-y 좌표", "각 점 속도 방향에 수직인 보조선"])
    _extend_unique(bp.fbd_forces, ["속도해석 문제라면 힘보다 각 점의 속도 방향 표시가 우선"])
    _extend_unique(bp.coordinate_guide, ["A점 속도 방향", "B점 속도 방향", "각 속도 방향에 수직인 선으로 IC 탐색"])
    _extend_unique(bp.governing_equations, ["v_B = v_A + ω × r_B/A", "v_A = ω r_A/IC", "v_B = ω r_B/IC"])
    _extend_unique(bp.auxiliary_equations, ["ω = v_A / r_A/IC", "v_B = ω r_B/IC"])
    _extend_unique(bp.application_conditions, ["강체가 한 순간 평면운동을 하고, 속도 방향 정보가 충분할 때"])
    _extend_unique(bp.next_steps, ["각 점의 속도 방향을 확인한다.", "속도 방향에 수직인 선을 그린다.", "두 수직선의 교점을 순간중심 IC로 잡는다.", "ω = v_A/r_A/IC를 구한다.", "v_B = ωr_B/IC로 관심점 속도를 구한다."])
    _extend_unique(bp.warnings, ["순간중심은 그 순간 속도가 0인 점이지 실제 고정점일 필요는 없다.", "속도 방향 정보가 부족하면 순간중심을 결정할 수 없다."])


def _template_collision_restitution(text: str, model: ProblemModel, bp: SolutionBlueprint, cues: Dict[str, bool]) -> None:
    if not ((cues.get("collision") and not cues.get("no_collision")) or _has(text, r"반발계수|coefficient\s+of\s+restitution|충돌\s*후|collision")):
        return
    _set_type(model, "충격량-운동량/충돌 문제")
    _extend_unique(model.analysis_targets, ["두 물체를 하나의 계로 설정"])
    _extend_unique(model.constraints, ["충돌 전/후 상태를 분리", "충돌 시간 동안 외부 충격량이 무시 가능해야 운동량 보존 가능"])
    _extend_unique(model.risky_methods, ["완전탄성 조건 없이 운동에너지 보존을 가정하는 것"])
    _extend_unique(bp.fbd_forces, ["충돌 동안 내부 충격력은 계 내부 힘", "외부 충격량이 무시 가능한지 확인"])
    _extend_unique(bp.coordinate_guide, ["1차원 충돌이면 한 방향을 +로 정하고 모든 속도 부호를 통일"])
    _extend_unique(bp.governing_equations, ["m1v1i + m2v2i = m1v1f + m2v2f", "e = (v2f - v1f)/(v1i - v2i)"])
    _extend_unique(bp.auxiliary_equations, ["완전비탄성 충돌: v1f = v2f", "완전탄성 충돌: e = 1", "완전탄성 충돌에서는 운동에너지 보존도 가능"])
    _extend_unique(bp.application_conditions, ["계 전체에 대한 외부 충격량이 충돌 시간 동안 무시 가능해야 함"])
    _extend_unique(bp.next_steps, ["계와 +방향을 정한다.", "충돌 전 속도와 충돌 후 속도를 분리한다.", "운동량 보존식과 반발계수식을 함께 세운다.", "완전비탄성이라면 공동속도 조건을 추가한다."])
    _extend_unique(bp.warnings, ["운동량 보존과 운동에너지 보존은 항상 동시에 성립하지 않는다.", "외부 충격량이 크면 운동량 보존을 바로 쓰면 안 된다."])


def _template_angular_momentum(text: str, model: ProblemModel, bp: SolutionBlueprint, cues: Dict[str, bool]) -> None:
    if not (cues.get("angular_momentum") or _has(text, r"각운동량|angular\s+momentum|moment\s+of\s+momentum")):
        return
    _set_type(model, "각운동량 보존 문제")
    _extend_unique(model.analysis_targets, ["기준점 O에 대한 질점 또는 강체"])
    _extend_unique(model.constraints, ["기준점에 대한 외부 모멘트가 0이면 각운동량 보존"])
    _extend_unique(model.coordinate_systems, ["각운동량을 계산할 기준점 O 선택"])
    _extend_unique(model.risky_methods, ["기준점에 대한 외부 모멘트가 0인지 확인하지 않고 각운동량 보존을 쓰는 것"])
    _extend_unique(bp.fbd_forces, ["기준점 O에 대해 외부 모멘트를 만드는 힘만 확인"])
    _extend_unique(bp.coordinate_guide, ["O점 기준인지, 질량중심 G 기준인지 먼저 결정"])
    _extend_unique(bp.governing_equations, ["ΣM_O = dH_O/dt", "외부모멘트가 0이면 H_O1 = H_O2", "질점: H_O = r × mv", "강체: H_G = I_Gω"])
    _extend_unique(bp.auxiliary_equations, ["원운동 질점이면 H_O = mrv_t"])
    _extend_unique(bp.application_conditions, ["선운동량 보존과 달리 기준점 선택이 중요", "충돌/짧은 시간 문제에서는 기준점에 대한 외부 충격모멘트가 작은지 확인"])
    _extend_unique(bp.next_steps, ["각운동량 기준점을 정한다.", "그 기준점에 대한 외부 모멘트가 0인지 본다.", "초기/최종 H를 같은 기준점으로 쓴다.", "H_O1 = H_O2 또는 ΣM_O = dH_O/dt를 적용한다."])
    _extend_unique(bp.warnings, ["기준점을 잘못 잡으면 외부 모멘트가 0이 아닐 수 있다."])


def _template_incline_energy(text: str, model: ProblemModel, bp: SolutionBlueprint, cues: Dict[str, bool]) -> None:
    if not (cues.get("incline") and (cues.get("height") or cues.get("no_friction") or _has(text, r"속도|speed|velocity"))):
        return
    _extend_unique(bp.fbd_forces, ["경사면 물체: 중력 mg, 수직항력 N", "마찰이 없으면 f=0, 마찰이 있으면 f=μN"])
    _extend_unique(bp.coordinate_guide, ["경사면 평행 방향", "경사면 수직 방향"])
    if cues.get("no_friction") and (cues.get("height") or _has(text, r"높이|h\s*=")):
        _extend_unique(bp.governing_equations, ["mgh = 1/2mv²"])
        _extend_unique(bp.auxiliary_equations, ["질량 m은 약분됨", "수직항력은 이동 방향에 수직이라 일을 하지 않음"])
        _extend_unique(bp.warnings, ["경사각이 없으면 F=ma보다 에너지 방법이 더 직접적일 수 있다."])
    else:
        _extend_unique(bp.governing_equations, ["ΣF_parallel = ma", "ΣF_perpendicular = 0", "f = μN"])


def _template_projectile(text: str, model: ProblemModel, bp: SolutionBlueprint, cues: Dict[str, bool]) -> None:
    if not cues.get("projectile"):
        return
    if cues.get("air_resistance"):
        return
    _extend_unique(bp.governing_equations, ["x = x0 + v0cosθ · t", "y = y0 + v0sinθ · t - 1/2gt²", "v_y = v0sinθ - gt"])
    _extend_unique(bp.auxiliary_equations, ["v0x = v0cosθ", "v0y = v0sinθ", "최고점: v_y = 0"])
    _extend_unique(bp.warnings, ["공기저항이 없는 경우에만 수평방향 가속도 0을 둔다."])


def _template_fixed_axis(text: str, model: ProblemModel, bp: SolutionBlueprint, cues: Dict[str, bool]) -> None:
    if not cues.get("fixed_axis"):
        return
    _set_type(model, "강체 고정축 회전")
    _extend_unique(bp.governing_equations, ["ΣM_O = I_Oα", "ω = ω0 + αt", "ω² = ω0² + 2αθ"])
    _extend_unique(bp.auxiliary_equations, ["O축을 지나는 반력은 O점 기준 모멘트가 0일 수 있음"])
    _extend_unique(bp.warnings, ["회전축이 고정되어 있는지, 질량중심도 병진하는지 먼저 구분한다."])


def _template_translation_only(text: str, model: ProblemModel, bp: SolutionBlueprint, cues: Dict[str, bool]) -> None:
    if not (cues.get("translation_only") and cues.get("no_rotation")):
        return
    _set_type(model, "순수 병진운동")
    _extend_unique(bp.governing_equations, ["회전 없음: α = 0", "모든 점의 속도와 가속도는 같음", "필요한 경우 ΣF = ma_G만 사용"])
    _extend_unique(bp.warnings, ["막대/강체라는 단어가 있어도 회전하지 않으면 ΣM=Iα를 우선 쓰지 않는다."])


def _template_straight_kinematics(text: str, model: ProblemModel, bp: SolutionBlueprint, cues: Dict[str, bool]) -> None:
    if not ((cues.get("time") or cues.get("distance") or cues.get("constant_accel")) and not (cues.get("force") or cues.get("tension") or cues.get("friction") or cues.get("rotation") or cues.get("circular") or cues.get("incline") or cues.get("height") or cues.get("spring") or cues.get("projectile") or cues.get("polar"))):
        return
    _set_type(model, "질점 직선 운동학")
    _extend_unique(model.coordinate_systems, ["운동 방향을 x축 +로 설정"])
    _extend_unique(model.constraints, ["등가속도 조건이 성립할 때만 표준 등가속도 공식 사용"] )
    _extend_unique(bp.coordinate_guide, ["운동 방향을 x축 +로 설정", "부호는 처음에 정한 +방향 기준으로 통일"] )
    _extend_unique(bp.governing_equations, ["v = v0 + at", "s = v0t + 1/2at²", "v² = v0² + 2as"] )
    _extend_unique(bp.application_conditions, ["가속도 a가 일정한 직선운동일 때"] )
    _extend_unique(bp.next_steps, ["u, v, a, s, t 중 주어진 값과 구할 값을 표로 정리한다.", "시간이 있으면 v=v0+at 또는 s=v0t+1/2at²를 우선 확인한다.", "시간이 없고 변위가 있으면 v²=v0²+2as를 확인한다."] )
    _extend_unique(bp.warnings, ["가속도가 일정하지 않으면 등가속도 공식을 그대로 쓰면 안 된다."] )


def _template_normal_tangent(text: str, model: ProblemModel, bp: SolutionBlueprint, cues: Dict[str, bool]) -> None:
    if not (cues.get("normal_tangent") or _has(text, r"곡률반지름|법선|접선|normal[-\s]*tangential")):
        return
    _set_type(model, "법선-접선 좌표계 운동")
    _extend_unique(model.coordinate_systems, ["n축: 곡률 중심 방향", "t축: 속도 방향"] )
    _extend_unique(bp.coordinate_guide, ["n축은 항상 곡률 중심 방향", "t축은 순간 속도 방향"] )
    _extend_unique(bp.governing_equations, ["a_n = v²/ρ", "a_t = dv/dt", "ΣF_n = m v²/ρ", "ΣF_t = m a_t"] )
    _extend_unique(bp.application_conditions, ["곡선 경로의 곡률반지름 ρ가 주어지거나 구할 수 있을 때"] )
    _extend_unique(bp.warnings, ["n방향 가속도는 속도 크기가 일정해도 v²/ρ로 남는다."] )


def _template_impulse(text: str, model: ProblemModel, bp: SolutionBlueprint, cues: Dict[str, bool]) -> None:
    if not cues.get("impulse"):
        return
    _set_type(model, "충격량-운동량 문제")
    _extend_unique(bp.governing_equations, ["J = ∫F dt = Δp", "J = m(v2 - v1)"] )
    _extend_unique(bp.application_conditions, ["짧은 시간 동안 큰 힘이 작용하고 위치 변화는 작다고 볼 때"] )
    _extend_unique(bp.next_steps, ["충격 전/후 속도 부호를 통일한다.", "힘-시간 그래프가 있으면 면적으로 충격량 J를 구한다."] )
