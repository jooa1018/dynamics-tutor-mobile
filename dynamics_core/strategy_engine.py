from __future__ import annotations

from typing import Dict, List

from .concepts import METHODS
from .models import FeatureReport, Recommendation


def _score_add(scores: Dict[str, int], method: str, points: int, reasons: List[str], reason: str) -> None:
    scores[method] += points
    reasons.append(reason)


def recommend_strategy(features: FeatureReport, goal: str = "자동 추정") -> Recommendation:
    cues = features.cues
    effective_goal = features.requested_quantity if goal == "자동 추정" and features.requested_quantity else goal
    scores = {m: 0 for m in METHODS}
    reasons: List[str] = []
    cautions: List[str] = []
    combined: List[str] = []

    # 1) 운동학
    if cues["time"] or cues["distance"] or cues["constant_accel"]:
        _score_add(scores, "운동학", 2, reasons, "시간·거리·속도·가속도 사이의 관계가 보이면 운동학을 후보로 둡니다.")
    if cues["projectile"]:
        _score_add(scores, "운동학", 6, reasons, "포물선/투사 운동은 x방향과 y방향을 나누는 운동학이 기본 출발점입니다.")
    if cues.get("air_resistance") and cues["projectile"]:
        scores["운동학"] = max(0, scores["운동학"] - 2)
        cautions.append("공기저항을 고려하면 표준 포물선 공식만으로는 부족합니다. drag 모델 또는 수치해석이 필요할 수 있습니다.")
    if effective_goal in ["속도", "가속도", "시간", "위치/변위"] and not (cues["force"] or cues["friction"] or cues["tension"] or cues["height"] or cues["rotation"]):
        _score_add(scores, "운동학", 2, reasons, "구하는 값이 운동 상태이고 힘/에너지/회전 단서가 약하면 운동학 가능성이 큽니다.")

    # 2) 뉴턴 제2법칙
    if cues["force"] or cues["mass"] or cues["tension"] or cues["friction"]:
        _score_add(scores, "뉴턴 제2법칙 F=ma", 4, reasons, "힘·질량·장력·마찰이 실제로 주어지면 자유물체도와 ΣF=ma가 필요합니다.")
    if cues["pulley_connected"]:
        _score_add(scores, "뉴턴 제2법칙 F=ma", 4, reasons, "연결된 물체/도르래는 물체별 FBD와 가속도 구속조건을 함께 세워야 합니다.")
        combined.append("뉴턴 제2법칙 F=ma")
    if cues["incline"] and (effective_goal in ["가속도", "힘", "장력/마찰력"] or cues["friction"] or cues["mass"]):
        _score_add(scores, "뉴턴 제2법칙 F=ma", 3, reasons, "경사면에서 가속도나 힘을 묻는다면 경사면 방향/수직 방향으로 힘을 분해해야 합니다.")
    if effective_goal in ["힘", "장력/마찰력"]:
        _score_add(scores, "뉴턴 제2법칙 F=ma", 3, reasons, "구하려는 값이 힘 계열이면 힘의 평형/운동방정식이 직접적입니다.")

    # 3) 일-에너지
    if cues["height"] or cues["spring"] or cues["variable_force"]:
        _score_add(scores, "일-에너지 원리", 4, reasons, "높이 변화·스프링·힘-변위 그래프는 일-에너지 원리와 잘 연결됩니다.")
    if cues["distance"] and not cues["time"] and effective_goal in ["속도", "에너지/일", "위치/변위"]:
        _score_add(scores, "일-에너지 원리", 2, reasons, "시간이 없고 거리/높이와 속도를 연결해야 하면 에너지식이 짧을 수 있습니다.")
    if cues["friction"] and cues["distance"]:
        _score_add(scores, "일-에너지 원리", 2, reasons, "마찰력이 일정 거리 동안 한 일은 에너지식에 포함하기 좋습니다.")
    if cues["no_friction"] and cues["height"] and effective_goal == "속도":
        _score_add(scores, "일-에너지 원리", 3, reasons, "마찰이 없고 높이 변화로 속도를 묻는다면 역학적 에너지 보존을 우선 의심합니다.")
    if cues.get("nonconservative_work"):
        _score_add(scores, "일-에너지 원리", 2, reasons, "손실/비보존력의 일이 언급되면 T1+V1+W_nc=T2+V2 형태를 확인합니다.")

    # 4) 충격량-운동량
    if cues["collision"]:
        _score_add(scores, "충격량-운동량", 6, reasons, "충돌 전후 속도는 운동량 보존과 반발계수부터 확인합니다.")
    if cues["impulse"]:
        _score_add(scores, "충격량-운동량", 5, reasons, "짧은 시간 동안 큰 힘/충격량이 나오면 ∫Fdt = Δp를 떠올립니다.")
    if cues["momentum"]:
        _score_add(scores, "충격량-운동량", 4, reasons, "운동량이라는 표현이 직접 나오므로 선운동량 보존/변화를 확인합니다.")
    if cues["angular_momentum"]:
        _score_add(scores, "충격량-운동량", 3, reasons, "각운동량이 직접 언급되면 기준점에 대한 외부 모멘트 충격량을 확인합니다.")
        combined.append("강체 평면운동")
    if cues["no_collision"]:
        scores["충격량-운동량"] = max(0, scores["충격량-운동량"] - 3)
        cautions.append("'충돌하지 않음/충돌 전' 표현은 충돌 후 속도 문제가 아닐 수 있습니다. 현재 운동량 p=mv와 충돌 방정식을 구분하세요.")
    if effective_goal == "충돌 후 속도":
        _score_add(scores, "충격량-운동량", 4, reasons, "구하려는 값이 충돌 후 속도이므로 운동량 보존식과 반발계수식이 핵심입니다.")

    # 5) 원운동 / n-t
    if cues["circular"] or cues["normal_tangent"]:
        _score_add(scores, "원운동 조건", 5, reasons, "원궤도/곡률반지름/법선-접선 단서가 있으면 ΣF_n=mv²/ρ와 ΣF_t=ma_t를 확인합니다.")
    if effective_goal == "접촉 유지 조건":
        _score_add(scores, "원운동 조건", 4, reasons, "접촉 유지/이탈 조건은 보통 N=0 또는 T=0 같은 한계 조건과 원운동식을 연결합니다.")
    if cues["polar"]:
        _score_add(scores, "운동학", 3, reasons, "극좌표 단서가 있으면 r, θ 방향 속도/가속도 성분을 먼저 세워야 합니다.")
        combined.append("운동학")

    # 6) 강체/회전
    if (cues["rotation"] or cues["rolling"] or cues["torque"] or cues["rigid_body"] or cues["fixed_axis"]) and not (cues["translation_only"] and cues["no_rotation"]):
        _score_add(scores, "강체 평면운동", 4, reasons, "강체·회전·토크·관성모멘트·굴림이 있으면 질점 모델만으로 부족할 수 있습니다.")
    if cues["fixed_axis"]:
        _score_add(scores, "강체 평면운동", 4, reasons, "고정축 회전은 축 기준 모멘트 방정식 ΣM_O=I_Oα가 핵심입니다.")
    if cues["rolling"]:
        _score_add(scores, "강체 평면운동", 4, reasons, "순수 구름은 병진과 회전이 v=ωR, a=αR로 묶입니다.")
    if cues["translation_only"] and cues["no_rotation"]:
        scores["강체 평면운동"] = max(0, scores["강체 평면운동"] - 4)
        cautions.append("막대/강체라는 말이 있어도 '회전하지 않고 병진운동'이면 우선 질점처럼 병진운동으로 모델링합니다.")
    if effective_goal in ["각속도/각가속도", "토크"]:
        _score_add(scores, "강체 평면운동", 4, reasons, "각속도·각가속도·토크를 묻는다면 ΣM=Iα 또는 회전 운동학이 필요합니다.")

    # 7) 상대속도/순간중심
    if cues["relative_motion"]:
        _score_add(scores, "상대속도/순간중심", 5, reasons, "상대속도/상대가속도 표현이 있으므로 한 점의 운동을 다른 점 기준으로 연결해야 합니다.")
    if cues["instant_center"]:
        _score_add(scores, "상대속도/순간중심", 7, reasons, "순간중심은 강체 평면운동에서 속도 방향과 크기를 잡는 핵심 도구입니다.")
        combined.append("강체 평면운동")

    # 복합 구조
    if cues["height"] and cues["circular"]:
        combined.extend(["일-에너지 원리", "원운동 조건"])
        scores["복합 풀이"] = max(scores["복합 풀이"], max(scores["일-에너지 원리"], scores["원운동 조건"]) + 2)
        reasons.append("높이로 속도를 구한 뒤, 그 속도를 원운동 접촉 조건에 넣는 복합 구조일 가능성이 큽니다.")
    if cues["rolling"] and (cues["height"] or cues["spring"] or cues["incline"]):
        combined.extend(["일-에너지 원리", "강체 평면운동"])
        scores["복합 풀이"] = max(scores["복합 풀이"], max(scores["일-에너지 원리"], scores["강체 평면운동"]) + 2)
        reasons.append("굴림 + 높이/경사면/스프링은 병진에너지와 회전에너지를 함께 넣는 복합 문제입니다.")
    if cues["tension"] and (cues["torque"] or cues["rigid_body"] or cues["fixed_axis"]):
        combined.extend(["뉴턴 제2법칙 F=ma", "강체 평면운동"])
        scores["복합 풀이"] = max(scores["복합 풀이"], max(scores["뉴턴 제2법칙 F=ma"], scores["강체 평면운동"]) + 2)
        reasons.append("질량/관성모멘트가 있는 도르래·강체가 있으면 ΣF=ma와 ΣM=Iα를 함께 써야 할 수 있습니다.")
    if cues["collision"] and (cues["rotation"] or cues["rigid_body"] or cues["angular_momentum"]):
        combined.extend(["충격량-운동량", "강체 평면운동"])
        scores["복합 풀이"] = max(scores["복합 풀이"], max(scores["충격량-운동량"], scores["강체 평면운동"]) + 1)
        reasons.append("충돌 후 회전이 생기면 선운동량뿐 아니라 각운동량 조건도 확인해야 합니다.")
    if cues["friction"] and cues["incline"] and effective_goal == "속도" and cues["distance"]:
        combined.extend(["뉴턴 제2법칙 F=ma", "일-에너지 원리"])
        scores["복합 풀이"] = max(scores["복합 풀이"], 6)
        reasons.append("마찰 있는 경사면에서 거리 후 속도는 F=ma로 가속도를 구하거나, 마찰 일을 포함한 에너지식으로 풀 수 있습니다.")
    if cues["pulley_connected"] and cues["fixed_axis"]:
        combined.extend(["뉴턴 제2법칙 F=ma", "강체 평면운동"])
        scores["복합 풀이"] = max(scores["복합 풀이"], 8)

    # 주의사항
    if cues["no_friction"]:
        cautions.append("마찰 없음/매끈한 면/마찰 무시는 마찰력을 그리지 말라는 뜻입니다. 단, 수직항력은 여전히 있을 수 있습니다.")
    if cues["friction"]:
        cautions.append("마찰 방향은 '상대운동 또는 상대운동하려는 경향'을 방해하는 방향입니다.")
    if cues["collision"]:
        cautions.append("충돌에서 운동에너지는 완전탄성 조건이 없으면 보존된다고 단정하면 안 됩니다.")
    if cues["spring"]:
        cautions.append("스프링/용수철 문제의 '탄성'과 탄성 충돌의 '탄성'을 구분하세요.")
    if cues["circular"]:
        cautions.append("구심력은 새로 추가하는 힘이 아니라, 반지름 방향 실제 힘들의 합입니다.")
    if cues["projectile"]:
        cautions.append("포물선 최고점에서 0이 되는 것은 수직속도 vy이고, 전체 속도는 보통 0이 아닙니다.")
    if cues["rolling"]:
        cautions.append("v=ωR은 미끄러지지 않는 순수 구름 조건에서만 바로 쓸 수 있습니다.")
    if cues["instant_center"]:
        cautions.append("순간중심은 속도 해석 도구입니다. '순간'이라는 말만 보고 충격량 문제로 분류하지 않습니다.")
    if cues["air_resistance"]:
        cautions.append("공기저항이 있으면 역학적 에너지 보존이나 표준 포물선 식을 그대로 쓰기 어렵습니다.")

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary, top = sorted_scores[0]

    if primary != "복합 풀이":
        strong = [m for m, s in sorted_scores if m != "복합 풀이" and s >= 6]
        if len(strong) >= 2 and (cues["height"] or cues["circular"] or cues["rolling"] or cues["collision"] or cues["torque"] or cues["fixed_axis"] or cues["pulley_connected"]):
            primary = "복합 풀이"
            scores["복합 풀이"] = max(scores["복합 풀이"], top + 1)
            combined.extend(strong[:3])
            top = scores["복합 풀이"]

    combined = list(dict.fromkeys([m for m in combined if m in METHODS and m != "복합 풀이"]))
    if primary == "복합 풀이" and not combined:
        combined = [m for m, s in sorted_scores if m != "복합 풀이" and s >= max(4, top - 4)][:3]

    steps = strategy_steps(primary, combined, cues)
    cue_count = sum(cues.values())
    confidence = "높음" if top >= 8 and cue_count >= 3 else "보통" if top >= 4 else "낮음"
    if features.warnings:
        confidence = "낮음~보통" if confidence == "보통" else confidence

    return Recommendation(
        primary=primary,
        scores=scores,
        reasons=list(dict.fromkeys(reasons)),
        cautions=list(dict.fromkeys(cautions)),
        steps=steps,
        combined_methods=combined,
        confidence=confidence,
    )


def strategy_steps(primary: str, combined: List[str], cues: Dict[str, bool]) -> List[str]:
    methods = set(combined or [primary])
    if primary == "복합 풀이":
        if {"일-에너지 원리", "원운동 조건"}.issubset(methods):
            return [
                "처음 위치와 관심 지점의 높이를 정합니다.",
                "마찰이 없거나 마찰 일을 알 수 있다면 에너지식으로 관심 지점 속도 v를 구합니다.",
                "그 지점에서 중심 방향을 잡고 실제 힘들의 합을 ΣF_n = mv²/R에 넣습니다.",
                "접촉 유지라면 N=0 또는 T=0 같은 한계 조건을 적용합니다.",
            ]
        if {"일-에너지 원리", "강체 평면운동"}.issubset(methods):
            return [
                "처음/끝 상태를 정하고 높이 또는 스프링 에너지 변화를 씁니다.",
                "운동에너지에 병진 1/2mv_G²와 회전 1/2I_Gω²를 모두 넣습니다.",
                "순수 구름이면 v_G=ωR, a_G=αR을 연결합니다.",
                "I=βmR² 값을 확인해 최종 속도 또는 각속도를 구합니다.",
            ]
        if {"뉴턴 제2법칙 F=ma", "강체 평면운동"}.issubset(methods):
            return [
                "각 물체의 FBD를 따로 그립니다.",
                "병진 운동은 ΣF=ma로 씁니다.",
                "회전하는 도르래/강체에는 ΣM=Iα를 씁니다.",
                "줄/구름 조건으로 a=αR을 연결한 뒤 연립합니다.",
            ]
        return ["문제를 구간 또는 물체별로 나눕니다.", "각 구간에서 필요한 원리를 정합니다.", "공통 변수로 식들을 연결합니다."]
    if primary == "운동학":
        if cues.get("projectile"):
            return ["v0를 vx=v0cosθ, vy=v0sinθ로 나눕니다.", "x방향은 등속, y방향은 -g 등가속도로 둡니다.", "최고점에서는 vy=0만 사용합니다.", "시간을 구한 뒤 x=vx t로 거리를 구합니다."]
        if cues.get("polar"):
            return ["위치벡터를 r, θ로 표현합니다.", "v = ṙ e_r + rθ̇ e_θ를 씁니다.", "a = (r̈-rθ̇²)e_r + (rθ̈+2ṙθ̇)e_θ를 씁니다.", "문제의 구속조건으로 r(t) 또는 θ(t)를 연결합니다."]
        return ["양의 방향을 정합니다.", "u, v, a, s, t를 표로 정리합니다.", "미지수가 하나 남는 등가속도 식을 고릅니다."]
    if primary == "뉴턴 제2법칙 F=ma":
        return ["분석할 물체를 하나씩 떼어 FBD를 그립니다.", "가속도 방향 또는 경사면 방향으로 좌표축을 잡습니다.", "각 축에 대해 ΣF=ma를 세웁니다.", "마찰/장력/수직항력 방향을 검산합니다."]
    if primary == "일-에너지 원리":
        return ["처음 상태와 마지막 상태를 정합니다.", "K, U_g, U_s를 적습니다.", "마찰이나 외력이 한 일이 있으면 포함합니다.", "단위가 J 또는 m/s로 맞는지 확인합니다."]
    if primary == "충격량-운동량":
        return ["충돌 전/후 또는 힘이 작용하기 전/후를 나눕니다.", "외부 충격량을 무시할 수 있는지 확인합니다.", "운동량 보존식 또는 ∫Fdt=Δp를 씁니다.", "필요하면 반발계수 식을 추가합니다."]
    if primary == "원운동 조건":
        return ["중심/법선 방향을 +로 정합니다.", "반지름 방향 실제 힘만 모읍니다.", "ΣF_n=mv²/R을 씁니다.", "접선 방향이 필요하면 ΣF_t=ma_t를 별도로 씁니다."]
    if primary == "강체 평면운동":
        if cues.get("fixed_axis"):
            return ["고정축 O를 찾습니다.", "O점 기준으로 모멘트를 합산합니다.", "ΣM_O=I_Oα를 씁니다.", "각운동학 식으로 ω, θ, α를 연결합니다."]
        return ["질점으로 볼 수 있는지, 회전까지 필요한지 구분합니다.", "관성모멘트 I를 고릅니다.", "ΣF=ma_G와 ΣM_G=I_Gα를 필요에 따라 함께 씁니다.", "구름이면 v_G=ωR, a_G=αR 조건을 확인합니다."]
    if primary == "상대속도/순간중심":
        return ["강체 위 두 점의 속도 방향을 먼저 표시합니다.", "순간중심을 찾을 수 있으면 각 점 속도 방향에 수직인 선을 그어 만나는 점을 찾습니다.", "v=ωr 관계로 속도 크기를 연결합니다.", "가속도까지 묻는다면 상대가속도 식을 따로 세웁니다."]
    return ["문제 단서를 다시 정리합니다."]
