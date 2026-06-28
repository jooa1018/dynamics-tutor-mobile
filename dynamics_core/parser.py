from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Pattern, Tuple

from .concepts import ALL_CUES, CUE_LABELS
from .models import Evidence, FeatureReport
from .semantic_normalizer import normalize_symbols, semantic_flags


def normalize_text(text: str) -> str:
    return normalize_symbols(text)


def _compile(patterns: Iterable[str]) -> List[Pattern[str]]:
    return [re.compile(p, flags=re.IGNORECASE) for p in patterns]


# 한국어 조사/어미를 허용하기 위한 공통 패턴. 예: 5 kg인, 3 m를, 10 N의, 30 rad/s로
JOSA = r"(?:\s*(?:인|의|짜리|를|을|로|으로|에서|까지|마다|이고|이며|이다|일 때|일때))?"
NUM = r"[-+]?\d+(?:\.\d+)?"

PATTERNS: Dict[str, List[Pattern[str]]] = {
    "time": _compile([rf"{NUM}\s*(?:초|s|sec|second)s?\b{JOSA}", r"비행\s*시간", r"\btime\b", r"시간\s*[tT]?", r"\bt\s*="]),
    "distance": _compile([rf"{NUM}\s*(?:m|미터)(?=$|\s|[가-힣]|[,.;:])(?!\s*/\s*s){JOSA}", r"거리", r"변위", r"이동\s*거리", r"수평\s*거리", r"\bs\s*=", r"\bx\s*="]),
    "constant_accel": _compile([r"등가속", r"가속도\s*일정", r"일정한\s*가속", r"uniform\s+acceleration"]),
    "projectile": _compile([r"포물선", r"투사", r"발사", r"던져", r"쏘아", r"projectile", r"launch"]),
    "incline": _compile([r"경사면", r"빗면", r"inclined?\s+plane", r"\bincline\b"]),
    "force": _compile([rf"{NUM}\s*N(?=$|\s|[가-힣]|[,.;:]){JOSA}", r"수직항력", r"외력", r"하중", r"\bforce\b", r"(?<![A-Za-z가-힣])힘(?![가-힣]*내|들|껏)"]),
    "mass": _compile([rf"{NUM}\s*kg(?=$|\s|[가-힣]|[,.;:]){JOSA}", r"질량", r"\bm_?\d*\s*=\s*[-+]?\d+(?:\.\d+)?\s*kg(?=$|\s|[가-힣]|[,.;:])", r"\bm\s*=\s*[-+]?\d+(?:\.\d+)?\s*kg(?=$|\s|[가-힣]|[,.;:])", r"mass"]),
    "tension": _compile([r"장력", r"도르래", r"로프", r"밧줄", r"(?<![가-힣])줄(?=$|\s|[이가은는을를의에과와로])", r"(?<![가-힣])끈(?=$|\s|[이가은는을를의에과와로])", r"\bpulley\b", r"\btension\b", r"\brope\b", r"\bstring\b", r"\bcord\b"]),
    "pulley_connected": _compile([r"도르래", r"연결된\s*물체", r"두\s*물체가\s*(?:줄|로프|끈)", r"줄로\s*연결", r"pulley", r"connected\s+blocks"]),
    "friction": _compile([r"마찰\s*(?:이\s*)?(?:있|있는|작용)", r"마찰계수", r"운동마찰", r"정지마찰", r"거친", r"거칠", r"\brough\b", r"\bfriction\b", r"μ", r"\bmu\b"]),
    "height": _compile([r"높이차", r"최고\s*높이", r"최저점", r"최고점", r"높이", r"고도", r"\bh\s*=", r"\bheight\b"]),
    # '탄성' 단독은 충돌의 종류일 수 있어 스프링 단서로 세지 않는다.
    "spring": _compile([r"스프링", r"용수철", r"탄성\s*(?:위치)?에너지", r"탄성력", r"복원력", r"\bspring\b", r"\bk\s*="]),
    "collision": _compile([r"충돌\s*(?:한다|했다|하였다|후|전후|직후|직전)", r"부딪", r"반발계수", r"완전\s*탄성\s*충돌", r"비탄성\s*충돌", r"탄성\s*충돌", r"\bcollision\b", r"\bcollide", r"\bimpact\b"]),
    "impulse": _compile([r"충격량", r"짧은\s*시간", r"타격", r"\bimpulse\b"]),
    "momentum": _compile([r"운동량", r"\bmomentum\b", r"linear\s+momentum"]),
    "angular_momentum": _compile([r"각운동량", r"moment\s+of\s+momentum", r"angular\s+momentum"]),
    "circular": _compile([r"원운동", r"원형\s*(?:트랙|고리|궤도|커브)", r"원궤도", r"곡률반지름", r"구심", r"수직\s*원", r"평평한\s*커브", r"\bloop\b", r"circular\s+path", r"radius\s+of\s+curvature"]),
    "normal_tangent": _compile([r"법선[-\s]*접선", r"접선\s*방향", r"법선\s*방향", r"n[-\s]*t\s*좌표", r"normal[-\s]*tangential"]),
    # r(t) 단독은 직교좌표 위치벡터일 수 있으므로 극좌표 단서로 세지 않는다.
    # 극좌표는 θ/theta/e_r/e_θ/polar 등 각도 방향 단서가 함께 있을 때 우선 판정한다.
    "polar": _compile([r"극좌표", r"polar\s+coordinate", r"r[-\s]*theta", r"r[-\s]*θ", r"e_r", r"e_θ", r"radial\s+transverse", r"theta\s*=", r"θ\s*=", r"theta\(t\)", r"θ\(t\)", r"r_dot", r"theta_dot", r"r의\s*시간함수.*(?:θ|theta|각도)", r"각도\s*θ.*시간"]),
    "rotation": _compile([r"회전", r"각속도", r"각가속도", r"\bomega\b", r"\balpha\b", r"ω", r"α"]),
    "translation_only": _compile([r"순수\s*병진", r"병진운동", r"translation\s+only", r"pure\s+translation"]),
    "rolling": _compile([r"굴러", r"구르", r"구른", r"굴림", r"구름", r"미끄러지지\s*않(?:고)?\s*(?:굴|구르|구른)", r"\brolling\b", r"rolls?\s+without\s+slipping"]),
    "sliding": _compile([r"미끄러진", r"미끄러져", r"미끄러지며", r"미끄러지면서", r"미끄럼\s*(?:이\s*)?(?:발생|있|생김)", r"활주", r"sliding", r"slides?", r"slip(?:s|ping)?"]),
    "torque": _compile([r"토크", r"모멘트", r"관성모멘트", r"\btorque\b", r"\bmoment\b", r"moment\s+of\s+inertia", r"\bI\s*="]),
    "fixed_axis": _compile([r"고정축", r"축이\s*고정", r"핀으로\s*고정", r"fixed\s+axis", r"pinned", r"힌지", r"핀\s*지지"]),
    "rigid_body": _compile([r"강체", r"막대", r"원판", r"원반", r"바퀴", r"원통", r"실린더", r"(?<![가-힣])공(?=$|\s|[이가은는을를의에과와로])", r"(?<![가-힣])구(?=$|\s|[이가은는을를의에과와로])", r"\bdisk\b", r"\bwheel\b", r"\bcylinder\b", r"\bsphere\b", r"\brod\b", r"\bbar\b"]),
    "relative_motion": _compile([r"상대속도", r"상대가속도", r"상대운동", r"기준\s*좌표계", r"moving\s+frame", r"relative\s+(?:velocity|acceleration|motion)"]),
    "instant_center": _compile([r"순간\s*중심", r"순간중심", r"instantaneous\s+center", r"center\s+of\s+zero\s+velocity"]),
    "variable_force": _compile([r"위치에\s*따라", r"변하는\s*힘", r"힘-변위", r"F\s*\(\s*x\s*\)", r"그래프"]),
    "air_resistance": _compile([r"공기\s*저항\s*(?:이|을|은|도)?\s*(?:고려|무시하지\s*않|있|작용|속도에\s*비례|속도의\s*제곱에\s*비례)", r"저항력\s*은?\s*(?:k|c)?v(?:\^2|²)?", r"속도에\s*비례하는\s*저항", r"속도의\s*제곱에\s*비례하는\s*저항", r"drag\s+force", r"air\s+resistance", r"damping\s+force", r"not\s+neglect\s+air\s+resistance"]),
    "nonconservative_work": _compile([r"비보존", r"손실", r"마찰\s*일", r"일\s*손실", r"nonconservative", r"energy\s+loss"]),
}

NEGATION: Dict[str, List[Pattern[str]]] = {
    "friction": _compile([r"마찰(?:계수\s*[^.。]*?)?\s*(?:을|은|이|력은|력은)?\s*(?:없는|없고|없이|없다면|무시(?!하지)|무시한다|무시할|고려하지\s*않|작용하지\s*않)", r"마찰력\s*은\s*작용하지\s*않", r"frictionless", r"no\s+friction", r"without\s+friction", r"neglect\s+friction", r"ignore\s+friction", r"friction\s+is\s+negligible", r"매끈한", r"매끄러운", r"매끄럽다고\s*가정", r"매끄럽", r"\bsmooth\b", r"smooth\s+(?:surface|table|plane)"]),
    "spring": _compile([r"스프링\s*(?:없는|없이)", r"용수철\s*(?:없는|없이)", r"no\s+spring"]),
    "air_resistance": _compile([r"공기\s*저항\s*(?:이|을)?\s*(?:없는|없음|없고|없이|무시(?!하지)|무시한다|무시할)", r"air\s+resistance\s*(?:is\s*)?(?:negligible|ignored)", r"neglect\s+air\s+resistance"]),
    "collision": _compile([r"충돌하지\s*않", r"아직\s*충돌하지", r"충돌하기\s*전(?!후)", r"충돌\s*(?:전|직전)(?!후)", r"before\s+collision", r"approaching\s+without\s+impact", r"without\s+collision", r"does\s+not\s+collide"]),
    "rotation": _compile([r"회전하지\s*않", r"회전\s*없이", r"각속도\s*는?\s*0", r"순수\s*병진", r"병진운동만", r"no\s+rotation", r"without\s+rotating", r"pure\s+translation"]),
}

IGNORED_FALSE_POSITIVES: List[Tuple[str, Pattern[str], str]] = [
    ("tension", re.compile(r"매끈한|매끄러운"), "'매끈한/매끄러운'은 끈이 아니라 마찰 없음 단서입니다."),
    ("rigid_body", re.compile(r"구하라|구한다|구하여|구하면|구할"), "'구하라/구할'은 풀이 지시어이지 구형 물체 단서가 아닙니다."),
    ("torque", re.compile(r"\bmomentum\b", flags=re.IGNORECASE), "'momentum'은 운동량이며 'moment'가 아닙니다."),
    ("impulse", re.compile(r"순간\s*중심|순간중심"), "'순간중심'은 충격량 문제가 아니라 강체 평면운동/상대속도 단서입니다."),
    ("spring", re.compile(r"탄성\s*충돌|비탄성\s*충돌|완전\s*비탄성|완전\s*탄성\s*충돌"), "'탄성 충돌'의 탄성은 스프링/용수철 단서가 아니라 충돌 종류입니다."),
]

GOAL_PATTERNS: List[Tuple[str, Pattern[str]]] = [
    ("충돌 후 속도", re.compile(r"충돌\s*후.*속도|속도.*충돌\s*후", re.IGNORECASE)),
    ("각속도/각가속도", re.compile(r"각속도|각가속도|angular\s+(?:velocity|acceleration)", re.IGNORECASE)),
    ("장력/마찰력", re.compile(r"장력|마찰력", re.IGNORECASE)),
    ("접촉 유지 조건", re.compile(r"접촉\s*유지|떨어지지|이탈하지|최소\s*높이|minimum\s+height", re.IGNORECASE)),
    ("가속도", re.compile(r"가속도|acceleration", re.IGNORECASE)),
    ("속도", re.compile(r"속도|속력|speed|velocity", re.IGNORECASE)),
    ("시간", re.compile(r"시간|time", re.IGNORECASE)),
    ("위치/변위", re.compile(r"변위|거리|위치|displacement|position", re.IGNORECASE)),
    ("토크", re.compile(r"토크|모멘트|torque|\bmoment\b", re.IGNORECASE)),
    ("힘", re.compile(r"힘|force|수직항력|하중", re.IGNORECASE)),
]


def _find_all(patterns: List[Pattern[str]], text: str) -> List[re.Match[str]]:
    matches: List[re.Match[str]] = []
    for p in patterns:
        matches.extend(list(p.finditer(text)))
    return matches


def infer_requested_quantity(text: str) -> Optional[str]:
    for label, pattern in GOAL_PATTERNS:
        if pattern.search(text):
            return label
    return None


def analyze_text(problem: str, solution: str = "") -> FeatureReport:
    raw_text = f"{problem}\n{solution}".strip()
    text = normalize_text(raw_text)
    sem = semantic_flags(text)
    cues: Dict[str, bool] = {key: False for key in ALL_CUES}
    negated: Dict[str, bool] = {}
    evidence: List[Evidence] = []
    ignored: List[str] = []
    warnings: List[str] = []

    for cue, patterns in NEGATION.items():
        matches = _find_all(patterns, text)
        if not matches:
            continue
        negated[cue] = True
        if cue == "friction":
            cues["no_friction"] = True
            cues["friction"] = False
            for m in matches[:4]:
                evidence.append(Evidence("no_friction", m.group(0), CUE_LABELS["no_friction"], m.start(), m.end()))
        elif cue == "air_resistance":
            cues["no_air_resistance"] = True
            cues["air_resistance"] = False
            for m in matches[:4]:
                evidence.append(Evidence("no_air_resistance", m.group(0), CUE_LABELS["no_air_resistance"], m.start(), m.end()))
        elif cue == "collision":
            cues["no_collision"] = True
            cues["collision"] = False
            for m in matches[:4]:
                evidence.append(Evidence("no_collision", m.group(0), CUE_LABELS["no_collision"], m.start(), m.end()))
        elif cue == "rotation":
            cues["no_rotation"] = True
            cues["rotation"] = False
            for m in matches[:4]:
                evidence.append(Evidence("no_rotation", m.group(0), CUE_LABELS["no_rotation"], m.start(), m.end()))
        elif cue in cues:
            cues[cue] = False

    for cue, patterns in PATTERNS.items():
        matches = _find_all(patterns, text)
        if not matches:
            continue
        if cue == "friction" and negated.get("friction"):
            for m in matches[:4]:
                ignored.append(f"'{m.group(0)}'은/는 마찰 무시/마찰 없음 문맥이 우선되어 마찰력 단서로 세지 않았습니다.")
            continue
        if cue == "air_resistance" and negated.get("air_resistance"):
            for m in matches[:4]:
                ignored.append(f"'{m.group(0)}'은/는 공기저항 무시 문맥이 우선되어 drag 단서로 세지 않았습니다.")
            continue
        if cue == "collision" and negated.get("collision"):
            for m in matches[:4]:
                ignored.append(f"'{m.group(0)}'은/는 충돌하지 않음/충돌 전 문맥이 우선되어 충돌 문제로 세지 않았습니다.")
            continue
        if cue in {"rotation", "torque"} and negated.get("rotation"):
            if cue == "rotation":
                for m in matches[:4]:
                    ignored.append(f"'{m.group(0)}'은/는 회전하지 않음 문맥이 우선되어 회전 단서로 세지 않았습니다.")
                continue
        if cue == "impulse" and re.search(r"순간\s*중심|순간중심", text):
            continue
        cues[cue] = True
        for m in matches[:4]:
            evidence.append(Evidence(cue, m.group(0), CUE_LABELS.get(cue, cue), m.start(), m.end()))


    # 공통 의미 정규화 계층: 테스트 문장 하드코딩이 아니라 물리 의미 동의어를 cue로 반영합니다.
    if sem.frictionless:
        cues["no_friction"] = True
        cues["friction"] = False
    elif sem.friction_present and not cues.get("no_friction"):
        cues["friction"] = True
    if sem.slip_present:
        cues["sliding"] = True
        cues["rolling"] = True if sem.rolling_word else cues.get("rolling", False)
        cues["rotation"] = True if sem.rotation_word or sem.rolling_word else cues.get("rotation", False)
        cues["rigid_body"] = True if sem.rotation_word or sem.rolling_word else cues.get("rigid_body", False)
        warnings.append("미끄럼이 있는 구름/회전 문제로 보이면 순수 구름 조건 v_G=ωR, a_G=αR을 적용식으로 쓰지 않습니다.")
    if sem.cartesian_position_vector:
        cues["polar"] = False
        warnings.append("r(t)가 i, j 성분 위치벡터로 주어졌으므로 직교좌표 미분을 우선합니다.")
    elif sem.polar_motion:
        cues["polar"] = True
    if sem.string_support:
        cues["tension"] = True
    if sem.bullet_rotating_body_collision:
        cues["collision"] = True
        cues["angular_momentum"] = True
        cues["rigid_body"] = True
        cues["rotation"] = True
        cues["fixed_axis"] = True

    # 문맥 보정
    if cues["instant_center"]:
        cues["relative_motion"] = True
        cues["rigid_body"] = True
        cues["rotation"] = True
        cues["impulse"] = False
        warnings.append("순간중심은 충격량 문제가 아니라 강체 평면운동에서 속도 관계를 잡는 단서입니다.")

    if cues["rolling"]:
        cues["rotation"] = True
        cues["rigid_body"] = True
        cues["no_rotation"] = False

    if cues["translation_only"] and cues["no_rotation"]:
        cues["rotation"] = False
        cues["rolling"] = False
        if not cues["fixed_axis"]:
            cues["torque"] = False
        warnings.append("'회전하지 않고 병진운동'은 강체 모양이 있어도 회전 방정식을 우선 쓰는 문제가 아닙니다.")

    body_radius = re.search(r"반지름\s*[A-Za-z가-힣0-9]*\s*인\s*(?:원판|원반|바퀴|원통|실린더|공|구)", text)
    path_radius = re.search(r"반지름\s*[A-Za-z가-힣0-9]*\s*인\s*원형\s*(?:트랙|고리|궤도|커브)", text)
    if body_radius and not path_radius:
        cues["rigid_body"] = True
        if cues["rolling"] or cues["torque"] or cues["fixed_axis"]:
            cues["rotation"] = True
        if not re.search(r"원운동|원형\s*(?:트랙|고리|궤도|커브)|곡률반지름|구심", text):
            cues["circular"] = False
            warnings.append("반지름이 원판/구 자체의 크기를 뜻하므로, 자동으로 원운동 문제로 보지 않았습니다.")

    if cues["projectile"]:
        cues["constant_accel"] = True
        if cues["air_resistance"]:
            warnings.append("공기저항을 고려하면 표준 포물선 공식(x등속, y등가속도)을 그대로 쓰면 위험합니다.")
        elif cues["no_air_resistance"]:
            warnings.append("공기저항을 무시한다는 조건 때문에 표준 포물선 운동 모델을 사용할 수 있습니다.")


    if cues["projectile"] and not (cues["rotation"] or cues["rolling"] or cues["torque"] or cues["fixed_axis"]):
        # 한국어 문제의 "공"은 투사체를 뜻할 때가 많으므로, 회전 단서가 없으면 강체로 보지 않는다.
        cues["rigid_body"] = False

    if cues["fixed_axis"]:
        cues["rotation"] = True
        cues["rigid_body"] = True
        cues["torque"] = True

    if cues["pulley_connected"]:
        cues["tension"] = True

    if cues["no_collision"]:
        cues["collision"] = False
        if cues["momentum"]:
            warnings.append("충돌하지 않았으므로 충돌 전후 방정식보다 현재 운동량 p=mv 또는 운동량 변화식을 먼저 확인하세요.")

    for cue, pattern, message in IGNORED_FALSE_POSITIVES:
        if pattern.search(text):
            ignored.append(message)

    if re.search(rf"{NUM}\s*m\b(?!\s*/\s*s){JOSA}", text, re.IGNORECASE) and not cues["mass"]:
        ignored.append("숫자 뒤의 m은 거리 단위로 처리했고, 질량 m으로 보지 않았습니다.")
    if re.search(r"\bm\s*=\s*[-+]?\d+(?:\.\d+)?\s*kg(?=$|\s|[가-힣]|[,.;:])", text, re.IGNORECASE):
        cues["mass"] = True
        ignored.append("m=5 kg 같은 표현은 질량으로 처리했습니다. 단위 m와 구분합니다.")

    if cues["spring"] and re.search(r"탄성\s*충돌|비탄성\s*충돌", text):
        # 같은 문제에 스프링 단어가 없고 충돌 탄성만 있는 경우 spring을 끈다.
        if not re.search(r"스프링|용수철|탄성\s*(?:위치)?에너지|복원력|\bspring\b|\bk\s*=", text, re.IGNORECASE):
            cues["spring"] = False

    if sum(cues.values()) <= 1 and text:
        warnings.append("문제 조건이 짧아 추천 신뢰도가 낮을 수 있습니다. 힘, 거리, 시간, 그림 조건을 더 넣으면 좋아요.")

    requested = infer_requested_quantity(problem)
    unique_evidence: List[Evidence] = []
    seen = set()
    for ev in evidence:
        key = (ev.cue, ev.text, ev.start, ev.end)
        if key not in seen:
            seen.add(key)
            unique_evidence.append(ev)

    return FeatureReport(
        cues=cues,
        negated=negated,
        evidence=unique_evidence,
        ignored_matches=list(dict.fromkeys(ignored)),
        requested_quantity=requested,
        warnings=list(dict.fromkeys(warnings)),
    )
