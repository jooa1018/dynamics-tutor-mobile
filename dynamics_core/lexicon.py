from __future__ import annotations

import re
from typing import Iterable

# Shared natural-language lexicon for beginner-facing mechanics classification.
# These patterns are intentionally broad as *cues*.  Final problem-type decisions
# must still use combinations of cues, not a single shared word such as rope/string.
ROPE_TERMS = [
    r"(?<![가-힣])줄(?=$|\s|[이가은는을를의에과와로끝])",
    r"(?<![가-힣])실(?=$|\s|[이가은는을를의에과와로끝])",
    r"(?<![가-힣])끈(?=$|\s|[이가은는을를의에과와로끝])",
    r"로프", r"밧줄", r"케이블", r"와이어",
    r"\bcord\b", r"\bstring(?=$|\s|[가-힣])", r"\brope(?=$|\s|[가-힣])", r"\bcable(?=$|\s|[가-힣])", r"\bwire(?=$|\s|[가-힣])",
]
REST_TERMS = [
    r"정지", r"가만히", r"움직이지\s*않", r"움직임이\s*없", r"멈춰\s*있", r"멈춘", r"평형", r"정적\s*평형",
    r"가속도\s*0", r"가속도가\s*없", r"속도\s*변화\s*없", r"속도가\s*일정",
    r"\bstationary\b", r"\bat\s+rest\b", r"\bequilibrium\b", r"static\s+equilibrium",
    r"있음",  # only used in combination with other rest cues such as 가만히 있음
]
PENDULUM_TERMS = [
    r"단진자", r"진자", r"흔들린", r"흔들림", r"흔들리", r"진동", r"왕복\s*운동", r"작은\s*각도", r"작은\s*각", r"작은\s*진폭", r"소진동", r"살짝\s*흔들림", r"살짝\s*흔들린",
    r"\bpendulum\b", r"small\s+angle", r"small\s+oscillation", r"small\s+amplitude", r"oscillat",
]
HANGING_TERMS = [
    r"매달린", r"매달려", r"매달", r"매단", r"달린", r"달려", r"걸린", r"걸려\s*있는", r"천장에\s*연결된", r"(?:줄|실|끈|로프)\s*끝에\s*달린", r"끝에\s*달린", r"연결된\s*(?:물체|추)",
    r"\bhanging\b", r"\bsuspended\b", r"hangs?",
]
CONICAL_TERMS = [
    r"원뿔\s*진자", r"원뿔\s*모양", r"원뿔면", r"수평\s*원운동", r"수평\s*원을", r"수직선과\s*(?:각도|θ|theta)", r"연직선과\s*(?:각도|θ|theta)", r"수직선과[^.。]{0,20}각도", r"연직선과[^.。]{0,20}각도", r"수직선과[^.。]{0,20}θ", r"연직선과[^.。]{0,20}θ", r"원을\s*그리며\s*(?:돈|돎|도는|돌|회전)", r"반지름\s*r의\s*원운동", r"각속도\s*(?:ω|omega)",
    r"conical\s+pendulum", r"horizontal\s+circular\s+motion", r"horizontal\s+circle", r"moves?\s+in\s+a\s+circle",
]
PERIOD_QUERY_TERMS = [r"주기", r"period", r"T_period"]
TENSION_QUERY_TERMS = [r"장력", r"tension"]
ANGULAR_SPEED_QUERY_TERMS = [r"각속도", r"angular\s+speed", r"omega", r"ω"]
PULLEY_STRUCTURE_TERMS = [
    r"도르래", r"\bpulley\b", r"움직도르래", r"고정도르래",
    r"(?:줄|실|끈|로프|케이블|와이어)(?:로|으로)\s*연결",
    r"connected\s+(?:to|by|over).*pulley", r"over\s+a\s+pulley",
    r"블록\s*A.*블록\s*B", r"block\s*A.*block\s*B", r"두\s*(?:물체|블록|질량)",
]


def has_any(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(p, text, flags=re.I) for p in patterns)


def normalize_colloquial(text: str) -> str:
    """Lightweight Korean colloquial normalization for short student inputs."""
    out = text
    replacements = {
        "돎": "돈다",
        "흔들림": "흔들린다",
        "살짝 흔들림": "작은 진폭으로 흔들린다",
        "가만히 있음": "가만히 있다",
        "장력?": "장력을 구하라",
        "주기?": "주기를 구하라",
        "각속도?": "각속도를 구하라",
    }
    for a, b in replacements.items():
        out = out.replace(a, b)
    return out


def has_rope(text: str) -> bool:
    return has_any(text, ROPE_TERMS)


def has_rest(text: str) -> bool:
    return has_any(text, REST_TERMS)


def has_hanging(text: str) -> bool:
    return has_any(text, HANGING_TERMS)


def has_pendulum(text: str) -> bool:
    return has_any(text, PENDULUM_TERMS)


def has_conical(text: str) -> bool:
    return has_any(text, CONICAL_TERMS)


def has_pulley_structure(text: str) -> bool:
    return has_any(text, PULLEY_STRUCTURE_TERMS)


def is_single_string_equilibrium(text: str) -> bool:
    t = normalize_colloquial(text)
    return has_rope(t) and has_hanging(t) and has_rest(t) and has_any(t, TENSION_QUERY_TERMS) and not has_pulley_structure(t)


def is_simple_pendulum(text: str) -> bool:
    t = normalize_colloquial(text)
    has_length = bool(re.search(r"길이\s*L|length\s*L|\bL\b", t, flags=re.I))
    return has_rope(t) and (has_length or has_hanging(t)) and has_pendulum(t) and has_any(t, PERIOD_QUERY_TERMS) and not has_pulley_structure(t)



def is_conical_candidate_unclear(text: str) -> bool:
    t = normalize_colloquial(text)
    uncertain = bool(re.search(r"확인|여부|명확하지|정보가\s*(?:없|부족)|not\s+stated|need\s+to\s+confirm", t, flags=re.I))
    circle_or_angle = bool(re.search(r"원운동|원을\s*그리|원을\s*돈|회전|수평\s*원|horizontal|circle|vertical\s+angle|줄\s*각도|각도", t, flags=re.I))
    return has_rope(t) and (has_hanging(t) or circle_or_angle) and circle_or_angle and uncertain and not has_pulley_structure(t)

def is_conical_pendulum(text: str) -> bool:
    t = normalize_colloquial(text)
    if re.search(r"확인|여부|명확하지|정보가\s*(?:없|부족)|not\s+stated|need\s+to\s+confirm", t, flags=re.I):
        return False
    strong = sum([
        bool(has_rope(t) or has_hanging(t)),
        bool(re.search(r"수평\s*원운동|원을\s*그리며\s*(?:돈|돎|도는|돌)|horizontal\s+(?:circular|circle)|moves?\s+in\s+a\s+circle", t, flags=re.I)),
        bool(re.search(r"(?:수직선|연직선|vertical)[^.。]{0,30}(?:각도|θ|theta)|(?:각도|θ|theta)[^.。]{0,30}(?:수직선|연직선|vertical)|기울어진\s*채|비스듬한", t, flags=re.I)),
        bool(re.search(r"원뿔\s*진자|conical\s+pendulum|원뿔\s*모양|원뿔면", t, flags=re.I)),
    ])
    return strong >= 2 and has_any(t, ANGULAR_SPEED_QUERY_TERMS + [r"원운동", r"circle", r"돈다", r"돎"]) and not has_pulley_structure(t)
