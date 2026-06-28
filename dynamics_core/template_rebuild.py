from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from .models import ProblemModel, SolutionBlueprint
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


def _replace(
    bp: SolutionBlueprint,
    *,
    template_id: str,
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
    support_level: str = "AI 검증 후 재생성된 전문가 템플릿",
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
    bp.template_id = template_id  # type: ignore[attr-defined]
    bp.final_template_id = template_id  # type: ignore[attr-defined]


def _set_model(model: ProblemModel, *, problem_type: str, targets: Sequence[str], constraints: Sequence[str] = (), risky: Sequence[str] = (), methods: Sequence[str] = ()) -> None:
    model.problem_type = problem_type
    model.analysis_targets = _uniq(targets)
    model.constraints = _uniq([*model.constraints, *constraints])
    model.risky_methods = _uniq([*model.risky_methods, *risky])
    model.allowed_methods = _uniq([*model.allowed_methods, *methods])


def build_conical(problem: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    _set_model(
        model,
        problem_type="원뿔진자 원운동 문제",
        targets=["줄/끈/실/로프에 매단 질점"],
        constraints=["질점은 수평 원운동을 한다", "줄은 수직/연직선과 각도 θ를 이룬다"],
        risky=["강체 일반 평면운동 식 ΣM_G = I_Gα를 우선 적용하는 것"],
        methods=["원운동 n방향 뉴턴 제2법칙"],
    )
    _replace(
        bp,
        template_id="conical_pendulum",
        title="원뿔진자 풀이 골격",
        fbd=["중력 mg", "장력 T"],
        coordinates=["수직 방향", "수평 중심 방향"],
        applicable=["T cosθ = mg", "T sinθ = mω²r", "T sinθ = mv²/r", "r = L sinθ", "ω² = g/(L cosθ)"],
        auxiliary=["v = ωr"],
        conditions=["줄 길이 L과 각도 θ의 기준이 필요", "수평 원운동이어야 함"],
        steps=["질점 하나를 떼어 FBD를 그린다.", "장력 T를 수직 성분과 수평 중심 성분으로 분해한다.", "수직 방향 평형식과 중심 방향 원운동식을 세운다.", "r = L sinθ를 대입해 각속도를 정리한다."],
        cautions=["원뿔진자는 질점 원운동 문제이지 강체 일반 평면운동 문제가 아니다."],
        not_applicable=["ΣM_G = I_Gα : 원뿔진자 질점 문제의 우선 적용식이 아님"],
        suppressed=["general_planar_rigid_body", "fixed_axis_rotation"],
    )


def build_sliding_rotation(problem: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    _set_model(
        model,
        problem_type="미끄럼을 동반한 회전/구름 운동",
        targets=["원통/바퀴/원판의 질량중심 G"],
        constraints=["접점에서 미끄럼이 있으므로 순수 구름 구속조건은 성립하지 않음"],
        risky=["v_G = ωR, a_G = αR을 순수 구름 조건으로 적용하는 것"],
        methods=["병진 ΣF=ma_G", "회전 ΣM_G=I_Gα"],
    )
    _replace(
        bp,
        template_id="sliding_rotation",
        title="미끄럼 동반 회전/구름 풀이 골격",
        fbd=["중력 mg", "수직항력 N", "운동마찰력 f_k"],
        coordinates=["경사면 평행/수직 방향", "회전 양의 방향"],
        applicable=["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"],
        auxiliary=["미끄럼이 있으므로 회전운동과 병진운동은 마찰 토크로 연결"],
        conditions=["운동마찰계수 μ_k, 경사각 θ, 관성모멘트 I_G가 필요할 수 있음"],
        steps=["질량중심 병진 운동방정식을 세운다.", "질량중심 기준 모멘트 방정식을 세운다.", "운동마찰력 f_k = μ_kN을 사용한다.", "순수 구름 조건을 적용하지 않는다."],
        cautions=["미끄럼 단서가 있으므로 순수 구름 조건은 적용식이 아니라 비적용식으로만 둔다."],
        not_applicable=["v_G = ωR : 미끄럼이 있으면 적용식으로 사용 불가", "a_G = αR : 미끄럼이 있으면 적용식으로 사용 불가"],
        suppressed=["pure_rolling"],
    )


def build_pure_rolling(problem: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    _set_model(model, problem_type="순수 구름 운동", targets=["구르는 강체"], constraints=["미끄러지지 않음"], methods=["에너지", "병진+회전"])
    _replace(
        bp,
        template_id="pure_rolling",
        title="미끄럼 없는 순수 구름 풀이 골격",
        fbd=["중력 mg", "수직항력 N", "정지마찰력 f_s"],
        coordinates=["경사면 평행/수직 방향", "회전 방향"],
        applicable=["v_G = ωR", "a_G = αR", "mgh = 1/2mv_G² + 1/2I_Gω²"],
        conditions=["접점에서 미끄럼이 없어야 함"],
        cautions=["미끄럼이 발생하면 v_G = ωR, a_G = αR을 적용할 수 없다."],
    )


def build_vertical_string_bottom(problem: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    _set_model(model, problem_type="수직 원운동 최저점 장력 문제", targets=["줄/끈/로프에 매단 물체"], constraints=["최저점에서 중심 방향은 위쪽"], methods=["중심방향 뉴턴 제2법칙"])
    _replace(
        bp,
        template_id="vertical_circle_string_bottom",
        title="수직 원운동 최저점 장력 풀이 골격",
        fbd=["중력 mg 아래", "장력 T 위쪽/중심 방향"],
        coordinates=["중심 방향을 양의 방향", "최저점에서는 위쪽이 중심 방향"],
        applicable=["T - mg = mv²/R", "T = mg + mv²/R"],
        conditions=["줄/끈/실/로프 문제이므로 힘 이름은 장력 T"],
        steps=["최저점에서 중심 방향을 위쪽으로 잡는다.", "장력은 중심 방향, 중력은 중심 반대 방향이다.", "ΣF_n = mv²/R을 적용한다."],
        cautions=["최저점 장력 문제에서 최고점 최소속도 조건을 우선 적용하면 안 된다."],
        not_applicable=["N - mg = mv²/R : 줄 문제에서는 수직항력 N이 아니라 장력 T를 사용", "v_min = √(gR) : 최고점 접촉 유지 최소속도 조건이므로 최저점 장력의 핵심 적용식이 아님"],
        suppressed=["vertical_circle_top_minimum_speed", "vertical_circle_track"],
    )


def build_vertical_string_top(problem: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    _set_model(model, problem_type="수직 원운동 최고점 장력/최소속도 문제", targets=["줄/끈/로프에 매단 물체"], constraints=["최고점에서 중심 방향은 아래쪽"], methods=["중심방향 뉴턴 제2법칙"])
    _replace(
        bp,
        template_id="vertical_circle_string_top",
        title="수직 원운동 최고점 장력/최소속도 풀이 골격",
        fbd=["중력 mg 아래/중심 방향", "장력 T 아래/중심 방향"],
        coordinates=["중심 방향을 양의 방향", "최고점에서는 아래쪽이 중심 방향"],
        applicable=["T + mg = mv²/R", "최소 팽팽 조건: T = 0", "v_min = √(gR)"],
        not_applicable=["T - mg = mv²/R : 최저점 식이므로 최고점에는 우선 적용 불가"],
    )


def build_cartesian_vector(problem: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    _set_model(model, problem_type="직교좌표 위치벡터 미분 문제", targets=["질점"], constraints=["i, j 또는 <x(t), y(t)> 성분으로 주어진 위치벡터"], methods=["벡터 미분"])
    _replace(
        bp,
        template_id="cartesian_position_vector",
        title="직교좌표 위치벡터 미분 풀이 골격",
        fbd=["운동학 문제이면 FBD보다 위치벡터 성분 확인이 우선"],
        coordinates=["직교좌표 i, j 방향"],
        applicable=["r(t) = x(t)i + y(t)j", "v(t) = dr/dt", "a(t) = d²r/dt²", "v(t) = dx/dt i + dy/dt j", "a(t) = d²x/dt² i + d²y/dt² j"],
        steps=["x(t), y(t) 성분을 분리한다.", "각 성분을 한 번 미분해 속도를 구한다.", "각 성분을 두 번 미분해 가속도를 구한다."],
        cautions=["r(t)라는 글자만으로 극좌표라고 판단하면 안 된다. i, j 성분이면 직교좌표 위치벡터이다."],
        not_applicable=["극좌표 가속도식 : e_r, e_θ 또는 θ(t)가 명시되지 않은 i, j 위치벡터 문제에서는 우선 적용 금지", "e_r, e_θ 기반 식 : 직교좌표 성분 문제에서는 우선 적용 금지"],
        suppressed=["polar_motion"],
    )


def build_polar_motion(problem: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    _set_model(model, problem_type="극좌표 운동학 문제", targets=["극좌표로 표현된 질점"], constraints=["r(t)와 θ(t) 또는 e_r/e_θ 단서가 필요"], methods=["극좌표 운동학"])
    _replace(
        bp,
        template_id="polar_motion",
        title="극좌표 운동학 풀이 골격",
        fbd=["운동학 문제이면 힘보다 r, θ 함수 확인이 우선"],
        coordinates=["e_r 방향", "e_θ 방향"],
        applicable=["v = r_dot e_r + r theta_dot e_theta", "a = (r_ddot - r theta_dot²)e_r + (r theta_ddot + 2r_dot theta_dot)e_theta"],
        not_applicable=["v(t)=dr/dt만으로 끝내기 : 극좌표에서는 기저벡터 변화 항이 필요"],
    )


def build_bullet_rotating_collision(problem: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    _set_model(
        model,
        problem_type="탄환/투사체-회전강체 충돌 문제",
        targets=["탄환/총알", "원판/바퀴/막대/회전판 등 고정축 강체"],
        constraints=["충돌 시간이 매우 짧음", "탄환이 박힌 뒤 강체와 함께 회전", "회전축 또는 고정축 기준 각운동량 보존"],
        risky=["단순 1차원 선운동량 보존만 우선 적용하는 것", "projectile 단어만 보고 포물선 운동으로 분류하는 것"],
        methods=["고정축 기준 각운동량 보존"],
    )
    _replace(
        bp,
        template_id="bullet_rotating_body_collision",
        title="탄환-회전강체 충돌 각운동량 풀이 골격",
        fbd=["충돌 전 탄환의 운동량 m_b v", "충돌 후 탄환+강체의 전체 관성모멘트 I_total", "고정축 반력은 축 기준 모멘트가 0일 수 있음"],
        coordinates=["고정축 O 기준", "충돌점까지의 수직거리 r"],
        applicable=["H_O(before) = H_O(after)", "m_b v r = I_totalω"],
        auxiliary=["I_total = I_body + m_b r²", "탄환이 박히면 완전비탄성 회전 충돌로 함께 회전"],
        conditions=["기준점 O를 고정축/핀에 잡아야 축 반력의 충격량 모멘트를 제거할 수 있음"],
        steps=["충돌 순간 기준점을 고정축 O로 잡는다.", "충돌 전 탄환의 O점 기준 각운동량을 쓴다.", "충돌 후 전체 관성모멘트와 각속도를 연결한다.", "H_O(before)=H_O(after)를 적용한다."],
        cautions=["축 반력의 외부 충격량 때문에 선운동량 보존은 일반적으로 성립하지 않을 수 있다."],
        not_applicable=["m1v1i + m2v2i = m1v1f + m2v2f : 고정축 반력이 있는 회전충돌에서 단순 1D 선운동량 보존만 우선 적용 금지", "포물선 운동 템플릿 : projectile/bullet가 회전강체에 박히는 문제에서는 우선 적용 금지"],
        suppressed=["projectile_motion", "one_dimensional_linear_collision", "general_planar_rigid_body"],
    )


def build_frictionless_pulley_block(problem: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    _set_model(model, problem_type="마찰 없는 수평면 블록 + 매달린 물체 연결 문제", targets=["수평면 위 블록 A", "매달린 물체 B"], constraints=["마찰 없음 f=0", "줄 조건 |a_A|=|a_B|"], methods=["뉴턴 제2법칙"])
    _replace(
        bp,
        template_id="frictionless_pulley_block",
        title="마찰 없는 수평면 블록-매달린 물체 풀이 골격",
        fbd=["블록 A: 중력 m_Ag", "블록 A: 수직항력 N_A", "블록 A: 장력 T", "물체 B: 중력 m_Bg", "물체 B: 장력 T"],
        coordinates=["블록 A: 수평 운동 방향", "물체 B: 아래 방향을 양의 방향"],
        applicable=["f = 0", "N_A = m_Ag", "T = m_Aa", "m_Bg - T = m_Ba"],
        auxiliary=["줄 조건: |a_A| = |a_B| = a"],
        cautions=["frictionless/smooth/negligible friction 조건이면 μ가 언급되어도 f=0을 우선 적용한다."],
        not_applicable=["f = μN_A : 마찰 없는 수평면에서는 적용 불가", "T - f = m_Aa : 최종 적용식은 f=0을 대입해 T=m_Aa로 정리"],
        suppressed=["frictional_horizontal_block_hanging_mass", "ideal_atwood"],
    )


def build_banked_friction_max(problem: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    _set_model(model, problem_type="마찰 있는 경사진 커브 최대속도 문제", targets=["자동차"], constraints=["최대속도에서 마찰은 보통 경사면 아래쪽으로 작용"], methods=["중심방향 뉴턴 제2법칙"])
    _replace(
        bp,
        template_id="banked_curve_with_friction_max_speed",
        title="마찰 있는 경사진 커브 최대속도 풀이 골격",
        fbd=["중력 mg", "수직항력 N", "정지마찰력 f"],
        coordinates=["수직 방향", "중심 방향"],
        applicable=["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"],
        cautions=["마찰 있는 경사진 커브에서는 마찰 없는 설계속도 식 tanθ = v²/(gR)만 단독으로 적용하면 부족하다."],
        not_applicable=["N = mg : 경사진 커브에서는 수직항력의 수직 성분만 mg와 균형", "μ_s ≥ v²/(gR) : 평평한 커브 식이므로 적용 불가", "tanθ = v²/(gR)만 단독 적용 : 마찰 없는 설계속도 조건"],
        suppressed=["flat_curve_friction", "banked_curve_frictionless"],
    )


def build_banked_friction_min(problem: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    _set_model(model, problem_type="마찰 있는 경사진 커브 최소속도 문제", targets=["자동차"], constraints=["최소속도에서 마찰 방향은 최대속도와 반대일 수 있음"], methods=["중심방향 뉴턴 제2법칙"])
    _replace(
        bp,
        template_id="banked_curve_with_friction_min_speed",
        title="마찰 있는 경사진 커브 최소속도 풀이 골격",
        fbd=["중력 mg", "수직항력 N", "정지마찰력 f"],
        coordinates=["수직 방향", "중심 방향"],
        applicable=["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"],
        cautions=["최소속도에서는 자동차가 아래쪽으로 미끄러지려는 경향이 있어 마찰 방향이 최대속도와 반대일 수 있다."],
        not_applicable=["N = mg : 경사진 커브에서는 적용 불가", "μ_s ≥ v²/(gR) : 평평한 커브 식", "tanθ = v²/(gR)만 단독 적용 : 마찰 없는 조건"],
        suppressed=["flat_curve_friction", "banked_curve_frictionless"],
    )


def build_vertical_track_bottom(problem: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    _set_model(model, problem_type="수직 원운동 트랙 최저점 수직항력 문제", targets=["트랙/레일 위 물체"], constraints=["최저점에서 중심 방향은 위쪽"], methods=["중심방향 뉴턴 제2법칙"])
    _replace(
        bp,
        template_id="vertical_circle_track_bottom",
        title="수직 원운동 트랙 최저점 수직항력 풀이 골격",
        fbd=["중력 mg 아래", "수직항력 N 위쪽/중심 방향"],
        coordinates=["최저점에서 중심 방향은 위쪽"],
        applicable=["N - mg = mv²/R", "N = mg + mv²/R"],
        not_applicable=["T - mg = mv²/R : 트랙/레일 문제에서는 장력 T가 아니라 수직항력 N 사용"],
    )


def build_generic_planar(problem: str, model: ProblemModel, bp: SolutionBlueprint) -> None:
    _set_model(model, problem_type="강체 일반 평면운동", targets=["질량중심 G와 강체 회전"], methods=["ΣF=ma_G", "ΣM_G=I_Gα"])
    _replace(
        bp,
        template_id="general_planar_rigid_body",
        title="강체 일반 평면운동 기본 골격",
        fbd=["외력", "중력", "지점반력/접촉력"],
        coordinates=["x-y 병진 좌표", "회전 양의 방향"],
        applicable=["ΣF = ma_G", "ΣM_G = I_Gα", "v_B = v_A + ω × r_B/A"],
        cautions=["더 구체적인 충돌/순간중심/구름 조건이 있으면 해당 전용 템플릿이 우선입니다."],
    )


TemplateBuilder = Callable[[str, ProblemModel, SolutionBlueprint], None]

TEMPLATE_REBUILDERS: Dict[str, TemplateBuilder] = {
    "conical_pendulum": build_conical,
    "sliding_rotation": build_sliding_rotation,
    "pure_rolling": build_pure_rolling,
    "vertical_circle_string_bottom": build_vertical_string_bottom,
    "vertical_circle_string_top": build_vertical_string_top,
    "vertical_circle_track_bottom": build_vertical_track_bottom,
    "cartesian_position_vector": build_cartesian_vector,
    "polar_motion": build_polar_motion,
    "bullet_rotating_body_collision": build_bullet_rotating_collision,
    "frictionless_pulley_block": build_frictionless_pulley_block,
    "banked_curve_with_friction_max_speed": build_banked_friction_max,
    "banked_curve_with_friction_min_speed": build_banked_friction_min,
    "general_planar_rigid_body": build_generic_planar,
}

GPT_CANDIDATE_TO_TEMPLATE_ID: Dict[str, str] = {
    "conical_pendulum": "conical_pendulum",
    "sliding_rotation": "sliding_rotation",
    "pure_rolling": "pure_rolling",
    "vertical_circle_string_bottom": "vertical_circle_string_bottom",
    "vertical_circle_string_top": "vertical_circle_string_top",
    "vertical_circle_track_bottom": "vertical_circle_track_bottom",
    "cartesian_position_vector": "cartesian_position_vector",
    "polar_motion": "polar_motion",
    "bullet_rotating_body_collision": "bullet_rotating_body_collision",
    "frictionless_pulley_block": "frictionless_pulley_block",
    "banked_curve_with_friction_max_speed": "banked_curve_with_friction_max_speed",
    "banked_curve_with_friction_min_speed": "banked_curve_with_friction_min_speed",
    "general_planar_rigid_body": "general_planar_rigid_body",
}

MORE_SPECIFIC_THAN_GENERIC = {
    "conical_pendulum",
    "sliding_rotation",
    "vertical_circle_string_bottom",
    "vertical_circle_string_top",
    "vertical_circle_track_bottom",
    "cartesian_position_vector",
    "polar_motion",
    "bullet_rotating_body_collision",
    "frictionless_pulley_block",
    "banked_curve_with_friction_max_speed",
    "banked_curve_with_friction_min_speed",
}


def current_template_id(model: ProblemModel, bp: SolutionBlueprint) -> str:
    return str(getattr(bp, "template_id", "")) or str(getattr(bp, "final_template_id", "")) or model.problem_type


def is_generic_current(model: ProblemModel, bp: SolutionBlueprint) -> bool:
    text = f"{model.problem_type} {bp.title}"
    generic_words = ["일반", "기본", "강체 일반", "원운동 조건", "복합", "가능성", "정보 부족"]
    return any(word in text for word in generic_words)


def required_features_satisfied(candidate: str, problem: str, detected_features: Optional[dict] = None) -> bool:
    sem = semantic_flags(problem)
    df = detected_features or {}
    if candidate == "conical_pendulum":
        return sem.conical_explicit or sem.conical_structural or bool(df.get("has_string") and (df.get("has_horizontal_circle") or df.get("has_circular_motion")))
    if candidate == "sliding_rotation":
        return (sem.slip_present and (sem.rolling_word or sem.rotation_word)) or bool(df.get("has_slipping") and (df.get("has_rolling") or df.get("has_rotation")))
    if candidate == "pure_rolling":
        return sem.explicit_pure_rolling and not sem.slip_present
    if candidate == "vertical_circle_string_bottom":
        return sem.string_support and sem.bottom_position
    if candidate == "vertical_circle_string_top":
        return sem.string_support and sem.top_position
    if candidate == "vertical_circle_track_bottom":
        return sem.track_support and sem.bottom_position
    if candidate == "cartesian_position_vector":
        return sem.cartesian_position_vector or bool(df.get("has_cartesian_vector"))
    if candidate == "polar_motion":
        return sem.polar_motion or bool(df.get("has_polar_vector"))
    if candidate == "bullet_rotating_body_collision":
        return sem.bullet_rotating_body_collision or bool(df.get("has_collision") and df.get("has_fixed_axis"))
    if candidate == "frictionless_pulley_block":
        return sem.frictionless and sem.horizontal_table and sem.hanging_mass and sem.pulley
    if candidate.startswith("banked_curve_with_friction"):
        return sem.banked_curve and (sem.friction_present or bool(df.get("friction_mode") not in (None, "none", "frictionless")))
    if candidate == "general_planar_rigid_body":
        return True
    return False


@dataclass
class RebuildDecision:
    applied: bool
    final_template_id: str
    reason: str


def rebuild_from_template_id(template_id: str, problem: str, model: ProblemModel, bp: SolutionBlueprint) -> bool:
    builder = TEMPLATE_REBUILDERS.get(template_id)
    if not builder:
        return False
    builder(problem, model, bp)
    apply_final_consistency_guard(bp, problem)
    return True


def reconcile_and_rebuild(
    *,
    problem: str,
    model: ProblemModel,
    bp: SolutionBlueprint,
    ai_candidate: str,
    ai_confidence: float,
    detected_features: Optional[dict] = None,
    rule_confidence: float = 0.0,
    risk_flags: Optional[Sequence[str]] = None,
) -> RebuildDecision:
    template_id = GPT_CANDIDATE_TO_TEMPLATE_ID.get(ai_candidate)
    bp.rule_template_id = current_template_id(model, bp)  # type: ignore[attr-defined]
    if not template_id:
        bp.reconciliation_status = "no_mapping"  # type: ignore[attr-defined]
        return RebuildDecision(False, current_template_id(model, bp), f"GPT 후보 {ai_candidate}에 대한 내부 템플릿 매핑 없음")
    if ai_confidence < 0.50:
        bp.reconciliation_status = "low_ai_confidence"  # type: ignore[attr-defined]
        bp.ambiguity_notes.append("AI confidence가 0.50 미만이어서 단일 템플릿으로 확정하지 않습니다.")
        return RebuildDecision(False, current_template_id(model, bp), "AI confidence가 낮음")

    sem_ok = required_features_satisfied(template_id, problem, detected_features)
    generic = is_generic_current(model, bp)
    more_specific = template_id in MORE_SPECIFIC_THAN_GENERIC
    risk = bool(risk_flags)
    current_id = current_template_id(model, bp)
    same = template_id == current_id or template_id in current_id

    if ai_confidence >= 0.84 and (sem_ok or generic or risk or same):
        rebuild_from_template_id(template_id, problem, model, bp)
        bp.reconciliation_status = "rebuilt_from_ai_candidate"  # type: ignore[attr-defined]
        bp.final_template_id = template_id  # type: ignore[attr-defined]
        bp.cautions.append(f"AI 후보 {ai_candidate}와 물리 단서 검증 결과 {template_id} 템플릿으로 재선택했습니다.")
        return RebuildDecision(True, template_id, "AI confidence 충분 + 단서/위험 조건 충족")

    if ai_confidence >= 0.72 and more_specific and (generic or risk) and sem_ok:
        rebuild_from_template_id(template_id, problem, model, bp)
        bp.reconciliation_status = "rebuilt_more_specific_template"  # type: ignore[attr-defined]
        bp.final_template_id = template_id  # type: ignore[attr-defined]
        bp.cautions.append(f"기존 결과보다 구체적인 AI 후보 {template_id}로 템플릿을 재생성했습니다.")
        return RebuildDecision(True, template_id, "더 구체적 템플릿으로 재선택")

    bp.reconciliation_status = "candidate_recorded_not_rebuilt"  # type: ignore[attr-defined]
    if not sem_ok:
        bp.ambiguity_notes.append(f"AI 후보 {template_id}의 필수 물리 단서가 충분하지 않아 템플릿을 확정하지 않았습니다.")
    else:
        bp.ambiguity_notes.append(f"AI 후보 {template_id}와 규칙 결과를 함께 검토해야 합니다.")
    return RebuildDecision(False, current_template_id(model, bp), "재선택 기준 미충족")
