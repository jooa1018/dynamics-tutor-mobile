from __future__ import annotations

import re
from typing import Iterable, List, Sequence

from .models import FeatureReport, ProblemModel, Recommendation, SolutionBlueprint
from .parser import normalize_text
from .semantic_normalizer import semantic_flags
from .consistency_guard import apply_final_consistency_guard


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


def _has_any(text: str, patterns: Sequence[str]) -> bool:
    return any(_has(text, pattern) for pattern in patterns)


def _friction_state(text: str, features: FeatureReport) -> str:
    """Return 'none', 'present', or 'unknown'.

    공통 의미 정규화 계층을 사용합니다. 마찰 무시/없음 표현은 μ나
    friction 단어보다 우선합니다.
    """
    sem = semantic_flags(text)
    if features.cues.get("no_friction") or sem.frictionless:
        return "none"
    if _has(text, r"friction\s+not\s+specified|마찰\s*(?:조건|유무).*주어지지|마찰\s*조건은?\s*불명"):
        return "unknown"
    if features.cues.get("friction") or sem.friction_present:
        return "present"
    return "unknown"


def _sync(bp: SolutionBlueprint, text: str = "") -> SolutionBlueprint:
    """Keep 3차 필드와 4차 필드를 동기화하고 최종 일관성 검사를 적용합니다."""
    bp.fbd_forces = _uniq(bp.fbd_forces)
    bp.coordinate_guide = _uniq(bp.coordinate_guide)
    bp.applicable_equations = _uniq(bp.applicable_equations or bp.governing_equations)
    bp.governing_equations = list(bp.applicable_equations)
    bp.not_applicable_equations = _uniq(bp.not_applicable_equations)
    bp.auxiliary_equations = _uniq(bp.auxiliary_equations)
    bp.application_conditions = _uniq(bp.application_conditions)
    bp.next_steps = _uniq(bp.next_steps)
    bp.cautions = _uniq(bp.cautions or bp.warnings)
    bp.warnings = _uniq([*bp.warnings, *bp.cautions])
    bp.interpretation_checks = _uniq(bp.interpretation_checks)
    bp.suppressed_templates = _uniq(bp.suppressed_templates)
    bp.ambiguity_notes = _uniq(bp.ambiguity_notes)
    if text:
        _final_consistency_guard(bp, text)
    return bp


def _final_consistency_guard(bp: SolutionBlueprint, text: str) -> None:
    """최종 출력 직전에 서로 충돌하는 적용식/주의식을 정리합니다."""
    sem = semantic_flags(text)
    def remove_app(patterns: Sequence[str]) -> None:
        bp.applicable_equations = [eq for eq in bp.applicable_equations if not any(p in eq for p in patterns)]
    def add_not(item: str) -> None:
        if item not in bp.not_applicable_equations:
            bp.not_applicable_equations.append(item)
    rolling_slip_context = sem.slip_present and (sem.rolling_word or sem.rotation_word or _has(text, r"원통|원반|원판|바퀴|cylinder|disk|wheel"))
    if rolling_slip_context:
        remove_app(["v_G = ωR", "a_G = αR", "mgh = 1/2mv_G² + 1/2I_Gω²"])
        add_not("v_G = ωR : 미끄럼이 있으면 적용식으로 사용 불가")
        add_not("a_G = αR : 미끄럼이 있으면 적용식으로 사용 불가")
        if not any("f_k = μ_kN" in eq for eq in bp.applicable_equations):
            bp.applicable_equations.append("f_k = μ_kN")
    if sem.explicit_pure_rolling and not sem.slip_present:
        bp.not_applicable_equations = [eq for eq in bp.not_applicable_equations if not ("v_G = ωR" in eq and "적용" in eq) and not ("a_G = αR" in eq and "적용" in eq)]
    if sem.frictionless:
        remove_app(["f = μN", "f = μN_A", "f = μ_sN", "f_s ≤ μ_sN", "μ_s ≥ v²/(gR)", "f_k = μ_kN", "μ_kN"])
        if "f = 0" not in bp.applicable_equations and (sem.horizontal_table or "frictionless" in text.lower() or "마찰" in text):
            bp.applicable_equations.insert(0, "f = 0")
    if sem.cartesian_position_vector:
        remove_app(["e_r", "e_θ", "theta_dot", "thetȧ"])
        add_not("극좌표 가속도식 : i, j 또는 <x,y> 직교좌표 위치벡터에서는 우선 적용 금지")
    # 선택된 템플릿인데 적용식이 비는 상황 방지
    if not bp.applicable_equations:
        if sem.banked_curve and sem.max_speed:
            bp.applicable_equations.extend(["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"])
        elif sem.banked_curve and sem.min_speed:
            bp.applicable_equations.extend(["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"])
        elif sem.track_support and sem.bottom_position:
            bp.applicable_equations.extend(["N - mg = mv²/R", "N = mg + mv²/R"])
        elif (sem.conical_explicit or sem.conical_structural or sem.conical_candidate) and not (sem.horizontal_table and sem.hanging_mass and sem.pulley):
            bp.applicable_equations.extend(["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"])
    apply_final_consistency_guard(bp, text)
    bp.applicable_equations = _uniq(bp.applicable_equations)
    bp.not_applicable_equations = _uniq(bp.not_applicable_equations)


def _replace(
    bp: SolutionBlueprint,
    *,
    title: str,
    fbd: Sequence[str],
    coordinates: Sequence[str],
    applicable: Sequence[str],
    auxiliary: Sequence[str] = (),
    conditions: Sequence[str] = (),
    steps: Sequence[str] = (),
    cautions: Sequence[str] = (),
    not_applicable: Sequence[str] = (),
    suppressed: Sequence[str] = (),
    ambiguity: Sequence[str] = (),
    support_level: str = "대표 유형 풀이 골격 생성",
) -> None:
    bp.title = title
    bp.fbd_forces = _uniq(fbd)
    bp.coordinate_guide = _uniq(coordinates)
    bp.applicable_equations = _uniq(applicable)
    bp.governing_equations = list(bp.applicable_equations)
    bp.auxiliary_equations = _uniq(auxiliary)
    bp.application_conditions = _uniq(conditions)
    bp.next_steps = _uniq(steps)
    bp.cautions = _uniq(cautions)
    bp.warnings = _uniq(cautions)
    bp.not_applicable_equations = _uniq(not_applicable)
    bp.suppressed_templates = _uniq(suppressed)
    bp.ambiguity_notes = _uniq(ambiguity)
    bp.support_level = support_level


def apply_fourth_rework_templates(
    problem: str,
    model: ProblemModel,
    features: FeatureReport,
    rec: Recommendation,
    bp: SolutionBlueprint,
) -> SolutionBlueprint:
    """4차 개선: 구조화된 적용식/금지식/배제 템플릿 레이어.

    3차 전문가 템플릿은 맞는 식을 추가하는 데 강했습니다. 이 레이어는
    교재형 복합 문제에서 잘못된 일반 템플릿이 적용식처럼 섞이지 않도록
    더 구체적인 템플릿을 우선 적용하고, 배제된 템플릿과 금지식을 별도 영역에 둡니다.
    """
    text = normalize_text(problem)

    # 가장 구체적인 복합 유형을 먼저 판정합니다.
    for detector in (
        _bullet_rod_collision,
        _horizontal_block_hanging_mass,
        _inclined_block_hanging_mass,
        _massive_pulley,
        _movable_pulley,
        _banked_curve,
        _conical_pendulum,
        _rolling_with_slipping,
        _position_function_kinematics,
        _variable_force_work,
        _time_dependent_impulse,
        _ladder_instant_center,
        _slot_pin_relative_motion,
        _pure_rolling,
        _flat_curve,
        _vertical_circle,
        _collision_restitution,
        _angular_momentum,
        _fixed_axis,
        _general_plane_motion,
        _ambiguous_pulley,
    ):
        if detector(text, model, features, bp):
            return _sync(bp, text)

    # 특정 구조가 아니면 3차 결과를 구조화 필드에 복사합니다.
    return _sync(bp, text)


def _horizontal_block_hanging_mass(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    sem = semantic_flags(text)
    if not (sem.horizontal_table and (sem.hanging_mass or _has(text, r"매달|hanging|suspended|추")) and (sem.pulley or sem.frictionless or _has(text, r"도르래|pulley|줄로\s*연결|로프|tied|connected|블록.*매달|매달.*블록|매달린\s*추|hanging\s+(?:block|mass|B)"))):
        return False
    friction_state = _friction_state(text, features)
    model.problem_type = "수평면 블록 + 매달린 물체 연결 문제"
    model.analysis_targets = ["수평면 위 블록 A", "매달린 물체 B"]
    model.constraints = ["같은 줄로 연결되어 두 물체의 가속도 크기는 같다", "수평면 블록은 수직 방향 가속도가 0"]
    model.risky_methods = ["블록 A를 수직 매달림 물체처럼 m_Ag - T = m_Aa로 처리하는 것"]

    applicable = ["N_A = m_Ag", "m_Bg - T = m_Ba"]
    auxiliary = ["줄 조건: |a_A| = |a_B| = a"]
    cautions = ["일반 애트우드 장치가 아니다.", "블록 A에 m_Ag - T = m_Aa를 적용하면 안 된다."]
    if _has(text, r"\btable\b|테이블|탁자") and not _has(text, r"수평|horizontal|level"):
        cautions.append("테이블은 일반 교재 문맥상 수평면으로 해석했습니다. 문제 그림에서 기울어진 테이블이면 별도 조건이 필요합니다.")
    not_applicable = ["m_Ag - T = m_Aa : 블록 A는 수평면 위에 있으므로 적용 불가", "T - m_Ag = m_Aa : 블록 A를 매달린 물체처럼 본 식이므로 적용 불가"]
    ambiguity = []

    if friction_state == "none":
        applicable += ["f = 0", "T = m_Aa"]
        auxiliary += ["일반식 T - f = m_Aa에서 f = 0을 대입하면 T = m_Aa"]
        not_applicable += ["f = μN_A = μm_Ag : 마찰 없는 수평면에서는 적용 불가", "T - f = m_Aa : 최종 적용식은 f = 0을 대입해 T = m_Aa로 정리"]
        cautions += ["마찰 없음/매끄러운 면 조건이 μ 또는 마찰계수 언급보다 우선한다."]
    elif friction_state == "present":
        applicable += ["f = μN_A = μm_Ag", "T - f = m_Aa"]
    else:
        applicable += ["T - f = m_Aa"]
        auxiliary += ["마찰 있음이면 f = μN_A", "마찰 없음이면 f = 0"]
        ambiguity += ["수평면의 마찰 유무가 명확하지 않습니다. 마찰 있음/없음 조건을 확인해야 합니다."]
        cautions += ["마찰 조건 불명: f 값을 확정하지 말고 조건을 먼저 확인한다."]

    _replace(
        bp,
        title="수평면 블록-매달린 물체 풀이 골격",
        fbd=["블록 A: 중력 m_Ag", "블록 A: 수직항력 N_A", "블록 A: 장력 T", *( ["블록 A: 마찰력 f"] if friction_state != "none" else [] ), "물체 B: 중력 m_Bg", "물체 B: 장력 T"],
        coordinates=["블록 A: 수평 운동 방향을 +x", "블록 A: 수직 위쪽을 +y", "물체 B: 아래 방향을 +로 잡으면 식이 단순"],
        applicable=applicable,
        auxiliary=auxiliary,
        conditions=["블록 A는 수평면 위에 있으므로 중력은 운동방향 성분이 아니라 N_A 계산에 사용", "이상적 줄/도르래이면 같은 줄의 장력은 T"],
        steps=["블록 A와 물체 B를 따로 떼어 FBD를 그린다.", "블록 A의 수직 방향에서 N_A를 구한다.", "마찰 조건을 먼저 확인한다.", "블록 A의 수평 운동방정식을 세운다.", "물체 B의 수직 운동방정식을 세운다.", "두 식을 연립해 a와 T를 구한다."],
        cautions=cautions,
        not_applicable=not_applicable,
        suppressed=["ideal_atwood", "vertical_two_mass_pulley"],
        ambiguity=ambiguity,
    )
    return True


def _inclined_block_hanging_mass(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    if not (_has(text, r"도르래|pulley|줄로\s*연결|로프") and _has(text, r"경사면|빗면|incline|inclined") and _has(text, r"매달|hanging|suspended|질량\s*M")):
        return False
    friction_state = _friction_state(text, features)
    model.problem_type = "경사면 블록 + 매달린 물체 연결 문제"
    model.analysis_targets = ["경사면 위 블록 m", "매달린 물체 M"]
    model.constraints = ["경사면 위 블록은 중력을 평행/수직 성분으로 분해", "같은 줄이면 두 물체의 가속도 크기는 같다"]
    model.risky_methods = ["경사면 블록을 수직 매달림 물체처럼 처리하는 것"]

    applicable = ["N = mg cosθ", "Mg - T = Ma"]
    auxiliary = ["줄 조건: |a_m| = |a_M| = a", "마찰 방향은 운동 또는 미끄러지려는 방향의 반대"]
    cautions = ["경사면에서는 mg sinθ, mg cosθ 성분 분해가 반드시 필요하다.", "일반 애트우드 식을 그대로 적용하면 안 된다."]
    not_applicable = ["m1g - T = m1a : 경사면 위 블록에는 그대로 적용 불가", "T - m2g = m2a : 경사면 블록 식으로 적용 불가"]
    ambiguity = []

    if friction_state == "none":
        applicable += ["f = 0", "T - mg sinθ = ma", "또는 mg sinθ - T = ma"]
        not_applicable += ["f = μN = μmg cosθ : 매끈한/마찰 없는 경사면에서는 적용 불가", "T - mg sinθ - f = ma : 최종 적용식은 f = 0을 대입해 정리"]
        cautions += ["마찰 없음 조건이면 경사면 방향 식에서 f 항을 제거한다."]
    elif friction_state == "present":
        applicable += ["f = μN = μmg cosθ", "T - mg sinθ - f = ma", "또는 mg sinθ - T - f = ma"]
    else:
        applicable += ["T - mg sinθ - f = ma", "또는 mg sinθ - T - f = ma"]
        auxiliary += ["마찰 있음이면 f = μN", "마찰 없음이면 f = 0"]
        ambiguity += ["경사면의 마찰 유무가 명확하지 않습니다. 마찰 있음/없음 조건을 확인해야 합니다."]
        cautions += ["마찰 조건 불명: f 값을 확정하지 말고 조건을 먼저 확인한다."]

    _replace(
        bp,
        title="경사면 블록-매달린 물체 풀이 골격",
        fbd=["경사면 블록: 중력 mg", "경사면 블록: 수직항력 N", "경사면 블록: 장력 T", *( ["경사면 블록: 마찰력 f"] if friction_state != "none" else [] ), "매달린 물체: 중력 Mg", "매달린 물체: 장력 T"],
        coordinates=["경사면 블록: 경사면 평행 방향", "경사면 블록: 경사면 수직 방향", "매달린 물체: 실제 운동 방향을 +로 설정"],
        applicable=applicable,
        auxiliary=auxiliary,
        conditions=["경사면 각도 θ가 주어지거나 그림에서 읽혀야 수치 계산 가능"],
        steps=["경사면 블록과 매달린 물체를 따로 그린다.", "경사면 블록의 중력을 mg sinθ, mg cosθ로 분해한다.", "수직 방향에서 N을 먼저 구한다.", "마찰 조건과 운동 경향에 맞춰 마찰력 항을 결정한다.", "매달린 물체 식과 연립한다."],
        cautions=cautions,
        not_applicable=not_applicable,
        suppressed=["ideal_atwood", "vertical_two_mass_pulley"],
        ambiguity=ambiguity,
    )
    return True


def _massive_pulley(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    if not (_has(text, r"도르래|pulley") and _has(text, r"관성모멘트|질량\s*있는\s*도르래|무게\s*있는\s*도르래|회전\s*관성|massive\s+pulley|pulley\s+inertia|I\s*=")):
        return False
    model.problem_type = "질량 있는 도르래 문제"
    model.analysis_targets = ["물체 1", "물체 2", "질량 있는 도르래"]
    model.constraints = ["질량 있는 도르래에서는 일반적으로 T1 ≠ T2", "줄이 미끄러지지 않으면 a = αR"]
    _replace(
        bp,
        title="질량 있는 도르래 풀이 골격",
        fbd=["물체 1: 중력 m1g, 장력 T1", "물체 2: 중력 m2g, 장력 T2", "도르래: 장력 T1, T2, 축 반력"],
        coordinates=["무거운 쪽 물체의 운동 방향을 +", "도르래 회전 양의 방향은 줄 운동과 일치"],
        applicable=["m1g - T1 = m1a", "T2 - m2g = m2a", "(T1 - T2)R = Iα", "a = αR"],
        auxiliary=["질량 있는 도르래: T1 ≠ T2", "도르래 반지름 R 필요"],
        conditions=["도르래의 관성모멘트 I가 무시되지 않음", "줄이 도르래에서 미끄러지지 않음"],
        steps=["두 물체와 도르래를 따로 분석한다.", "양쪽 장력을 T1, T2로 다르게 둔다.", "도르래에 대해 모멘트 방정식을 세운다.", "a = αR로 병진식과 회전식을 연결한다."],
        cautions=["질량 있는 도르래에서 같은 줄의 장력을 같다고 두면 안 된다."],
        not_applicable=["T1 = T2 = T : 질량 있는 도르래에서는 일반적으로 적용 불가", "같은 줄의 장력은 같다 : 도르래 회전관성을 무시할 때만 가능"],
        suppressed=["ideal_pulley_equal_tension"],
    )
    return True


def _movable_pulley(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    if not _has(text, r"움직도르래|움직이는\s*도르래|movable\s+pulley"):
        return False
    model.problem_type = "움직도르래 연결 문제"
    model.analysis_targets = ["움직도르래에 매달린 하중", "줄의 자유단 또는 연결 물체"]
    model.constraints = ["움직도르래에서는 줄 길이 구속조건으로 가속도 비가 달라질 수 있음", "이상적 줄이면 같은 줄 장력은 T"]
    _replace(
        bp,
        title="움직도르래 풀이 골격",
        fbd=["하중: 중력 mg", "하중: 줄 두 가닥의 장력 2T", "필요 시 연결 물체의 중력/장력"],
        coordinates=["하중의 이동방향", "줄 자유단의 이동방향"],
        applicable=["2T - mg = ma_load", "줄 길이 구속조건: a_free = 2a_load 또는 문제 배치에 맞는 관계"],
        auxiliary=["이상적 움직도르래에서는 하중을 지탱하는 줄 가닥 수를 센다"],
        conditions=["줄과 도르래가 이상적이고 가벼울 때", "그림 배치에 따라 가속도 관계 부호가 달라질 수 있음"],
        steps=["움직도르래를 지탱하는 줄 가닥 수를 센다.", "하중 FBD에 장력들을 모두 표시한다.", "줄 길이 일정 조건으로 가속도 관계를 세운다."],
        cautions=["움직도르래는 일반 고정 도르래와 가속도 구속조건이 다르다."],
        not_applicable=["|a1| = |a2| : 움직도르래 배치에서는 그대로 성립하지 않을 수 있음"],
        suppressed=["ideal_atwood"],
    )
    return True


def _banked_curve(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    sem = semantic_flags(text)
    if not sem.banked_curve:
        return False
    friction_state = _friction_state(text, features)
    wants_max = sem.max_speed
    wants_min = sem.min_speed
    model.analysis_targets = ["자동차 또는 입자"]
    # 표현에 "마찰"이 직접 없어도 banked curve에서 최대/최소 속력 한계를 묻고
    # 마찰 없음이 명시되지 않았으면 정지마찰 한계 문제로 보는 편이 안전합니다.
    if friction_state == "unknown" and (wants_max or wants_min):
        friction_state = "present"

    if friction_state == "present" and wants_max:
        model.problem_type = "마찰 있는 경사진 커브 최대속도 문제"
        model.constraints = ["최대속도에서는 보통 위쪽으로 미끄러지려는 경향", "마찰은 경사면 아래쪽 방향으로 작용하는 경우가 표준"]
        _replace(
            bp,
            title="마찰 있는 경사진 커브 최대속도 풀이 골격",
            fbd=["중력 mg: 아래 방향", "수직항력 N: 도로면에 수직", "정지마찰력 f: 최대속도에서는 보통 경사면 아래쪽"],
            coordinates=["수직 방향", "곡률 중심 방향"],
            applicable=["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
            auxiliary=["두 식을 연립해 v_max를 구한다"],
            conditions=["마찰 있는 banked curve", "최대속도 한계에서는 정지마찰이 한계값"],
            steps=["마찰 방향을 먼저 정한다.", "N과 f를 수직/중심 방향으로 분해한다.", "수직방향 평형식과 중심방향 운동방정식을 세운다.", "f = μ_sN을 대입한다."],
            cautions=["마찰 없는 설계속도 식 tanθ = v²/(gR)만 단독으로 적용하면 부족하다.", "평평한 커브 식 N = mg를 적용하면 안 된다."],
            not_applicable=["N = mg : 경사진 커브에서는 일반적으로 적용 불가", "μ_s ≥ v²/(gR) : 평평한 커브 식", "tanθ = v²/(gR) : 마찰 없는 설계속도 식이므로 최대속도 한계식으로 단독 적용 불가"],
            suppressed=["flat_curve_friction", "banked_curve_frictionless"],
        )
        return True

    if friction_state == "present" and wants_min:
        model.problem_type = "마찰 있는 경사진 커브 최소속도 문제"
        model.constraints = ["최소속도에서는 보통 아래쪽으로 미끄러지려는 경향", "마찰은 경사면 위쪽 방향으로 작용하는 경우가 표준"]
        _replace(
            bp,
            title="마찰 있는 경사진 커브 최소속도 풀이 골격",
            fbd=["중력 mg: 아래 방향", "수직항력 N: 도로면에 수직", "정지마찰력 f: 최소속도에서는 보통 경사면 위쪽"],
            coordinates=["수직 방향", "곡률 중심 방향"],
            applicable=["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"],
            auxiliary=["두 식을 연립해 v_min을 구한다"],
            conditions=["마찰 있는 banked curve", "최소속도 한계에서는 정지마찰이 한계값"],
            steps=["낮은 속도에서 미끄러지려는 방향을 판단한다.", "마찰 방향을 경사면 위쪽으로 두고 성분을 분해한다.", "수직/중심 방향 식을 세운다.", "f = μ_sN을 대입한다."],
            cautions=["최대속도와 최소속도는 마찰 방향이 반대가 될 수 있다.", "tanθ = v²/(gR)만으로는 마찰 있는 최소속도 한계를 구할 수 없다."],
            not_applicable=["N = mg : 경사진 커브에서는 일반적으로 적용 불가", "μ_s ≥ v²/(gR) : 평평한 커브 식", "tanθ = v²/(gR) : 마찰 없는 설계속도 식이므로 최소속도 한계식으로 단독 적용 불가"],
            suppressed=["flat_curve_friction", "banked_curve_frictionless"],
        )
        return True

    if friction_state == "present":
        model.problem_type = "마찰 있는 경사진 커브 문제 — 속도 한계 정보 필요"
        _replace(
            bp,
            title="마찰 있는 경사진 커브 정보 보완 안내",
            fbd=["중력 mg", "수직항력 N", "정지마찰력 f"],
            coordinates=["수직 방향", "곡률 중심 방향"],
            applicable=[],
            auxiliary=["최대속도이면 마찰은 보통 경사면 아래쪽", "최소속도이면 마찰은 보통 경사면 위쪽"],
            conditions=["최대속도/최소속도 또는 미끄러지려는 방향 확인 필요"],
            steps=["최대속도인지 최소속도인지 먼저 확인한다.", "마찰 방향을 정한 뒤 성분식을 세운다."],
            cautions=["마찰 방향이 정해지지 않으면 적용식을 하나로 확정하면 위험하다."],
            not_applicable=["tanθ = v²/(gR) : 마찰 없는 설계속도 식을 단독 적용하면 안 됨", "N = mg : 경사진 커브에서는 일반적으로 적용 불가", "μ_s ≥ v²/(gR) : 평평한 커브 식"],
            suppressed=["flat_curve_friction", "banked_curve_frictionless"],
            ambiguity=["마찰 있는 경사진 커브로 보이지만 최대속도/최소속도 정보가 부족합니다."],
            support_level="정보 부족 감지 및 추가 조건 안내",
        )
        return True

    model.problem_type = "마찰 없는 경사진 커브 문제"
    model.constraints = ["마찰 없는 경사진 커브에서는 수직항력의 수평 성분이 구심력 역할", "수직 방향 가속도는 0"]
    _replace(
        bp,
        title="마찰 없는 경사진 커브 풀이 골격",
        fbd=["중력 mg: 아래 방향", "수직항력 N: 도로면에 수직", "마찰 없음"],
        coordinates=["수직 방향", "곡률 중심 방향"],
        applicable=["N cosθ = mg", "N sinθ = mv²/R", "tanθ = v²/(gR)"],
        auxiliary=["두 식을 나누면 N이 제거됨"],
        conditions=["마찰 없는 banked curve", "도로가 각도 θ만큼 기울어져 있음"],
        steps=["FBD에서 N을 수직/수평 성분으로 나눈다.", "수직 방향 평형식을 세운다.", "중심 방향에 뉴턴 제2법칙을 적용한다.", "두 식을 나누어 tanθ를 구한다."],
        cautions=["이 문제에서 N = mg라고 두면 안 된다.", "마찰 없는 경사진 커브에서는 마찰력이 구심력을 제공하지 않는다."],
        not_applicable=["N = mg : 평평한 커브에서나 가능한 단순식", "μ_s ≥ v²/(gR) : 평평한 커브의 최소 마찰계수 식", "f_s = mv²/R : 마찰 없는 경사진 커브에는 적용 불가"],
        suppressed=["flat_curve_friction"],
    )
    return True


def _flat_curve(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    sem = semantic_flags(text)
    if not (sem.flat_curve or _has(text, r"평평한\s*커브|수평\s*커브|flat\s+curve|level\s+curve|평평한\s*(?:원형\s*도로|도로.*커브)")):
        return False
    if _has(text, r"경사진|banked|기울어진|경사각"):
        return False
    model.problem_type = "평평한 커브의 원운동/마찰 문제"
    _replace(
        bp,
        title="평평한 커브 풀이 골격",
        fbd=["중력 mg: 아래 방향", "수직항력 N: 위 방향", "정지마찰력 f_s: 곡률 중심 방향"],
        coordinates=["중심 방향 n축", "수직 방향 y축"],
        applicable=["N = mg", "ΣF_n = mv²/R", "f_s = mv²/R", "f_s ≤ μ_sN", "μ_s ≥ v²/(gR)"],
        auxiliary=["최대 정지마찰: f_s,max = μ_sN", "구심가속도: a_n = v²/R"],
        conditions=["도로가 기울어지지 않은 평평한 커브", "마찰이 구심력 역할을 함"],
        steps=["자동차 FBD를 그린다.", "수직 방향에서 N을 구한다.", "중심 방향 힘이 마찰임을 확인한다.", "마찰 한계식으로 μ_s를 정리한다."],
        cautions=["수직항력은 구심력이 아니다.", "마찰이 부족하면 바깥쪽으로 미끄러진다."],
        not_applicable=["N cosθ = mg : 경사진 커브 식", "N sinθ = mv²/R : 경사진 커브 식"],
        suppressed=["banked_curve"],
    )
    return True


def _conical_pendulum(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    sem = semantic_flags(text)
    explicit = sem.conical_explicit
    structural = sem.conical_structural
    conical_candidate = sem.conical_candidate
    if _has(text, r"가능성|확인|검토|인지|정보가\s*필요|주어지지|not\s+stated") and not _has(text, r"원뿔\s*(?:모양|형태)(?:으?로)|conical\s+motion|conical\s+pendulum"):
        explicit = False
        structural = False
        conical_candidate = True
    if not (explicit or structural):
        if conical_candidate:
            model.problem_type = "원뿔진자 가능성 있음 — 추가 조건 필요"
            model.analysis_targets = ["줄/끈에 매단 질점 또는 물체"]
            _replace(
                bp,
                title="원뿔진자 후보 정보 보완 안내",
                fbd=["중력 mg", "장력 T"],
                coordinates=["수직 방향", "수평 중심 방향 가능성"],
                applicable=["수평 원운동이면 T cosθ = mg", "수평 원운동이면 T sinθ = mω²r", "줄 길이 L이 주어지면 r = L sinθ"],
                auxiliary=["수평 원운동이면 T cosθ = mg", "수평 원운동이면 T sinθ = mω²r", "줄 길이 L이 주어지면 r = L sinθ"],
                conditions=["수평 원운동 여부", "줄이 수직/연직선과 이루는 각도 θ", "줄 길이 L 또는 원궤도 반지름 r"],
                steps=["수평 원운동인지 먼저 확인한다.", "각도 θ가 수직/연직 기준인지 확인한다.", "조건이 확인되면 원뿔진자 식을 적용한다."],
                cautions=["원뿔진자 가능성이 있지만 각도 기준 또는 수평 원운동 조건이 부족하면 확정하지 않는다.", "강체 일반 평면운동으로 바로 보내면 안 된다."],
                not_applicable=["ΣM_G = I_Gα : 원뿔진자 후보는 강체 회전식으로 우선 처리하지 않음"],
                suppressed=["general_rigid_body", "fixed_axis_rotation"],
                ambiguity=["원뿔진자 가능성 있음 — 수평 원운동 여부와 각도 기준 확인 필요"],
                support_level="모호성 감지 및 추가 조건 안내",
            )
            return True
        return False
    model.problem_type = "원뿔진자 원운동 문제"
    model.analysis_targets = ["질량 m인 물체"]
    _replace(
        bp,
        title="원뿔진자 풀이 골격",
        fbd=["중력 mg", "장력 T"],
        coordinates=["수직 방향", "수평 중심 방향"],
        applicable=["T cosθ = mg", "T sinθ = mv²/r", "T sinθ = mω²r", "r = L sinθ", "ω² = g/(L cosθ)", "ω² = g / (L cosθ)"],
        auxiliary=["r = L sinθ", "T = mg / cosθ", "ω² = g / (L cosθ)"],
        conditions=["질점이 줄에 매달려 수평 원운동", "줄 길이 L과 각도 θ가 정의되어야 함"],
        steps=["질량 m만 떼어 FBD를 그린다.", "장력 T를 수직/수평 성분으로 나눈다.", "수직 방향은 평형, 수평 방향은 구심가속도를 적용한다.", "r = L sinθ를 연결한다."],
        cautions=["원뿔진자는 강체 문제가 아니다.", "ΣM_G = I_Gα를 우선 쓰지 않는다."],
        not_applicable=["ΣM_G = I_Gα : 원뿔진자는 질점 원운동으로 우선 처리", "강체 일반 평면운동 템플릿"],
        suppressed=["general_rigid_body", "fixed_axis_rotation"],
    )
    return True


def _vertical_circle(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    sem = semantic_flags(text)
    loop_contact = _has(text, r"loop[- ]?the[- ]?loop|maintain\s+contact|접촉을\s*유지|접촉\s*유지|minimum\s+height|최소\s*높이")
    asks_tension = _has(text, r"장력|tension|tensile\s+force|string\s+force|rope\s+force")
    asks_normal = _has(text, r"수직항력|normal\s+(?:force|reaction)|track\s+force|rail\s+force")
    vertical_context = _has(text, r"수직\s*원|원형\s*(?:트랙|레일|고리)|vertical\s+(?:circle|loop)|vertical\s+circular\s+rail|loop") or loop_contact
    point_force_query = (sem.bottom_position or sem.top_position) and (asks_tension or asks_normal or sem.string_support or sem.track_support)
    if not (vertical_context or point_force_query):
        return False
    explicit_track = _has(text, r"트랙|레일|rail|track|circular\s+rail|원형\s*궤도|원형\s*트랙")
    force_conflict = explicit_track and asks_tension
    is_string = (sem.string_support or asks_tension) and not (explicit_track or asks_normal)
    is_track = (explicit_track or asks_normal) and not is_string
    force_symbol = "장력 T" if is_string else "수직항력 N"
    force_letter = "T" if is_string else "N"
    if force_conflict and sem.bottom_position:
        model.problem_type = "수직 원운동 최저점 힘 기호 충돌 — 확인 필요"
        _replace(
            bp,
            title="수직 원운동 최저점 힘 기호 확인 안내",
            fbd=["트랙/레일이면 수직항력 N", "줄/끈이면 장력 T", "중력 mg는 아래 방향"],
            coordinates=["최저점에서는 위쪽, 즉 중심 방향을 +n으로 설정"],
            applicable=["트랙/레일 문제라면 N - mg = mv²/R", "줄/끈 문제라면 T - mg = mv²/R"],
            auxiliary=["문제에서 tension을 물었지만 rail/track 단서가 있어 물리 모델 확인 필요"],
            conditions=["트랙/레일 접촉력인지 줄 장력인지 확인"],
            cautions=["rail/track과 tension 표현이 충돌합니다. 힘 기호를 무리하게 하나로 확정하지 마세요."],
            ambiguity=["트랙/레일은 보통 수직항력 N, tension은 줄 장력 T입니다. 물체가 레일에 얹힌 것인지 줄에 매단 것인지 확인이 필요합니다."],
            not_applicable=["N만 단독 또는 T만 단독으로 확정 금지"],
            support_level="모호성 감지 및 추가 조건 안내",
        )
        return True

    if sem.bottom_position:
        model.problem_type = "수직 원운동 최저점 장력/수직항력 문제"
        _replace(
            bp,
            title="수직 원운동 최저점 풀이 골격",
            fbd=[f"최저점: {force_symbol}는 중심 방향", "최저점: 중력 mg는 중심 반대 방향"],
            coordinates=["최저점에서는 위쪽, 즉 중심 방향을 +n으로 설정"],
            applicable=[f"{force_letter} - mg = mv²/R", f"{force_letter} = mg + mv²/R"],
            auxiliary=["필요하면 에너지식으로 최저점 속도 v를 먼저 구함"],
            conditions=["관심 위치가 최저점", "중심 방향 힘의 합이 mv²/R"],
            steps=["최저점에서 중심 방향을 위쪽으로 잡는다.", "중심 방향 힘과 반대 방향 힘을 구분한다.", f"{force_letter} - mg = mv²/R을 세운다.", f"{force_letter}를 정리한다."],
            cautions=["최저점 장력 문제에서 최고점 최소속도 조건을 우선 적용하면 안 된다."],
            not_applicable=["v_min = √(gR) : 최고점 접촉 유지 최소속도 조건", "최고점: mg + N = mv²/R : 최저점에는 적용 불가"],
            suppressed=["vertical_circle_top_minimum_speed"],
        )
        return True

    if sem.top_position or loop_contact or _has(text, r"떨어지지|이탈하지|최소\s*(?:속도|속력)|minimum\s+(?:speed|height)"):
        model.problem_type = "수직 원운동 최고점 접촉 유지 문제"
        _replace(
            bp,
            title="수직 원운동 최고점 풀이 골격",
            fbd=[f"최고점: 중력 mg는 중심 방향", f"최고점: {force_symbol}도 중심 방향"],
            coordinates=["최고점에서는 아래쪽, 즉 중심 방향을 +n으로 설정"],
            applicable=[f"최고점: mg + {force_letter} = mv²/R", f"mg + {force_letter} = mv²/R", f"최소 조건: {force_letter} = 0", "mg = mv²/R", "v_min = √(gR)"],
            auxiliary=["필요하면 에너지식으로 최고점 속도 v를 구함"],
            conditions=["접촉 유지/줄 팽팽함의 최소 조건은 접촉력 또는 장력이 0이 되는 경계", f"{force_letter} < 0은 물리적으로 불가능"],
            steps=["최고점에서 중심 방향을 아래쪽으로 표시한다.", "중심 방향의 실제 힘만 합한다.", f"최소 조건이면 {force_letter}를 0으로 둔다."],
            cautions=["구심력이라는 별도 힘을 FBD에 추가하지 않는다."],
            not_applicable=["N = mg : 수직 원운동 최고점에서는 일반적으로 성립하지 않음", "T - mg = mv²/R : 최저점 줄 문제 식"],
            suppressed=["flat_curve_friction", "vertical_circle_bottom_tension"],
        )
        return True

    model.problem_type = "수직 원운동 임의 각도 문제"
    _replace(
        bp,
        title="수직 원운동 임의 각도 풀이 골격",
        fbd=[f"{force_symbol}", "중력 mg"],
        coordinates=["중심 방향 n축", "접선 방향 t축"],
        applicable=[f"{force_letter} - mg cosθ = mv²/R", "ΣF_t = ma_t"],
        auxiliary=["각도 θ의 기준에 따라 mg cosθ의 부호가 달라질 수 있음", "필요하면 에너지식으로 v(θ)를 구함"],
        conditions=["임의 각도에서 중심 방향 성분을 정확히 정해야 함"],
        steps=["각도 θ가 어디서부터 정의되었는지 확인한다.", "중력을 중심 방향/접선 방향으로 분해한다.", "중심 방향에는 mv²/R을 적용한다."],
        cautions=["각도 정의가 다르면 부호가 바뀐다. 그림 기준을 반드시 확인한다."],
        not_applicable=["v_min = √(gR) : 최고점 최소속도 전용 조건", "N = mg : 수직 원운동 임의 위치에서 일반적으로 성립하지 않음"],
        suppressed=["flat_curve_friction"],
    )
    return True


def _rolling_with_slipping(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    sem = semantic_flags(text)
    round_body = _has(text, r"원통|원판|원반|바퀴|구슬|(?:^|\s)공(?=$|\s|[이가은는을를의에과와로])|(?:^|\s)구(?=$|\s|[이가은는을를의에과와로])|cylinder|disk|wheel|sphere")
    rolling_context = sem.rolling_word or round_body or _has(text, r"굴러|구르|rolling")
    if not (sem.slip_present and rolling_context):
        return False
    model.problem_type = "미끄럼을 동반한 구름 운동"
    model.constraints = ["접점에서 미끄러짐이 있으므로 순수 구름 구속조건을 바로 쓸 수 없음"]
    _replace(
        bp,
        title="미끄럼 구름 풀이 골격",
        fbd=["중력 mg", "수직항력 N", "운동마찰력 f_k"],
        coordinates=["질량중심 G의 병진 방향", "회전 양의 방향"],
        applicable=["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"],
        auxiliary=["접점 상대운동 방향으로 운동마찰력 방향 결정"],
        conditions=["미끄러짐이 실제로 존재함", "운동마찰계수 μ_k 또는 마찰력 정보 필요"],
        steps=["원통/구의 FBD를 그린다.", "마찰력을 운동마찰로 둔다.", "병진식과 회전식을 따로 세운다.", "순수 구름 조건 없이 v_G와 ω를 별도 변수로 둔다."],
        cautions=["v_G = ωR 적용 불가: 미끄러지지 않는 순수 구름에서만 사용", "a_G = αR 적용 불가: 미끄러지지 않는 순수 구름에서만 사용"],
        not_applicable=["v_G = ωR : 현재 문제에서는 적용식으로 사용 불가", "a_G = αR : 현재 문제에서는 적용식으로 사용 불가", "mgh = 1/2mv_G² + 1/2I_Gω² : 마찰 손실이 있으면 단순 보존식으로 사용 불가"],
        suppressed=["pure_rolling"],
    )
    return True


def _pure_rolling(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    sem = semantic_flags(text)
    if sem.slip_present:
        return False
    round_body = _has(text, r"원통|원판|원반|바퀴|공|구슬|sphere|cylinder|disk|wheel|ball")
    rolling_or_rotation_context = sem.rolling_word or sem.rotation_word or round_body or _has(text, r"구름|굴러|구르|rolling|rolls?|회전")
    # '미끄러지지 않을 최대 속도' 같은 커브/마찰 한계 표현은 순수 구름이 아닙니다.
    if sem.banked_curve or sem.flat_curve or _has(text, r"커브|curve|마찰계수.*최대|최대.*마찰계수"):
        return False
    if not (sem.explicit_pure_rolling and rolling_or_rotation_context):
        return False
    model.problem_type = "순수 구름 운동"
    _replace(
        bp,
        title="순수 구름 풀이 골격",
        fbd=["중력 mg", "수직항력 N", "정지마찰력 f_s"],
        coordinates=["질량중심 G의 병진 방향", "회전 양의 방향"],
        applicable=["mgh = 1/2mv_G² + 1/2I_Gω²", "v_G = ωR", "a_G = αR"],
        auxiliary=["ω = v_G/R", "정지마찰은 접점에서 일을 하지 않는 경우가 많음"],
        conditions=["미끄러지지 않는다는 조건이 명시되어야 함", "순수 구름에서는 병진 에너지와 회전 에너지를 모두 포함"],
        steps=["미끄러짐이 없는지 먼저 확인한다.", "병진/회전 에너지를 모두 적는다.", "ω = v_G/R을 대입한다.", "물체의 I_G를 대입한다."],
        cautions=["순수 구름 조건이 명시되어 있으므로 v_G = ωR, a_G = αR을 사용할 수 있습니다."],
        not_applicable=["f_k = μ_kN : 순수 구름에서는 보통 운동마찰이 아니라 정지마찰"],
        suppressed=["rolling_with_slipping"],
    )
    return True


def _position_function_kinematics(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    # r(t)=...i+...j 형태는 극좌표 r이 아니라 직교좌표 위치벡터입니다.
    # θ/theta/e_r/e_θ/polar가 함께 명시될 때만 극좌표 템플릿이 우선됩니다.
    sem = semantic_flags(text)
    cartesian_vector = sem.cartesian_position_vector
    component_functions = _has(text, r"x\s*=\s*[^,.;]+t|y\s*=\s*[^,.;]+t|x\(t\)|y\(t\)|위치가\s*[^.。]*주어진")
    polar_explicit = sem.polar_motion
    if not (cartesian_vector or (component_functions and not polar_explicit)):
        return False
    model.problem_type = "위치 함수 기반 입자 운동학"
    model.analysis_targets = ["입자"]
    _replace(
        bp,
        title="위치 함수 운동학 풀이 골격",
        fbd=[],
        coordinates=["직교좌표 i, j", "x(t), y(t)를 각각 시간에 대해 미분"],
        applicable=["r(t) = x(t)i + y(t)j", "v(t) = dr/dt = dx/dt i + dy/dt j", "a(t) = d²r/dt² = d²x/dt² i + d²y/dt² j"],
        auxiliary=["속력은 |v| = √(v_x² + v_y²)", "가속도 크기는 |a| = √(a_x² + a_y²)"],
        conditions=["위치 함수가 시간의 함수로 주어짐"],
        steps=["x(t), y(t)를 분리해 적는다.", "각 성분을 한 번 미분해 속도를 구한다.", "각 성분을 한 번 더 미분해 가속도를 구한다."],
        cautions=["x(t), y(t)가 주어졌다면 등가속도 공식보다 미분이 우선이다."],
        not_applicable=["v = v0 + at : 가속도가 일정할 때만 사용", "s = v0t + 1/2at² : 등가속도 조건 없이는 우선 적용 불가", "v² = v0² + 2as : 등가속도 조건 없이는 우선 적용 불가", "극좌표 가속도식 : i, j 성분 위치벡터 문제에서는 우선 적용 불가", "e_r, e_θ 기반 식 : 직교좌표 위치벡터 문제에서는 우선 적용 불가"],
        suppressed=["constant_acceleration_kinematics"],
    )
    return True


def _variable_force_work(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    if not _has(text, r"F\s*\(\s*x\s*\)|F\s*=\s*[^,.;。]*x(?:\^\d+|²|\d|\s)|위치에\s*따라\s*변하는\s*힘|x에\s*따라\s*변하는\s*힘|x\s*=\s*0\s*부터"):
        return False
    model.problem_type = "위치 의존 힘에 의한 일-에너지 문제"
    _replace(
        bp,
        title="위치 의존 힘 일-에너지 풀이 골격",
        fbd=["위치에 따라 변하는 외력 F(x)", "필요 시 중력/수직항력/마찰력"],
        coordinates=["힘이 작용하는 x방향"],
        applicable=["W = ∫ F(x) dx", "W = ΔT", "∫_{x1}^{x2} F(x) dx = 1/2mv₂² - 1/2mv₁²"],
        auxiliary=["예: ∫_0^2 3x² dx", "힘-변위 그래프가 있으면 그래프 아래 면적이 일"],
        conditions=["힘이 위치 x의 함수로 주어짐", "시작/끝 위치 x1, x2 필요"],
        steps=["힘이 일정한지 위치에 따라 변하는지 확인한다.", "일을 적분으로 계산한다.", "계산한 일을 운동에너지 변화와 연결한다."],
        cautions=["힘이 일정하지 않으면 W = Fs를 그대로 쓰면 안 된다.", "일반 F=ma보다 일-에너지 적분 접근이 더 직접적일 수 있다."],
        not_applicable=["W = Fs : 힘이 일정할 때만 사용", "일반 ΣF = ma만으로 바로 수치 속도를 구하려는 접근"],
        suppressed=["constant_force_work", "generic_fma_first"],
    )
    return True


def _time_dependent_impulse(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    if not _has(text, r"F\s*\(\s*t\s*\)|시간에\s*따라\s*변하는\s*힘|t에\s*따라\s*변하는\s*힘|충격량.*시간|force.*time"):
        return False
    model.problem_type = "시간 의존 힘과 충격량 문제"
    _replace(
        bp,
        title="시간 의존 힘 충격량 풀이 골격",
        fbd=["시간에 따라 변하는 외력 F(t)", "필요 시 중력/접촉력"],
        coordinates=["충격량을 계산할 방향"],
        applicable=["J = ∫_{t1}^{t2} F(t) dt", "J = Δp", "∫F(t)dt = m(v₂ - v₁)"],
        auxiliary=["힘-시간 그래프가 있으면 그래프 아래 면적이 충격량"],
        conditions=["힘이 시간의 함수로 주어짐", "충격 시간 구간 t1~t2 필요"],
        steps=["힘의 방향과 시간 구간을 정한다.", "F(t)를 적분해 충격량 J를 구한다.", "J = Δp로 속도 변화를 구한다."],
        cautions=["힘이 일정하지 않으면 J = FΔt를 그대로 쓰면 안 된다."],
        not_applicable=["J = FΔt : 평균힘 또는 일정힘일 때만 직접 사용"],
        suppressed=["constant_force_impulse"],
    )
    return True


def _ladder_instant_center(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    if not (_has(text, r"벽과\s*바닥\s*사이|사다리|ladder") and _has(text, r"미끄러|속도|순간중심|A점|B점")):
        return False
    model.problem_type = "막대/사다리 벽-바닥 순간중심 문제"
    model.analysis_targets = ["벽과 바닥 사이에서 미끄러지는 막대 또는 사다리"]
    _replace(
        bp,
        title="벽-바닥 막대 순간중심 풀이 골격",
        fbd=[],
        coordinates=["A점: 바닥을 따라 수평 속도", "B점: 벽을 따라 수직 속도"],
        applicable=["v_A = ω r_A/IC", "v_B = ω r_B/IC", "v_B = v_A + ω × r_B/A"],
        auxiliary=["A점 속도 방향에 수직인 선", "B점 속도 방향에 수직인 선", "두 수직선의 교점 = 순간중심 IC"],
        conditions=["힘보다 속도 관계를 묻는 강체 운동학 문제", "A점/B점 속도 방향 정보 필요"],
        steps=["A점과 B점의 속도 방향을 먼저 표시한다.", "각 속도 방향에 수직인 선을 그린다.", "교점을 순간중심 IC로 잡는다.", "ω = v_A/r_A/IC를 구하고 v_B를 계산한다."],
        cautions=["이 문제는 힘/모멘트 방정식보다 강체 운동학 관계가 우선이다."],
        not_applicable=["ΣF = ma_G : 속도 관계만 묻는 순간중심 문제에서는 우선식이 아님", "ΣM_G = I_Gα : 힘/가속도 조건 없이는 우선식이 아님"],
        suppressed=["rigid_body_dynamics_fma_moment"],
    )
    return True


def _slot_pin_relative_motion(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    if not _has(text, r"슬롯|홈을\s*따라|핀|pin\s+in\s+slot|slot"):
        return False
    if _has(text, r"순간\s*중심|순간중심|instantaneous\s+center"):
        return False
    if _has(text, r"핀으로\s*고정|고정된\s*막대|fixed\s+axis|pinned\s+rod"):
        return False
    model.problem_type = "슬롯/핀 상대속도 문제"
    _replace(
        bp,
        title="슬롯/핀 상대속도 풀이 골격",
        fbd=[],
        coordinates=["고정 좌표계", "슬롯 방향 좌표", "슬롯에 수직인 구속 방향"],
        applicable=["v_B = v_A + ω × r_B/A", "a_B = a_A + α × r_B/A - ω²r_B/A", "슬롯 방향 상대속도 성분을 둔다"],
        auxiliary=["핀은 슬롯 방향으로 상대운동 가능", "슬롯에 수직한 방향은 기하 구속조건을 만족"],
        conditions=["링크/막대/슬롯의 기하 관계가 필요"],
        steps=["각 점의 허용 속도 방향을 표시한다.", "상대속도식을 쓴다.", "슬롯 방향/수직 방향으로 성분 분해한다."],
        cautions=["슬롯 문제는 힘보다 운동학적 구속조건이 먼저인 경우가 많다."],
        not_applicable=["ΣF = ma_G만으로 바로 속도를 구하는 접근"],
        suppressed=["generic_rigid_body_dynamics"],
    )
    return True


def _bullet_rod_collision(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    sem = semantic_flags(text)
    rotating_body = _has(text, r"막대|rod|bar|hinged\s+(?:rod|bar)|pivoted\s+(?:rod|bar)|(?:rod|bar)\s+pivoted|(?:rod|bar)\s+pinned\s+at\s+one\s+end|hinged\s+bar|pivoted\s+bar|원판|원반|바퀴|회전판|진자막대|고정축\s*강체|회전강체|disk|wheel|rotating\s+body")
    embedded = _has(text, r"박힌|박힌다|박힌\s*뒤|박힌\s*후|박혀서|박히고|박힘|붙는다|붙어|꽂힌|꽂힌다|가장자리에\s*(?:박|꽂)|rim에\s*박|embedded|lodged|lodges?\s+in|sticks?(?:\s+(?:into|in|to))?|embeds?\s+in|remains?\s+in|hits?\s+and\s+(?:sticks|remains|lodges)|strikes?\s+[^.;]{0,40}\s+and\s+sticks")
    axis_rotation = _has(text, r"핀|회전축|고정축|축\s*주위|고정축을\s*중심|주위로\s*(?:회전|돈)|함께\s*돈|각속도|pinned|pivoted|hinged|pivoted\s+at\s+one\s+end|fixed\s+pivot|fixed\s+hinge|힌지|피벗|피벗된|힌지된|한쪽\s*끝(?:이)?\s*(?:고정|피벗|힌지)|fixed\s+axis|fixed\s+axle|about\s+(?:a|the)?\s*(?:fixed\s+)?(?:axis|axle|pivot)|angular\s+velocity\s+(?:just|immediately)?\s*after\s+(?:collision|impact)")
    if not (sem.bullet_rotating_body_collision or (_has(text, r"탄환|총알|투사체|bullet|projectile") and rotating_body and (embedded or axis_rotation))):
        return False
    body_label = "회전강체"
    if _has(text, r"원판|원반|회전판|disk"):
        body_label = "원판"
    elif _has(text, r"막대|rod|bar"):
        body_label = "막대"
    model.problem_type = f"탄환-{body_label} 충돌/각운동량 보존 문제"
    model.analysis_targets = [f"탄환 + {body_label} 계", "회전축 또는 핀 기준"]
    _replace(
        bp,
        title="탄환-회전강체 충돌 풀이 골격",
        fbd=["충돌 순간 외부 축 반력은 있을 수 있음", "축 기준으로는 축 반력의 모멘트가 0일 수 있음"],
        coordinates=["회전축 O 또는 핀 기준", "충돌 직전 탄환 속도 방향", "탄환이 박히는 위치의 반지름 r"],
        applicable=["H_O(before) = H_O(after)", "m_bvr = I_totalω", "m_b v r = I_totalω", "m_b v r = I_total ω", "탄환이 박히면 강체와 함께 회전"],
        auxiliary=["I_total = I_body,O + m_b r²", "충돌 직후 각속도 ω를 구함"],
        conditions=["충돌 시간이 매우 짧음", "기준점 O에 대한 외부 충격 모멘트가 무시 가능", "탄환이 박히는 완전비탄성 회전 충돌"],
        steps=["회전축 O를 기준점으로 잡는다.", "충돌 전 탄환의 각운동량 m_bvr을 계산한다.", "충돌 후 강체+탄환의 관성모멘트를 합한다.", "H_O(before)=H_O(after)로 ω를 구한다."],
        cautions=["축 반력의 외부 충격량 때문에 선운동량 보존은 성립하지 않을 수 있다.", "기준점 선택이 핵심이다."],
        not_applicable=["m1v1i + m2v2i = m1v1f + m2v2f : 축 반력이 있으면 선운동량 보존 우선식으로 부적절", "단순 1차원 선운동량 보존식만 우선 출력하는 접근", "1차원 충돌 반발계수 템플릿"],
        suppressed=["one_dimensional_linear_collision", "restitution_collision"],
    )
    return True


def _collision_restitution(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    if not (_has(text, r"충돌|collision|impact") and _has(text, r"반발계수|coefficient\s+of\s+restitution|\be\b")):
        return False
    if _has(text, r"탄환|총알|막대|원판|원반|회전판|핀|회전축|고정축|각속도"):
        return False
    model.problem_type = "충격량-운동량/충돌 문제"
    _replace(
        bp,
        title="충돌/반발계수 풀이 골격",
        fbd=["충돌하는 두 물체를 하나의 계로 설정"],
        coordinates=["충돌선 방향을 +로 설정"],
        applicable=["m1v1i + m2v2i = m1v1f + m2v2f", "e = (v2f - v1f)/(v1i - v2i)"],
        auxiliary=["반발계수식: e = (v2f - v1f)/(v1i - v2i)", "완전비탄성 충돌: v1f = v2f", "완전탄성 충돌: e = 1"],
        conditions=["충돌 시간 동안 외부 충격량이 무시 가능", "속도 부호 기준을 일관되게 설정"],
        steps=["충돌 전/후 속도 기호를 정한다.", "계 전체의 운동량 보존식을 쓴다.", "반발계수식을 추가해 연립한다."],
        cautions=["운동량 보존과 운동에너지 보존은 항상 동시에 성립하지 않는다."],
        not_applicable=["운동에너지 보존: 완전탄성 조건이 없으면 적용 불가"],
        suppressed=["energy_conservation_for_collision"],
    )
    return True


def _angular_momentum(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    if not _has(text, r"각운동량|angular\s+momentum|외부\s*모멘트\s*가\s*0|moment\s+of\s+momentum"):
        return False
    model.problem_type = "각운동량 보존 문제"
    _replace(
        bp,
        title="각운동량 보존 풀이 골격",
        fbd=["기준점에 대한 외부 모멘트 확인"],
        coordinates=["기준점 O", "질량중심 G 필요 시 별도"] ,
        applicable=["ΣM_O = dH_O/dt", "외부 모멘트가 0이면 H_O1 = H_O2", "질점: H_O = r × mv", "강체: H_G = I_Gω"],
        auxiliary=["기준점 선택에 따라 외부 모멘트가 달라짐"],
        conditions=["선택한 기준점에 대한 외부 모멘트가 0 또는 무시 가능"],
        steps=["기준점 O를 정한다.", "외부 모멘트가 0인지 확인한다.", "전/후 각운동량을 같은 기준으로 계산한다."],
        cautions=["선운동량 보존과 각운동량 보존은 조건이 다르다."],
        not_applicable=["선운동량 보존: 외력이 있어도 각운동량만 보존될 수 있음"],
        suppressed=["linear_momentum_only"],
    )
    return True


def _fixed_axis(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    if not _has(text, r"고정축|fixed\s+axis|핀으로\s*고정|힌지|pinned"):
        return False
    model.problem_type = "강체 고정축 회전"
    _replace(
        bp,
        title="고정축 회전 풀이 골격",
        fbd=["외력", "중력 mg", "축 반력", "토크를 만드는 힘"],
        coordinates=["고정축 O 기준 회전 양의 방향"],
        applicable=["ΣM_O = I_Oα", "ω = ω0 + αt", "ω² = ω0² + 2αθ"],
        auxiliary=["축을 지나는 반력은 O점 기준 모멘트가 0"],
        conditions=["회전축이 공간에 고정되어 있음"],
        steps=["회전축 O를 표시한다.", "O점 기준 모멘트를 합한다.", "필요하면 각운동학 식과 연결한다."],
        cautions=["고정축 문제에서는 질량중심 기준보다 축 기준 모멘트가 편한 경우가 많다."],
        not_applicable=["순수 병진운동 식만으로 처리"],
        suppressed=["pure_translation"],
    )
    return True


def _general_plane_motion(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    if not _has(text, r"일반\s*평면운동|general\s+plane\s+motion|강체\s*평면운동"):
        return False
    model.problem_type = "강체 일반 평면운동 문제"
    _replace(
        bp,
        title="강체 일반 평면운동 풀이 골격",
        fbd=["외력", "중력 mg", "접촉력/반력", "필요 시 마찰력"],
        coordinates=["질량중심 G의 x-y 좌표", "회전 양의 방향"],
        applicable=["ΣF_x = m a_Gx", "ΣF_y = m a_Gy", "ΣM_G = I_Gα", "v_B = v_A + ω × r_B/A"],
        auxiliary=["필요 시 a_B = a_A + α × r_B/A - ω²r_B/A"],
        conditions=["강체가 병진과 회전을 함께 함"],
        steps=["질량중심 G와 관심점을 표시한다.", "외력을 모두 FBD에 넣는다.", "병진식과 회전식을 함께 세운다.", "기하 구속조건을 추가한다."],
        cautions=["질점처럼 ΣF=ma만 쓰면 회전 효과를 놓칠 수 있다."],
        not_applicable=["순수 병진운동 가정", "고정축 회전만 가정"],
        suppressed=["particle_fma_only"],
    )
    return True


def _ambiguous_pulley(text: str, model: ProblemModel, features: FeatureReport, bp: SolutionBlueprint) -> bool:
    if not _has(text, r"도르래|pulley|줄로\s*연결"):
        return False
    # m1/m2가 있고 '가속도/장력'을 묻는 대표 애트우드형 문장은 기존 템플릿을 허용합니다.
    if _has(text, r"m1|m2|질량\s*m_?1|질량\s*m_?2|애트우드|atwood|모두\s*매달|두\s*물체.*매달"):
        return False
    if _has_any(text, [r"수평면|테이블|경사면|매달|관성모멘트|질량\s*있는|움직도르래|질량\s*없는|이상적"]):
        return False
    model.problem_type = "정보 부족: 도르래 연결 문제 후보"
    model.analysis_targets = ["연결된 물체들 — 배치 정보 확인 필요"]
    _replace(
        bp,
        title="도르래 문제 정보 부족 안내",
        fbd=[],
        coordinates=[],
        applicable=[],
        auxiliary=[],
        conditions=["두 물체가 모두 매달려 있는지, 한 물체가 수평면/경사면 위에 있는지 확인 필요", "도르래가 질량 없는지, 질량 있는지 확인 필요", "마찰 유무 확인 필요"],
        steps=["물체 배치를 먼저 확인한다.", "각 물체의 운동방향을 정한다.", "그 다음에 적절한 전용 템플릿을 적용한다."],
        cautions=["정보가 부족하므로 일반 애트우드 식을 바로 적용하지 않는다."],
        not_applicable=["m1g - T = m1a : 두 물체가 모두 수직으로 매달린 구조인지 확인 전에는 적용 보류", "T - m2g = m2a : 배치 정보 확인 전에는 적용 보류"],
        suppressed=["ideal_atwood_until_layout_known"],
        ambiguity=["도르래 연결 문제로 보이지만, 물체 배치 정보가 부족합니다.", "수평면/경사면/양쪽 매달림/질량 있는 도르래 여부를 추가로 입력하면 정확도가 올라갑니다."],
        support_level="정보 부족 감지 및 추가 조건 안내",
    )
    return True
