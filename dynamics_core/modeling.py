from __future__ import annotations

import re
from typing import Dict, List

from .models import FeatureReport, Recommendation, ProblemModel, SolutionBlueprint
from .expert_templates import apply_expert_templates
from .fourth_templates import apply_fourth_rework_templates


def _uniq(items: List[str]) -> List[str]:
    return list(dict.fromkeys([x for x in items if x]))


def extract_known_quantities(problem: str) -> List[str]:
    patterns = [
        (r"m\s*=\s*[-+]?\d+(?:\.\d+)?\s*kg", "질량"),
        (r"[-+]?\d+(?:\.\d+)?\s*kg\s*(?:인|의|짜리)?", "질량"),
        (r"[-+]?\d+(?:\.\d+)?\s*N\s*(?:의|짜리|인)?", "힘"),
        (r"[-+]?\d+(?:\.\d+)?\s*m/s(?:\^2|²)?\s*(?:로|의)?", "속도/가속도"),
        (r"[-+]?\d+(?:\.\d+)?\s*rad/s(?:\^2|²)?\s*(?:로|의)?", "각속도/각가속도"),
        (r"[-+]?\d+(?:\.\d+)?\s*m\b\s*(?:를|을|의|인|짜리|이동|높이)?", "길이/거리/높이"),
        (r"[-+]?\d+(?:\.\d+)?\s*(?:초|s)\b", "시간"),
        (r"\d+(?:\.\d+)?\s*도", "각도"),
        (r"μ\s*=\s*\d+(?:\.\d+)?|mu\s*=\s*\d+(?:\.\d+)?|마찰계수\s*\d+(?:\.\d+)?", "마찰계수"),
        (r"e\s*=\s*\d+(?:\.\d+)?|반발계수\s*\d+(?:\.\d+)?", "반발계수"),
        (r"I\s*=\s*[^,.;。\n]+|관성모멘트\s*[^,.;。\n]+", "관성모멘트"),
        (r"k\s*=\s*[-+]?\d+(?:\.\d+)?|스프링\s*상수\s*[-+]?\d+(?:\.\d+)?", "스프링 상수"),
    ]
    found: List[str] = []
    for pattern, label in patterns:
        for m in re.finditer(pattern, problem, flags=re.IGNORECASE):
            found.append(f"{label}: {m.group(0).strip()}")
    return _uniq(found)[:12]


def infer_targets(problem: str, cues: Dict[str, bool]) -> List[str]:
    targets: List[str] = []
    if cues.get("pulley_connected"):
        targets.append("연결된 각 물체")
    if cues.get("incline"):
        targets.append("경사면 위 물체")
    if cues.get("projectile"):
        targets.append("투사된 입자/공")
    if cues.get("rolling"):
        targets.append("구르는 강체의 질량중심 G")
    if cues.get("rigid_body"):
        if cues.get("fixed_axis"):
            targets.append("고정축 주위로 도는 강체")
        else:
            targets.append("강체 전체와 질량중심 G")
    if cues.get("circular"):
        targets.append("원궤도 위 입자/블록")
    if cues.get("collision"):
        targets.append("충돌 전후의 계 전체")
    if cues.get("relative_motion") or cues.get("instant_center"):
        targets.append("강체 위 기준점 A와 관심점 B")
    # 흔한 물체명 보강
    for name in ["블록", "물체", "공", "막대", "원판", "원통", "차", "입자", "구슬"]:
        if name in problem and name not in " ".join(targets):
            targets.append(name)
            break
    return _uniq(targets) or ["문제에서 관심 있는 물체 하나"]


def build_problem_model(problem: str, features: FeatureReport, rec: Recommendation, goal: str = "자동 추정") -> ProblemModel:
    cues = features.cues
    requested = features.requested_quantity or goal or "자동 추정"
    targets = infer_targets(problem, cues)
    known = extract_known_quantities(problem)
    motion: List[str] = []
    forces: List[str] = []
    ignored: List[str] = []
    constraints: List[str] = []
    conservation: List[str] = []
    coords: List[str] = []
    allowed: List[str] = []
    risky: List[str] = []
    assumptions: List[str] = []
    problem_type = "일반 동역학 문제"

    forces.append("중력 mg")
    if cues.get("incline") or cues.get("friction") or cues.get("no_friction") or cues.get("circular") or cues.get("force") or cues.get("rolling"):
        forces.append("수직항력 N")
    if cues.get("tension"):
        forces.append("장력 T")
    if cues.get("friction"):
        forces.append("마찰력 f: 운동/운동 경향을 방해하는 방향")
    if cues.get("spring"):
        forces.append("스프링 힘 kx 또는 탄성 위치에너지 1/2kx²")
    if cues.get("force"):
        forces.append("문제에서 주어진 외력/하중")

    if cues.get("no_friction"):
        ignored.append("마찰력 f = 0")
    if cues.get("no_air_resistance"):
        ignored.append("공기저항 무시")
    if cues.get("no_collision"):
        ignored.append("충돌 전후 방정식은 아직 적용하지 않음")
    if cues.get("no_rotation") and cues.get("translation_only"):
        ignored.append("회전 운동 방정식은 우선 제외")

    if cues.get("projectile"):
        problem_type = "포물선 운동"
        motion.extend(["x방향 등속", "y방향 등가속도 -g"])
        coords.extend(["수평 x축", "수직 y축, 위쪽을 +로 잡는 것이 보통 편함"])
        constraints.extend(["최고점: v_y = 0", "착지/도달 조건: y = 지정 높이"])
        allowed.append("운동학")
        if cues.get("air_resistance"):
            risky.append("공기저항이 있는데 표준 포물선 공식만 사용하는 것")
        else:
            assumptions.append("공기저항을 무시할 때 표준 포물선 모델 가능")

    if cues.get("incline"):
        problem_type = "경사면 질점 문제" if problem_type == "일반 동역학 문제" else problem_type
        coords.extend(["경사면 평행 방향", "경사면 수직 방향"])
        constraints.append("수직 방향 가속도가 없으면 ΣF_⊥ = 0")
        if cues.get("friction"):
            constraints.append("마찰 있음: f = μN 또는 f ≤ μ_sN")
        if cues.get("no_friction"):
            constraints.append("매끈한/마찰 무시: f = 0")
        allowed.append("뉴턴 제2법칙 F=ma")

    if cues.get("height"):
        conservation.append("마찰/손실이 없거나 일을 계산할 수 있으면 에너지식 사용 가능")
        allowed.append("일-에너지 원리")
        if cues.get("no_friction"):
            conservation.append("마찰 없음: T1 + V1 = T2 + V2 후보")
        if cues.get("friction") or cues.get("nonconservative_work"):
            conservation.append("비보존력 일 포함: T1 + V1 + W_nc = T2 + V2")
            risky.append("마찰이 있는데 단순 역학적 에너지 보존을 쓰는 것")

    if cues.get("pulley_connected"):
        problem_type = "연결된 물체/도르래 문제"
        constraints.extend(["줄이 늘어나지 않으면 연결된 물체의 가속도 크기 관계를 세움", "이상적인 가벼운 줄/마찰 없는 도르래이면 같은 줄의 장력은 같음"])
        coords.append("각 물체의 실제 운동 방향을 +방향으로 잡으면 식이 단순해짐")
        allowed.append("뉴턴 제2법칙 F=ma")

    if cues.get("circular") or cues.get("normal_tangent"):
        problem_type = "원운동/법선-접선 좌표 문제" if problem_type == "일반 동역학 문제" else problem_type
        coords.extend(["법선 n방향: 곡률 중심 방향", "접선 t방향: 속도 방향"])
        constraints.extend(["a_n = v²/ρ", "a_t = dv/dt"])
        allowed.append("원운동 조건")
        risky.append("구심력을 별도 힘처럼 FBD에 추가하는 것")

    if cues.get("collision") or cues.get("momentum"):
        problem_type = "충격량-운동량/충돌 문제" if cues.get("collision") else "운동량 문제"
        constraints.extend(["충돌 전 상태와 충돌 후 상태를 분리", "계 선택 후 외부 충격량이 무시 가능한지 확인"])
        allowed.append("충격량-운동량")
        if cues.get("collision"):
            constraints.append("반발계수 e가 있으면 v_rel,after = e v_rel,before 식 추가")
            risky.append("완전탄성 조건 없이 운동에너지 보존을 가정하는 것")

    if cues.get("fixed_axis"):
        problem_type = "강체 고정축 회전"
        coords.append("고정축 O 기준 회전 방향을 +로 설정")
        constraints.extend(["ΣM_O = I_O α", "각운동학: ω² = ω₀² + 2αθ 또는 ω = ω₀ + αt"])
        allowed.append("강체 평면운동")
    elif cues.get("rolling"):
        problem_type = "순수 구름 운동"
        coords.extend(["질량중심 G의 병진 방향", "회전 양의 방향"])
        constraints.extend(["미끄러지지 않으면 v_G = ωR", "미끄러지지 않으면 a_G = αR"])
        conservation.append("순수 구름 에너지: T = 1/2mv_G² + 1/2I_Gω²")
        allowed.extend(["강체 평면운동", "일-에너지 원리"])
        risky.append("미끄러짐이 있는데 v=ωR을 무조건 쓰는 것")
    elif (cues.get("rigid_body") or cues.get("rotation") or cues.get("torque")) and not (cues.get("translation_only") and cues.get("no_rotation")):
        problem_type = "강체 일반 평면운동" if not cues.get("fixed_axis") else problem_type
        coords.extend(["질량중심 G의 x-y 좌표", "회전 방향"])
        constraints.extend(["ΣF = ma_G", "ΣM_G = I_G α"])
        allowed.append("강체 평면운동")

    if cues.get("translation_only") and cues.get("no_rotation"):
        problem_type = "순수 병진운동"
        motion.append("강체의 모든 점이 같은 속도/가속도를 가짐")
        allowed.extend(["운동학", "뉴턴 제2법칙 F=ma"])
        risky.append("막대라는 이유만으로 ΣM=Iα를 먼저 쓰는 것")

    if cues.get("relative_motion") or cues.get("instant_center"):
        problem_type = "상대속도/순간중심 문제"
        coords.extend(["고정 좌표계", "강체 또는 이동 좌표계"])
        constraints.extend(["v_B = v_A + ω × r_B/A", "a_B = a_A + α × r_B/A - ω² r_B/A"])
        if cues.get("instant_center"):
            constraints.append("순간중심 사용 시 v = ωr")
        allowed.append("상대속도/순간중심")

    if cues.get("polar"):
        coords.extend(["e_r 방향", "e_θ 방향"])
        constraints.extend(["v = ṙe_r + rθ̇e_θ", "a = (r̈-rθ̇²)e_r + (rθ̈+2ṙθ̇)e_θ"])
        allowed.append("운동학")

    if rec.primary not in allowed and rec.primary != "복합 풀이":
        allowed.append(rec.primary)
    if rec.primary == "복합 풀이":
        allowed.extend(rec.combined_methods)

    if not coords:
        coords.append("운동 방향을 +방향으로 먼저 정함")
    if not motion:
        motion.append("문제 문장에서 정지/등속/가속/회전 여부를 추가 확인")
    if not known:
        known.append("수치 물리량이 충분히 추출되지 않음: 그림/조건을 함께 입력하면 정확도 상승")

    return ProblemModel(
        problem_type=problem_type,
        analysis_targets=_uniq(targets),
        requested_quantity=requested,
        known_quantities=_uniq(known),
        motion_state=_uniq(motion),
        forces_present=_uniq(forces),
        forces_ignored=_uniq(ignored),
        constraints=_uniq(constraints),
        conservation_conditions=_uniq(conservation),
        coordinate_systems=_uniq(coords),
        allowed_methods=_uniq(allowed),
        risky_methods=_uniq(risky),
        assumptions=_uniq(assumptions),
    )


def build_solution_blueprint(model: ProblemModel, features: FeatureReport, rec: Recommendation, problem: str = "") -> SolutionBlueprint:
    cues = features.cues
    equations: List[str] = []
    aux: List[str] = []
    conditions: List[str] = []
    steps: List[str] = []
    warnings: List[str] = []
    checks: List[str] = ["마지막 답의 단위가 구하려는 물리량과 맞는지 확인", "부호가 실제 운동 방향과 맞는지 해석"]

    title = f"{model.problem_type} 풀이 골격"

    if cues.get("incline"):
        equations.extend(["ΣF_parallel = ma_parallel", "ΣF_perpendicular = ma_perpendicular 또는 0"])
        aux.extend(["mg sinθ: 경사면 평행 성분", "mg cosθ: 경사면 수직 성분"])
        if cues.get("friction"):
            aux.append("f_k = μ_k N 또는 f_s ≤ μ_s N")
        if cues.get("no_friction"):
            aux.append("f = 0")
        steps.extend(["경사면 위 물체만 떼어 그린다.", "경사면 평행/수직축으로 힘을 분해한다.", "수직방향에서 N을 먼저 구하거나 제거한다."])

    if cues.get("projectile"):
        equations.extend(["x = x0 + v0 cosθ · t", "y = y0 + v0 sinθ · t - 1/2gt²", "v_y = v0 sinθ - gt"])
        aux.extend(["최고점: v_y = 0", "착지/도달 조건: y = 목표 높이"])
        conditions.append("공기저항을 무시할 때 표준 포물선 식 사용")
        if cues.get("air_resistance"):
            warnings.append("공기저항을 무시하지 않으므로 위 표준식은 근사/비적용일 수 있음")
        steps.extend(["초기속도를 x, y 성분으로 나눈다.", "y방정식으로 시간을 먼저 구한다.", "구한 시간을 x방정식에 넣어 거리/위치를 구한다."])

    if cues.get("height") or cues.get("nonconservative_work") or rec.primary == "일-에너지 원리" or "일-에너지 원리" in rec.combined_methods:
        if cues.get("rolling"):
            equations.append("T1 + V1 + W_nc = T2 + V2,  T = 1/2mv_G² + 1/2I_Gω²")
            aux.append("순수 구름이면 v_G = ωR")
        else:
            equations.append("T1 + V1 + W_nc = T2 + V2")
            if cues.get("no_friction") and cues.get("height"):
                aux.append("마찰 없음 + 높이 변화만이면 mgh = 1/2mv² 형태 가능")
        if cues.get("friction"):
            aux.append("마찰 일: W_f = -f_k s")
        conditions.append("처음 상태와 마지막 상태를 명확히 잡아야 함")
        steps.extend(["초기/최종 위치를 표시한다.", "각 위치의 K, U_g, U_s를 표로 적는다.", "마찰/외력의 일이 있으면 W_nc에 넣는다."])

    if cues.get("collision") or rec.primary == "충격량-운동량" or "충격량-운동량" in rec.combined_methods:
        equations.extend(["Σm v_before + 외부충격량 = Σm v_after", "외부충격량 무시 가능 시 Σm v_before = Σm v_after"])
        if cues.get("collision"):
            aux.append("반발계수: e = (분리 상대속도)/(접근 상대속도)")
        conditions.append("충돌 시간 동안 외부 충격량이 무시 가능한지 확인")
        warnings.append("완전탄성 충돌이 아니면 운동에너지 보존을 쓰지 않음")
        steps.extend(["계를 정한다.", "충돌 전/후 속도 부호를 통일한다.", "운동량식과 반발계수식을 연립한다."])

    if cues.get("circular") or cues.get("normal_tangent") or rec.primary == "원운동 조건":
        equations.extend(["ΣF_n = m v²/ρ", "ΣF_t = m a_t"])
        aux.append("접촉 한계: N = 0 또는 T = 0")
        conditions.append("n방향은 항상 곡률 중심 방향")
        steps.extend(["관심 지점에서 중심 방향을 표시한다.", "n방향 실제 힘만 ΣF_n에 넣는다.", "필요하면 에너지식으로 v를 먼저 구한다."])
        warnings.append("구심력이라는 새 힘을 추가하지 말고 실제 힘의 n방향 합으로 처리")

    if cues.get("fixed_axis"):
        equations.extend(["ΣM_O = I_O α", "ω = ω0 + αt", "ω² = ω0² + 2αθ"])
        conditions.append("O는 고정축/힌지/핀 같은 회전 기준점")
        steps.extend(["회전축을 먼저 표시한다.", "축을 지나는 반력은 그 축 기준 토크가 0인지 확인한다.", "중력/외력이 만드는 모멘트를 부호와 함께 합한다."])
    elif (cues.get("rigid_body") or cues.get("rotation") or cues.get("torque") or cues.get("rolling")) and not (cues.get("translation_only") and cues.get("no_rotation")):
        equations.extend(["ΣF = ma_G", "ΣM_G = I_G α"])
        if cues.get("rolling"):
            equations.append("구름 운동에너지: T = 1/2mv_G² + 1/2I_Gω²")
            aux.extend(["v_G = ωR", "a_G = αR"])
            conditions.append("미끄러지지 않는 순수 구름 조건이 명시되어야 함")
        steps.extend(["질량중심 G를 표시한다.", "외력을 모두 그린다.", "병진식과 회전식을 함께 세운다."])

    if cues.get("relative_motion") or cues.get("instant_center"):
        equations.extend(["v_B = v_A + ω × r_B/A", "a_B = a_A + α × r_B/A - ω² r_B/A"])
        if cues.get("instant_center"):
            aux.append("순간중심 IC 기준: v_A = ω r_A/IC, v_B = ω r_B/IC")
        steps.extend(["각 점의 속도 방향을 먼저 표시한다.", "상대속도식을 벡터 방향으로 분해한다.", "순간중심을 쓸 수 있으면 속도 방향에 수직인 선의 교점을 찾는다."])

    if cues.get("polar"):
        equations.extend(["v = ṙe_r + rθ̇e_θ", "a = (r̈-rθ̇²)e_r + (rθ̈+2ṙθ̇)e_θ"])
        steps.append("r방향과 θ방향 성분을 따로 정리한다.")

    if cues.get("translation_only") and cues.get("no_rotation"):
        equations.append("회전 없음: 모든 점의 v, a가 같음. 필요 시 ΣF = ma_G만 사용")
        warnings.append("강체 모양이 있어도 회전 방정식을 자동으로 쓰지 않음")

    if not equations:
        equations.extend(rec.steps)
    if not steps:
        steps.extend(rec.steps)
    if not conditions:
        conditions.append("그림 조건과 문제의 생략 조건을 반드시 확인")

    blueprint = SolutionBlueprint(
        title=title,
        fbd_forces=model.forces_present,
        coordinate_guide=model.coordinate_systems,
        governing_equations=_uniq(equations),
        auxiliary_equations=_uniq(aux),
        application_conditions=_uniq(conditions),
        next_steps=_uniq(steps)[:10],
        warnings=_uniq(warnings + model.risky_methods),
        interpretation_checks=_uniq(checks),
    )
    blueprint = apply_expert_templates(problem, model, features, rec, blueprint)
    return apply_fourth_rework_templates(problem, model, features, rec, blueprint)
