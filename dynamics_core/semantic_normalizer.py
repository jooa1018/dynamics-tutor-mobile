from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, Pattern

from . import lexicon


def _rx(pattern: str) -> Pattern[str]:
    return re.compile(pattern, flags=re.IGNORECASE)


@dataclass(frozen=True)
class SemanticFlags:
    frictionless: bool = False
    friction_present: bool = False
    slip_present: bool = False
    explicit_pure_rolling: bool = False
    rotation_word: bool = False
    rolling_word: bool = False
    string_support: bool = False
    track_support: bool = False
    bottom_position: bool = False
    top_position: bool = False
    banked_curve: bool = False
    flat_curve: bool = False
    max_speed: bool = False
    min_speed: bool = False
    conical_explicit: bool = False
    conical_structural: bool = False
    conical_candidate: bool = False
    cartesian_position_vector: bool = False
    polar_motion: bool = False
    bullet_rotating_body_collision: bool = False
    horizontal_table: bool = False
    hanging_mass: bool = False
    pulley: bool = False


def normalize_symbols(text: str) -> str:
    """Normalize common mechanics notation without changing the user's words too much."""
    out = text
    replacements = {
        "−": "-", "–": "-", "—": "-",
        "㎏": "kg", "ｍ": "m", "㎧": "m/s",
        "\u2061": "",  # function application invisible char
    }
    for a, b in replacements.items():
        out = out.replace(a, b)
    # Make LaTeX-like unit vectors searchable while preserving original forms too.
    out = re.sub(r"\\hat\s*\{\s*i\s*\}", " i_hat ", out, flags=re.IGNORECASE)
    out = re.sub(r"\\hat\s*\{\s*j\s*\}", " j_hat ", out, flags=re.IGNORECASE)
    out = re.sub(r"i\s*[- ]?hat", " i_hat ", out, flags=re.IGNORECASE)
    out = re.sub(r"j\s*[- ]?hat", " j_hat ", out, flags=re.IGNORECASE)
    out = re.sub(r"\bequals\b", "=", out, flags=re.IGNORECASE)
    out = re.sub(r"\bplus\b", "+", out, flags=re.IGNORECASE)
    out = re.sub(r"\bminus\b", "-", out, flags=re.IGNORECASE)
    out = out.replace("’", "'").replace("‘", "'").replace("r⃗", "r")
    out = re.sub(r"\\vec\s*\{\s*r\s*\}", "r", out, flags=re.IGNORECASE)
    # Normalize compact r(t)=...\hat{i}+...\hat{j} after replacing hats.
    return re.sub(r"\s+", " ", out.strip())


def has(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def has_any(text: str, patterns: Iterable[str]) -> bool:
    return any(has(text, pattern) for pattern in patterns)


FRICTIONLESS = [
    r"마찰(?:계수\s*[^.。]*?)?\s*(?:을|은|이|력은|력은)?\s*(?:없는|없음|없다|없이|없고|무시(?!하지)|무시한다|무시할|무시\s*가능|고려하지\s*않)",
    r"마찰력\s*은?\s*작용하지\s*않",
    r"매끈한|매끄러운|매끄럽다고\s*가정|매끄럽",
    r"\bsmooth(?=\b|[가-힣])|smooth\s+(?:surface|table|plane|incline|floor)",
    r"frictionless|friction[-\s]?free|no\s+friction|without\s+friction|neglect\s+friction|ignore\s+friction|friction\s+is\s+negligible|negligible\s+friction|friction\s+(?:is\s+|may\s+be\s+|can\s+be\s+)?(?:neglected|ignored)|polished\s+(?:\w+\s+){0,3}(?:table|surface|plane)",
]
FRICTION_PRESENT = [r"마찰\s*(?:이\s*)?(?:있|있는|작용)", r"friction\s*(?:이|이\s*있|있|present|acts)", r"마찰계수|운동마찰|정지마찰|거친|rough|\bfriction\b|μ|\bmu\b"]

SLIP_PRESENT = [
    r"미끄러진|미끄러져|미끄러지며|미끄러지면서|미끄럼\s*(?:이\s*)?(?:발생|있|생김)|미끄럼을\s*(?:동반|가지고)|미끄러짐을\s*동반|회전하면서\s*미끄러|구르면서\s*미끄러|미끄러지며\s*(?:회전|구름|돈|돌)",
    r"구르(?:지만|나)\s*미끄러|굴러(?:가지만| 내려가지만)?\s*미끄럼|굴러가지만\s*미끄러|구르면서\s*미끄러",
    r"rolling\s+(?:while|and)\s+slipping|rolls?\s+and\s+slips?|rolls?\s+while\s+slipping|slips?\s+while\s+rolling|rotating\s+while\s+slipping|rolling\s+with\s+slip(?:ping)?|with\s+slip(?:ping)?|skidding\s+while\s+rolling",
    r"(?<!no\s)(?<!without\s)slip\s+occurs|there\s+is\s+slip\s+at|contact\s+point\s+has\s+slip|slip\s+exists\s+at|slipping\s+exists\s+at\s+(?:the\s+)?(?:contact|point\s+of\s+contact)|slip(?:이|\s+is)?\s*(?:발생|있)|slips?\s+at\s+(?:the\s+)?point\s+of\s+contact|point\s+of\s+contact\s+slips?|contact\s+point\s+(?:is\s+)?slipping|contact\s+point\s+has\s+slip|contact\s+point\s+slips?|slip\s+exists\s+at\s+(?:the\s+)?(?:contact|point\s+of\s+contact)|slipping\s+exists\s+at\s+(?:the\s+)?(?:contact|point\s+of\s+contact)|slipping\s+at\s+(?:the\s+)?(?:contact|contact\s+point)",
    r"there\s+is\s+slipping\s+at\s+(?:the\s+)?(?:point\s+of\s+contact|contact\s+point)|slipping\s+exists\s+at\s+(?:the\s+)?(?:point\s+of\s+contact|contact\s+point|contact\s+patch)|slip\s+exists\s+at\s+(?:the\s+)?(?:point\s+of\s+contact|contact\s+point|contact\s+patch)|(?:rolling\s+)?(?:disk|wheel|cylinder)\s+has\s+slip(?:ping)?\s+at\s+(?:the\s+)?(?:point\s+of\s+contact|contact\s+point|contact\s+patch)|the\s+rolling\s+(?:disk|wheel|cylinder)\s+has\s+slip\s+at|contact\s+patch\s+has\s+slip(?:ping)?|point[-\s]of[-\s]contact\s+slip\s+exists\s+while\s+rolling",
    r"not\s+pure\s+rolling|순수\s*구름(?:은|이)?\s*아니|rolls?\s+but\s+skids?|rolls?\s+but\s+slips?|skids?|스키딩(?:하며|하면서)|스키딩\s*(?:발생|있)|slip\s+and\s+rotate|slip(?:하며|하면서)|slipping(?:하며|하면서)|skid(?:하며|하면서)",
    r"slides?\s+while\s+(?:rotating|spinning)|sliding\s+(?:while|and)\s+(?:rotating|spinning)|slips?\s+(?:as|while)\s+it\s+(?:rotates|spins|rolls?)|slips?\s+as\s+(?:it\s+)?rolls?",
]
PURE_ROLLING = [
    r"미끄러지지\s*않(?:고)?\s*(?:굴|구르|구른|회전|돈|돌|이동|내려)",
    r"미끄러지지\s*않",
    r"미끄럼\s*없이\s*(?:굴|구르|구른|회전|이동|내려)",
    r"미끄러짐\s*없이\s*(?:굴|구르|구른|회전|이동|내려)",
    r"접촉점에서\s*미끄러지지\s*않|접촉점에서\s*미끄럼\s*(?:이\s*)?없",
    r"pure\s+rolling",
    r"rolling\s+without\s+(?:any\s+)?slipping|rolling\s+without\s+(?:any\s+)?slip",
    r"rolls?\s+without\s+(?:any\s+)?slipping|rolls?\s+without\s+(?:any\s+)?slip",
    r"without\s+(?:any\s+)?slipping|without\s+(?:any\s+)?slip|without\s+(?:any\s+)?skidding|without\s+(?:any\s+)?skid",
    r"no\s+(?:any\s+)?slip(?:ping)?(?:\s+occurs?)?|no\s+(?:any\s+)?skid(?:ding)?(?:\s+occurs?)?|slip(?:ping)?\s+does\s+not\s+occur|skid(?:ding)?\s+does\s+not\s+occur|does\s+not\s+(?:slip|skid)",
    r"not\s+slipping\s+as\s+it\s+rolls?|rolling\s+but\s+not\s+slipping|rolls?\s+but\s+not\s+slipping|not\s+skidding\s+as\s+it\s+rolls?",
    r"no\s+slip(?:ping)?\s+at\s+(?:the\s+)?(?:point\s+of\s+contact|contact\s+point)|no\s+skid(?:ding)?\s+at\s+(?:the\s+)?(?:point\s+of\s+contact|contact\s+point)",
    r"no\s+slip(?:ping)?\s+exists\s+at\s+(?:the\s+)?(?:point\s+of\s+contact|contact\s+point|contact\s+patch)|there\s+is\s+no\s+slip(?:ping)?\s+at\s+(?:the\s+)?(?:point\s+of\s+contact|contact\s+point|contact\s+patch)|no\s+point[-\s]of[-\s]contact\s+slip|(?:disk|wheel|cylinder)\s+has\s+no\s+point[-\s]of[-\s]contact\s+slip|contact\s+(?:point|patch)\s+has\s+no\s+slip",
]
ROTATION_WORD = [r"회전|돈다|돌아간다|도는|각속도|spins?|rotates?|rotation|omega|ω"]
ROLLING_WORD = [r"굴러|구르|구른|구름|rolling|rolls?"]

STRING_SUPPORT = lexicon.ROPE_TERMS
TRACK_SUPPORT = [r"트랙|레일|원형\s*궤도|원형\s*고리|track|rail|loop"]
BOTTOM = [r"최저점|최하점|하단|바닥점|제일\s*아래|제일\s*낮은\s*점|가장\s*아래점|가장\s*아래|맨\s*아래|아래쪽\s*지점|가장\s*낮은\s*(?:점|위치)|아래\s*위치|bottom(?:\s+position)?|bottom\s*point|bottommost\s+point|at\s+the\s+bottom|lowest(?:\s+(?:point|position))?|lower\s+most\s+point|lowermost\s+point|lower\s+point|at\s+the\s+lower\s+end\s+of\s+the\s+vertical\s+circle|아래쪽"]
TOP = [r"최고점|가장\s*위점|가장\s*위|맨\s*위|위쪽\s*지점|가장\s*높은\s*(?:점|위치)|top(?:\s+position)?|at\s+the\s+top|highest\s+point|꼭대기"]

BANKED_CURVE = [r"경사진\s*(?:커브|곡선\s*도로|곡선도로|도로\s*커브|도로)|경사\s*(?:커브|곡선\s*도로|도로(?:\s*커브)?|도로)|뱅크\s*(?:커브|도로)|banked\s+(?:curve|road|roadway|turn)|bank\s*(?:curve|road|roadway|turn)|inclined\s+(?:curve|road\s+curve|roadway\s+curve|turn)|sloped\s+(?:curve|road\s+curve|roadway\s+curve|turn)|slanted\s+(?:curve|road\s+curve|roadway\s+curve|turn)|canted\s+(?:curve|road|roadway|turn)|road(?:way)?\s+curve\s+with\s+(?:static\s+)?friction|road\s+curve\s+with\s+bank(?:\s+angle)?|curve\s+on\s+an\s+inclined\s+roadway|curve\s+with\s+bank(?:\s+angle)?|sliding\s+(?:up|down|outward|inward)\s+(?:the\s+)?bank|vehicle\s+on\s+a\s+(?:sloped|banked|inclined|canted)\s+turn|car\s+on\s+a\s+banked\s+turn|기울어진\s*도로|경사각.*커브|커브.*경사각|커브가\s*경사져|커브.*경사져|경사져\s*있고.*커브|커브가\s*경사져|커브.*경사져|경사져\s*있고.*커브"]
FLAT_CURVE = [r"평평한\s*(?:커브|원형\s*도로|도로.*커브)|수평\s*(?:커브|원형\s*도로)|flat\s+curve|level\s+curve|평평한\s*도로.*커브"]
MAX_SPEED = [r"최고\s*(?:속도|속력)|가장\s*큰\s*(?:속도|속력)|최대\s*(?:속도|속력)|최대(?:속도|속력)|허용\s*(?:가능한\s*)?최대\s*(?:속도|속력)|최대\s*허용\s*(?:속도|속력)|미끄러지지\s*않고.*최대\s*(?:속도|속력)|maximum\s+(?:safe\s+|allowable\s+|permissible\s+|allowed\s+)?(?:speed|velocity)|highest\s+(?:speed|velocity)|fastest\s+(?:speed|velocity)|greatest\s+(?:speed|velocity)|max\s+speed|upper\s+(?:(?:speed|velocity)\s+)?limit|upper\s+limit\s+of\s+speed|speed\s+upper\s+limit|허용\s*최대\s*(?:속도|속력)|최대\s*허용\s*(?:속도|속력)|maximum\s+(?:speed|velocity)\s+before\s+(?:slipping|sliding)\s+outward|highest\s+speed\s+before\s+sliding\s+(?:up|outward)\s+(?:the\s+)?bank|바깥쪽으로\s*미끄러지기\s*직전|위쪽으로\s*미끄러지기\s*직전"]
MIN_SPEED = [r"최저\s*(?:속도|속력)|가장\s*작은\s*(?:속도|속력)|최소\s*(?:속도|속력)|최소(?:속도|속력)|최저\s*허용\s*(?:속도|속력)|최소\s*허용\s*(?:속도|속력)|허용\s*최소\s*(?:속도|속력)|아래로\s*미끄러지지\s*않는\s*최소\s*(?:속도|속력)|minimum\s+(?:permissible\s+|allowed\s+)?(?:speed|velocity)|lowest\s+(?:speed|velocity)|slowest\s+(?:speed|velocity)|lower\s+(?:permissible\s+|allowed\s+)?(?:speed|velocity)|lower\s+speed\s+limit|min\s+speed|minimum\s+(?:speed|velocity)\s+before\s+(?:slipping|sliding)\s+down|before\s+sliding\s+down|안쪽으로\s*미끄러지기\s*직전|아래쪽으로\s*미끄러지기\s*직전|아래로\s*미끄러지지\s*않는\s*최소\s*speed"]

CONICAL_EXPLICIT = [r"원뿔\s*진자|conical\s+pendulum|conical\s+(?:motion|movement)|conical\s+(?:path|trajectory)|cone[-\s]shaped\s+(?:path|trajectory)|moves?\s+along\s+a\s+conical\s+trajectory|follows?\s+a\s+conical\s+trajectory|traces?\s+(?:a\s+)?(?:conical\s+path|cone|conical\s+trajectory)|sweeps?\s+out\s+a\s+cone|describes?\s+(?:a\s+)?(?:cone|conical\s+(?:motion|path))|moves?\s+in\s+a\s+(?:conical|cone[-\s]shaped)\s+path|follows?\s+a\s+cone[-\s]shaped\s+trajectory|forms?\s+a\s+cone|string\s+forms?\s+a\s+cone|(?:bob|mass)\s+sweeps?\s+out\s+a\s+cone|moves?\s+like\s+a\s+cone|(?:bob|mass|stone).*moves?\s+like\s+a\s+cone|원뿔\s*(?:운동|형\s*운동|모양\s*운동|꼴\s*운동)|원뿔\s*(?:모양|형태|꼴)(?:으?로)?\s*(?:회전|돈|도는|돌|움직)|원뿔\s*(?:경로|궤적|형태의\s*경로|모양\s*궤적)|원뿔\s*궤적을\s*그린|원뿔면을\s*만들"]
HANGING_OBJECT = lexicon.HANGING_TERMS + [r"mass|bob|stone|pendulum|attached|tied"]
HORIZONTAL_CIRCLE = [r"수평\s*원운동|수평\s*원을\s*그린|수평\s*원을\s*그리|수평면에서\s*원|수평면에서\s*원을\s*그리|테이블과\s*평행한\s*원\s*궤도|수평\s*원\s*궤도|원을\s*그리며\s*(?:회전|돈|돎|도는|돌)|원\s*궤적|원형\s*경로|수평\s*원궤도|circular\s+motion|horizontal\s+(?:circular|circle)|moves?\s+in\s+a\s+horizontal\s+circle|revolves?\s+in\s+a\s+circle|(?:bob|mass|stone)\s+(?:revolves|moves)\s+in\s+a\s+circle|moves?\s+in\s+a\s+circle"]
VERTICAL_ANGLE = [r"연직선|수직선|수직과|수직\s*방향|기울어진\s*채|비스듬한\s*상태|vertical|with\s+vertical|angle\s+with\s+(?:the\s+)?vertical|makes?\s+[^.]{0,30}\s+with\s+(?:the\s+)?vertical|making\s+[^.]{0,30}\s+with\s+(?:the\s+)?vertical|inclined\s+from\s+vertical|각도\s*θ|θ를\s*이룬|theta|θ"]

CARTESIAN_VECTOR = [

    r"particle(?:'s)?\s+position\s+(?:(?:is\s+)?equal\s+to|equals|is)\s*\([^)]*,[^)]*\)",
    r"particle\s+position\s*=\s*\([^)]*,[^)]*\)",
    r"position\s+(?:(?:is\s+)?equal\s+to|equals|is)\s*\([^)]*,[^)]*\)",
    r"position\s*=\s*\([^)]*,[^)]*\)",
    r"coordinates\s+(?:are|equal)\s*\([^)]*,[^)]*\)",
    r"(?:particle\s+)?coords\s*(?:are|=|equal|equals)\s*(?:<[^>]+>|\([^)]*,[^)]*\))",
    r"(?:the\s+)?coordinates\s+of\s+(?:the\s+)?particle\s+(?:are|=|equal|equals)\s*(?:<[^>]+>|\([^)]*,[^)]*\))",
    r"particle(?:'s)?\s+coordinates\s+(?:are|=|equal|equals)\s*(?:<[^>]+>|\([^)]*,[^)]*\))",
    r"(?:위치|좌표)가\s*\([^)]*,[^)]*\)",
    r"r\s+vector\s*=\s*[^.。;\n]*(?:i_hat|î|i\b)\s*(?:\+|-)\s*[^.。;\n]*(?:j_hat|ĵ|j\b)",
    r"particle\s+has\s+position\s*\([^)]*,[^)]*\)",
    r"position\s+is\s*\([^)]*,[^)]*\)",
    r"r\s*vector\s*=\s*[^.。;\n]*(?:i_hat|î|i\b|\\hat\s*\{\s*i\s*\})\s*(?:\+|-)\s*[^.。;\n]*(?:j_hat|ĵ|j\b|\\hat\s*\{\s*j\s*\})",
    r"vector\s+r\s*=\s*[^.。;\n]*(?:i_hat|î|i\b)\s*(?:\+|-)\s*[^.。;\n]*(?:j_hat|ĵ|j\b)",
    r"(?:position|coords|coordinates|coordinate\s+vector|position\s+coordinates|particle(?:'s)?\s+(?:coords|coordinates))\s+(?:is|are|equal|equals|=|vector\s*=)\s*<[^>]+>",
    r"r\s*=\s*<[^>]+>",
    r"r\s*=\s*\([^)]*,[^)]*\)",
    r"입자\s*위치가\s*r\s*=\s*\([^)]*,[^)]*\)",
    r"r\s*=\s*[^.。;\n]*(?:i_hat|î|i\b|\\hat\s*\{\s*i\s*\})\s*(?:\+|-)\s*[^.。;\n]*(?:j_hat|ĵ|j\b|\\hat\s*\{\s*j\s*\})",
    r"위치\s*벡터|위치벡터|position\s+vector|위치가\s*벡터로",
    r"r\s*\(\s*t\s*\)\s*=\s*[^.。;\n]*(?:i_hat|î|i\b|\\hat\s*\{\s*i\s*\})\s*(?:\+|-)\s*[^.。;\n]*(?:j_hat|ĵ|j\b|\\hat\s*\{\s*j\s*\})",
    r"unit\s+vector\s+i\s+and\s+j|i\s*,\s*j\s*성분|i\s+and\s+j\s+components",
    r"r(?:vec|⃗)?\s*\(\s*t\s*\)\s*=\s*<[^>]+>",
    r"<\s*[^,>]+\s*,\s*[^>]+>\s*(?:이다|로\s*주어진|position|vector|v와|속도)",
]
POLAR = [r"극좌표|polar|e_r|e_θ|e_theta|radial\s*/?\s*transverse|radial\s+transverse|r\s*,\s*(?:θ|theta)|r[-\s]*(?:θ|theta)|r\s*\(\s*t\s*\).*?(?:θ|theta)\s*\(\s*t\s*\)|(?:θ|theta)\s*\(\s*t\s*\).*?r\s*\(\s*t\s*\)|r\s*=.*?(?:θ|theta)\s*="]

BULLET = [r"탄환|총알|투사체|bullet|projectile"]
EMBEDDED = [r"박힌|박힌다|박혀서|박힌\s*후|박힌\s*뒤|박히고|박힘|붙는다|붙어|꽂힌|꽂힌다|꽂힌\s*뒤|가장자리에\s*(?:박|꽂)|rim에\s*박|embedded|lodged|lodges?\s+in|sticks?(?:\s+(?:into|in|to))?|embeds?\s+in|becomes?\s+embedded|remains?\s+in|hits?\s+and\s+(?:sticks|remains|lodges)|strikes?\s+[^.;]{0,40}\s+and\s+sticks"]
ROTATING_BODY = [r"막대|rod|bar|hinged\s+(?:rod|bar)|pivoted\s+(?:rod|bar)|(?:rod|bar)\s+pivoted|(?:rod|bar)\s+pinned\s+at\s+one\s+end|hinged\s+bar|pivoted\s+bar|원판|원반|바퀴|회전판|진자막대|고정축\s*강체|회전강체|disk|wheel|rotating\s+body"]
AXIS_ROTATION = [r"핀|회전축|고정축|축\s*주위|고정축을\s*중심|주위로\s*(?:회전|돈)|함께\s*돈|각속도|pinned|pivoted|hinged|pivoted\s+at\s+one\s+end|fixed\s+pivot|fixed\s+hinge|힌지|피벗|피벗된|힌지된|한쪽\s*끝(?:이)?\s*(?:고정|피벗|힌지)|fixed\s+axis|fixed\s+axle|about\s+(?:a|the)?\s*(?:fixed\s+)?(?:axis|axle|pivot)|angular\s+velocity\s+(?:just|immediately)?\s*after\s+(?:collision|impact)"]

HORIZONTAL_TABLE = [r"수평면|수평\s*테이블|테이블|탁자|table|surface|plane|horizontal\s+(?:table|surface|plane)|smooth\s+horizontal\s+plane|level\s+(?:surface|plane)"]
HANGING = lexicon.HANGING_TERMS + [r"hanging\s+(?:block|mass|B)|hanging\s+B|추"]
PULLEY = lexicon.PULLEY_STRUCTURE_TERMS + [r"연결\s*문제", r"블록.*매달린|매달린.*블록|connected\s+to.*hanging|tied\s+to\s+hanging|tied.*hanging|connected.*hanging|tied\s+to\s+hanging\s+(?:block|mass)|블록.*매달린\s*추"]


def semantic_flags(text: str) -> SemanticFlags:
    t = normalize_symbols(lexicon.normalize_colloquial(text))
    frictionless = has_any(t, FRICTIONLESS)
    friction_present = (not frictionless) and has_any(t, FRICTION_PRESENT)
    pure_signal = has_any(t, PURE_ROLLING)
    raw_slip = has_any(t, SLIP_PRESENT)
    # Important priority: negated slip/skid phrases must dominate the bare token
    # "slip/skid". This makes the ontology rule executable: no slip/skid at the
    # contact point means pure rolling, while positive contact slip means sliding
    # rotation. Banked-curve sliding is handled separately by banked_curve flags.
    negated_slip = has_any(t, [
        r"without\s+(?:any\s+)?(?:slip|slipping|skid|skidding)",
        r"no\s+(?:slip|slipping|skid|skidding)(?:\s+occurs?)?",
        r"no\s+(?:point[-\s]of[-\s]contact\s+)?slip(?:ping)?(?:\s+(?:exists|occurs?))?(?:\s+at\s+(?:the\s+)?(?:point\s+of\s+contact|contact\s+point|contact\s+patch))?",
        r"there\s+is\s+no\s+slip(?:ping)?\s+at\s+(?:the\s+)?(?:point\s+of\s+contact|contact\s+point|contact\s+patch)",
        r"(?:disk|wheel|cylinder)\s+has\s+no\s+point[-\s]of[-\s]contact\s+slip(?:ping)?",
        r"contact\s+(?:point|patch)\s+has\s+no\s+slip(?:ping)?",
        r"(?:slip|slipping|skid|skidding)\s+does\s+not\s+occur",
        r"does\s+not\s+(?:slip|skid)",
        r"not\s+(?:slipping|skidding)\s+as\s+it\s+rolls?",
        r"rolling\s+but\s+not\s+(?:slipping|skidding)",
        r"rolls?\s+but\s+not\s+(?:slipping|skidding)",
        r"(?:slip|slipping|skid|skidding)\s*없이|스키딩\s*없이|미끄럼\s*없이|미끄러지지\s*않|접촉점에서\s*미끄러지지\s*않",
    ])
    positive_slip = has_any(t, [
        r"with\s+slipping", r"with\s+slip", r"rolling\s+(?:while|and)\s+slipping", r"rolls?\s+and\s+slips?", r"rolls?\s+while\s+slipping", r"slips?\s+while\s+rolling", r"rotating\s+while\s+slipping", r"rolling\s+with\s+slip", r"rolls?\s+but\s+skids?", r"rolls?\s+but\s+slips?",
        r"there\s+is\s+slip\s+at|contact\s+point\s+has\s+slip|slip\s+exists\s+at|slipping\s+exists\s+at", r"contact\s+point\s+(?:is\s+)?slipping", r"contact\s+point\s+slips?", r"point\s+of\s+contact\s+slips?", r"slips?\s+at\s+(?:the\s+)?point\s+of\s+contact", r"slipping\s+at\s+(?:the\s+)?(?:contact|contact\s+point)",
        r"skidding\s+while\s+rolling|skidding\s+while|스키딩(?:하며|하면서)", r"not\s+pure\s+rolling", r"slips?\s+(?:as|while)(?:\s+it)?\s+(?:rolls?|rotates?|spins?)", r"slides?\s+while",
        r"미끄럼\s*(?:이\s*)?(?:발생|있|생김)", r"미끄러지며|미끄러지면서|구르지만\s*미끄러|구르면서\s*미끄러",
        r"접촉점에서\s*미끄러(?!지지)",
    ])
    if negated_slip and has_any(t, [
        r"no\s+(?:point[-\s]of[-\s]contact\s+)?slip(?:ping)?(?:\s+(?:exists|occurs?))?(?:\s+at\s+(?:the\s+)?(?:point\s+of\s+contact|contact\s+point|contact\s+patch))?",
        r"there\s+is\s+no\s+slip(?:ping)?\s+at\s+(?:the\s+)?(?:point\s+of\s+contact|contact\s+point|contact\s+patch)",
        r"(?:disk|wheel|cylinder)\s+has\s+no\s+point[-\s]of[-\s]contact\s+slip(?:ping)?",
        r"contact\s+(?:point|patch)\s+has\s+no\s+slip(?:ping)?",
    ]):
        positive_slip = False
    slip_present = raw_slip
    if negated_slip and not positive_slip:
        slip_present = False
    elif pure_signal and not positive_slip:
        slip_present = False
    explicit_pure = (pure_signal or negated_slip) and not slip_present
    string_support = has_any(t, STRING_SUPPORT)
    horiz_circle = has_any(t, HORIZONTAL_CIRCLE)
    vertical_angle = has_any(t, VERTICAL_ANGLE)
    hanging_object = has_any(t, HANGING_OBJECT)
    conical_explicit = has_any(t, CONICAL_EXPLICIT)
    conical_structural = string_support and horiz_circle and vertical_angle
    # Block-pulley dominance: words such as string/hanging/horizontal also
    # appear in a horizontal block + hanging mass pulley problem.  They must not
    # turn on conical-pendulum formulas unless the conical geometry itself is
    # stated (cone/conical, horizontal circular motion with vertical angle).
    block_pulley_context = has_any(t, HORIZONTAL_TABLE) and has_any(t, HANGING) and has_any(t, PULLEY)
    conical_candidate = (
        not block_pulley_context
        and not has_any(t, [r"수직\s*원|vertical\s+circle", *TOP, *BOTTOM])
        and (
            conical_structural
            or (conical_explicit and (string_support or hanging_object or horiz_circle or vertical_angle))
            or (string_support and (horiz_circle or vertical_angle) and has(t, r"정보|없|확인|명확|not\s+stated|need|angle|원운동|circular|rotates?|회전|돈"))
        )
    )
    if block_pulley_context and not conical_structural and not conical_explicit:
        conical_explicit = False
        conical_structural = False
        conical_candidate = False
    cart = has_any(t, CARTESIAN_VECTOR)
    polar = has_any(t, POLAR) and not cart
    bullet_rot = has_any(t, BULLET) and has_any(t, ROTATING_BODY) and (has_any(t, EMBEDDED) or has_any(t, AXIS_ROTATION))
    return SemanticFlags(
        frictionless=frictionless,
        friction_present=friction_present,
        slip_present=slip_present,
        explicit_pure_rolling=explicit_pure,
        rotation_word=has_any(t, ROTATION_WORD),
        rolling_word=has_any(t, ROLLING_WORD),
        string_support=string_support,
        track_support=has_any(t, TRACK_SUPPORT),
        bottom_position=has_any(t, BOTTOM),
        top_position=has_any(t, TOP),
        banked_curve=has_any(t, BANKED_CURVE),
        flat_curve=has_any(t, FLAT_CURVE),
        max_speed=has_any(t, MAX_SPEED),
        min_speed=has_any(t, MIN_SPEED),
        conical_explicit=conical_explicit,
        conical_structural=conical_structural,
        conical_candidate=conical_candidate,
        cartesian_position_vector=cart,
        polar_motion=polar,
        bullet_rotating_body_collision=bullet_rot,
        horizontal_table=has_any(t, HORIZONTAL_TABLE),
        hanging_mass=has_any(t, HANGING),
        pulley=has_any(t, PULLEY),
    )
