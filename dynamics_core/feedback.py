from __future__ import annotations

import re
from typing import Dict, List, Tuple

from .models import Diagnosis, FeatureReport, Recommendation
from .modeling import build_problem_model, build_solution_blueprint
from .ai_assist import maybe_apply_ai_assist
from .scope_limits import detect_unsupported_scope, assess_information_sufficiency
from . import lexicon

MISCONCEPTIONS = [
    ("포물선 최고점에서 전체 속도 0 착각", [r"최고점.*(?:전체\s*)?속도.*0", r"꼭대기.*속도.*0"], "최고점에서 0이 되는 것은 수직속도 vy입니다. 수평속도 vx는 보통 남아 있습니다."),
    ("충돌에서 에너지 보존을 무조건 사용", [r"충돌.*에너지.*보존", r"부딪.*에너지.*보존"], "충돌에서는 운동량 보존을 먼저 확인합니다. 운동에너지는 완전탄성 조건이 있을 때만 보존됩니다."),
    ("구심력을 새로운 힘으로 추가", [r"구심력.*추가", r"구심력.*별도"], "구심력은 새 힘이 아니라 중심 방향 실제 힘들의 합입니다."),
    ("마찰 방향 단순 암기", [r"마찰.*항상.*속도", r"마찰.*무조건.*반대"], "마찰은 상대운동 또는 상대운동하려는 경향을 방해하는 방향입니다."),
    ("구름 조건 무조건 사용", [r"항상.*v\s*=\s*(?:ω|w).*r", r"굴림.*무조건"], "v=ωR은 미끄러지지 않는 순수 구름 조건에서만 성립합니다."),
    ("강체를 질점처럼 처리", [r"회전.*F\s*=\s*ma만", r"관성모멘트.*무시", r"토크.*무시"], "강체는 병진 ΣF=ma와 회전 ΣM=Iα가 함께 필요할 수 있습니다."),
]


def _blueprint_text(bp) -> str:
    if bp is None:
        return ""
    parts = [
        getattr(bp, "title", ""),
        getattr(bp, "template_id", ""),
        getattr(bp, "final_template_id", ""),
        *getattr(bp, "applicable_equations", []),
        *getattr(bp, "not_applicable_equations", []),
        *getattr(bp, "cautions", []),
    ]
    return "\n".join(str(x) for x in parts if x)


def _problem_family(problem: str, problem_type: str | None = None, bp=None) -> str:
    """Return the final high-level family used to scope misconception checks.

    Beginner-safety rule: problem-type-specific warnings must be driven by the
    final classified family, not by shared words such as string/hanging/tension.
    """
    text = "\n".join([problem or "", problem_type or "", _blueprint_text(bp)]).lower()
    if re.search(r"블록[-\s]*도르래|수평면\s*블록|매달린\s*물체\s*연결|연결된\s*물체/도르래|frictionless_pulley_block|ideal_pulley|massive_pulley|movable_pulley|block_pulley", text, flags=re.I):
        return "block_pulley"
    if "원뿔진자" in text or "conical_pendulum" in text:
        return "conical_pendulum"
    if re.search(r"단진자|simple\s+pendulum|small\s+angle|작은\s*각|작은\s*진폭|소진동|살짝\s*흔들림|pendulum", text, flags=re.I):
        return "simple_pendulum"
    if re.search(r"단일\s*(?:줄|실|끈|로프)|천장에\s*(?:매단|연결된)|single\s+(?:string|cord|rope)|hanging\s+from\s+(?:the\s+)?ceiling|single_string", text, flags=re.I):
        return "single_string_equilibrium"
    if re.search(r"경사진\s*커브|banked\s+curve|banked_curve|커브", text, flags=re.I):
        return "banked_curve"
    if re.search(r"순수\s*구름|미끄럼을\s*동반한\s*구름|rolling", text, flags=re.I):
        return "rolling"
    if re.search(r"충돌|collision|impact", text, flags=re.I):
        return "collision"
    if re.search(r"수직\s*원운동|vertical\s+(?:circle|loop)", text, flags=re.I):
        return "vertical_circle"
    return "general"


def _confirmed_block_pulley_context(problem: str, problem_type: str | None = None, bp=None) -> bool:
    if _problem_family(problem, problem_type, bp) != "block_pulley":
        return False
    # A pulley-specific acceleration-constraint warning is only valid for
    # confirmed connected-body pulley systems, not every problem containing
    # string/hanging/tension.
    text = problem.lower()
    has_pulley_or_connection = re.search(r"도르래|pulley|줄로\s*연결|connected|over\s+a\s+pulley|by\s+a\s+pulley|움직도르래|고정도르래", text, flags=re.I)
    has_multiple_bodies = re.search(r"블록\s*A|블록\s*B|m_A|m_B|두\s*물체|두\s*블록|block\s*A|block\s*B|two\s+(?:blocks|masses|bodies)", problem, flags=re.I)
    has_table_hanging = re.search(r"수평면|테이블|table|horizontal", problem, flags=re.I) and re.search(r"매달|hanging|suspended", problem, flags=re.I)
    return bool(has_pulley_or_connection and (has_multiple_bodies or has_table_hanging or re.search(r"움직도르래|movable\s+pulley", problem, flags=re.I)))


def _ambiguous_pulley_confirmation_question(problem: str, problem_type: str | None = None, bp=None) -> str | None:
    family = _problem_family(problem, problem_type, bp)
    if family in {"block_pulley", "conical_pendulum", "simple_pendulum", "single_string_equilibrium"}:
        return None
    if (lexicon.has_rope(problem) or re.search(r"장력|tension|매달|hanging", problem, flags=re.I)) and not lexicon.has_pulley_structure(problem):
        return "확인 필요: 이 문제가 도르래로 연결된 두 물체 문제라면 두 물체의 가속도 관계를 세워야 합니다. 하지만 현재 문장만으로는 도르래 문제인지 확정하기 어렵습니다."
    return None


def _set_single_string_equilibrium(model, bp) -> None:
    model.problem_type = "단일 줄 평형 문제"
    model.analysis_targets = ["줄/실/끈/로프에 매달린 질점"]
    model.constraints = list(dict.fromkeys([*model.constraints, "정지 또는 평형 상태이면 수직방향 가속도 0"]))
    bp.title = "단일 줄 평형 풀이 골격"
    bp.fbd_forces = ["중력 mg: 아래 방향", "장력 T: 줄 방향 위쪽"]
    bp.coordinate_guide = ["수직 방향을 축으로 잡고 평형식을 세움"]
    bp.applicable_equations = ["ΣF_y = 0", "T = mg"]
    bp.governing_equations = list(bp.applicable_equations)
    bp.auxiliary_equations = list(dict.fromkeys([*getattr(bp, "auxiliary_equations", []), "정지/가만히 있음/움직이지 않음 → a_y = 0"]))
    bp.not_applicable_equations = [eq for eq in getattr(bp, "not_applicable_equations", []) if "도르래" not in eq and "원뿔진자" not in eq]
    bp.cautions = list(dict.fromkeys(["단일 줄 평형 문제이므로 두 물체 가속도 관계를 세우지 않습니다.", *getattr(bp, "cautions", [])]))
    bp.support_level = "기본 평형식 안내"
    bp.template_id = "single_string_equilibrium"  # type: ignore[attr-defined]
    bp.final_template_id = "single_string_equilibrium"  # type: ignore[attr-defined]


def _set_simple_pendulum(model, bp) -> None:
    model.problem_type = "단진자 문제"
    model.analysis_targets = ["줄/실/끈에 매달린 추"]
    model.constraints = list(dict.fromkeys([*model.constraints, "작은 각도/작은 진폭/소진동 근사에서 단진자 주기식 사용 가능"]))
    bp.title = "단진자 주기 풀이 골격"
    bp.fbd_forces = ["중력 mg", "장력 T"]
    bp.coordinate_guide = ["접선 방향과 줄 방향을 구분"]
    bp.applicable_equations = ["T_period = 2π√(L/g)"]
    bp.governing_equations = list(bp.applicable_equations)
    bp.auxiliary_equations = list(dict.fromkeys([*getattr(bp, "auxiliary_equations", []), "작은 진폭/소진동이면 sinθ ≈ θ 근사 가능"]))
    bp.not_applicable_equations = [eq for eq in getattr(bp, "not_applicable_equations", []) if "도르래" not in eq and "원뿔진자" not in eq]
    bp.cautions = list(dict.fromkeys(["단진자는 도르래로 연결된 두 물체 문제가 아니므로 가속도 구속조건 경고를 적용하지 않습니다.", *getattr(bp, "cautions", [])]))
    bp.support_level = "기본 단진자 주기 안내"
    bp.template_id = "simple_pendulum"  # type: ignore[attr-defined]
    bp.final_template_id = "simple_pendulum"  # type: ignore[attr-defined]


def _set_conical_pendulum(model, bp) -> None:
    model.problem_type = "원뿔진자 원운동 문제"
    model.analysis_targets = ["줄/실/로프에 매달린 질점"]
    model.constraints = list(dict.fromkeys([*model.constraints, "줄과 연직선 사이 각도", "수평 원운동", "수직방향 가속도 0"]))
    bp.title = "원뿔진자 풀이 골격"
    bp.fbd_forces = ["중력 mg: 아래 방향", "장력 T: 줄 방향", "장력의 수평성분: 중심 방향"]
    bp.coordinate_guide = ["수직 방향과 수평 중심방향으로 장력을 분해"]
    bp.applicable_equations = ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ", "ω² = g/(L cosθ)"]
    bp.governing_equations = list(bp.applicable_equations)
    bp.auxiliary_equations = list(dict.fromkeys([*getattr(bp, "auxiliary_equations", []), "수평성분 T sinθ가 구심력 역할", "수직성분 T cosθ가 mg와 평형"]))
    bp.not_applicable_equations = [eq for eq in getattr(bp, "not_applicable_equations", []) if "도르래" not in eq]
    bp.cautions = list(dict.fromkeys(["원뿔진자는 도르래 연결 문제가 아니므로 두 물체 가속도 관계를 세우지 않습니다.", *getattr(bp, "cautions", [])]))
    bp.support_level = "원뿔진자 대표식 안내"
    bp.template_id = "conical_pendulum"  # type: ignore[attr-defined]
    bp.final_template_id = "conical_pendulum"  # type: ignore[attr-defined]


def _apply_beginner_v11_special_cases(problem: str, model, bp) -> None:
    """Single-string/simple-pendulum/conical postprocess with v1.2 synonyms.

    Rope-like words are broad cues only.  They never activate pulley-specific
    warnings unless a real pulley/connected-body structure is confirmed.
    """
    t = lexicon.normalize_colloquial(problem)
    if lexicon.is_conical_pendulum(t):
        _set_conical_pendulum(model, bp)
        return
    if lexicon.is_simple_pendulum(t):
        _set_simple_pendulum(model, bp)
        return
    if lexicon.is_single_string_equilibrium(t):
        _set_single_string_equilibrium(model, bp)
        return
    # Keep v1.1 legacy coverage.
    if re.search(r"원뿔진자|수평\s*원운동|conical|cone", t, flags=re.I):
        return
    if lexicon.has_pulley_structure(t) or re.search(r"블록\s*A|block\s*A|block\s*B", t, flags=re.I):
        return
    if re.search(r"(?:천장에\s*)?매단\s*(?:줄|끈)|줄에\s*정지|hanging\s+from\s+(?:the\s+)?ceiling", t, flags=re.I) and re.search(r"정지|평형|장력|equilibrium|at\s+rest|tension", t, flags=re.I):
        _set_single_string_equilibrium(model, bp)
        return
    if re.search(r"단진자|작은\s*각|small\s+angle|simple\s+pendulum", t, flags=re.I) and re.search(r"주기|period|진동|oscillat", t, flags=re.I):
        _set_simple_pendulum(model, bp)
        return

def detect_misconceptions(problem: str, solution: str, problem_type: str | None = None, blueprint=None) -> List[Tuple[str, str]]:
    text = f"{problem}\n{solution}"
    sol = solution or ""
    family = _problem_family(problem, problem_type, blueprint)
    hits: List[Tuple[str, str]] = []
    for name, patterns, explain in MISCONCEPTIONS:
        if any(re.search(p, text, flags=re.IGNORECASE) for p in patterns):
            hits.append((name, explain))

    from .semantic_normalizer import semantic_flags
    sem = semantic_flags(problem)

    def add(name: str, explain: str) -> None:
        if not any(n == name for n, _ in hits):
            hits.append((name, explain))

    if sem.frictionless and re.search(r"f\s*=\s*(?:μ|mu)|마찰력|friction", sol, flags=re.I):
        add("마찰 없는 문제에서 마찰력 사용", "이 문제는 마찰 없는 조건이므로 FBD에 마찰력을 넣거나 f = μN을 적용하면 안 됩니다.")
    if (not sem.explicit_pure_rolling) and re.search(r"v\s*(?:_?G)?\s*=\s*(?:ω|omega|w)\s*R|a\s*(?:_?G)?\s*=\s*(?:α|alpha)\s*R|v\s*=\s*(?:ω|omega|w)\s*R", sol, flags=re.I):
        add("순수 구름 조건 미확인 상태에서 v=ωR 사용", "v_G = ωR, a_G = αR은 접촉점 미끄럼 없음이 명시된 순수 구름에서만 사용할 수 있습니다.")
    if sem.banked_curve and re.search(r"N\s*=\s*mg|N\s*=\s*m\s*g", sol, flags=re.I):
        add("경사진 커브에서 N=mg 단독 사용", "경사진 커브에서는 수직항력의 수직/수평 성분을 분해해야 하므로 N = mg만 단독으로 두면 안 됩니다.")
    if re.search(r"수직\s*원|vertical\s+(?:circle|loop)", problem, flags=re.I) and re.search(r"최고점|top", problem, flags=re.I) and re.search(r"T\s*-\s*mg|N\s*-\s*mg", sol, flags=re.I):
        add("수직 원운동 최고점 힘 방향 혼동", "최고점에서는 중심 방향이 아래쪽이므로 중력과 장력/수직항력이 같은 중심방향으로 들어갈 수 있습니다.")
    if re.search(r"수직\s*원|vertical\s+(?:circle|loop)", problem, flags=re.I) and re.search(r"최저점|bottom|바닥|하단", problem, flags=re.I) and re.search(r"T\s*\+\s*mg|N\s*\+\s*mg", sol, flags=re.I):
        add("수직 원운동 최저점 힘 방향 혼동", "최저점에서는 중심 방향이 위쪽이므로 T - mg 또는 N - mg 형태로 중심방향 힘을 세웁니다.")
    if family == "block_pulley" and _confirmed_block_pulley_context(problem, problem_type, blueprint) and sol.strip():
        if not re.search(r"a_A\s*=\s*a_B|a_A\s*=\s*a|a_B\s*=\s*a|가속도\s*크기\s*같|same\s+acceleration|same\s+magnitude|같은\s*가속도|가속도\s*관계", sol, flags=re.I):
            add("도르래 문제의 가속도 관계 누락", "이상적인 줄로 연결된 두 물체 문제에서는 줄 길이 구속조건 때문에 가속도 크기 관계를 먼저 확인해야 합니다.")
        if not re.search(r"m_B\s*g\s*-\s*T|m_Bg\s*-\s*T|hanging\s+(?:block|mass).*T", sol, flags=re.I):
            add("매달린 물체 B의 운동방정식 누락", "블록-도르래 문제는 각 물체를 따로 FBD로 분리해야 하며, 매달린 물체 B에는 보통 m_Bg - T = m_Ba 형태의 식이 필요합니다.")
    if re.search(r"비탄성|완전\s*비탄성|붙|sticks?|embedded|충돌", problem, flags=re.I) and re.search(r"운동에너지\s*보존|kinetic\s+energy\s+conserved", sol, flags=re.I):
        add("비탄성 충돌에서 운동에너지 보존 사용", "비탄성 충돌에서는 운동에너지가 일반적으로 보존되지 않습니다. 운동량/각운동량 보존 조건을 먼저 확인하세요.")
    if re.search(r"마찰|friction|비보존|nonconservative", problem, flags=re.I) and re.search(r"기계적\s*에너지\s*보존|mechanical\s+energy\s+conserved", sol, flags=re.I):
        add("비보존력이 있는데 기계적 에너지 보존 단독 사용", "마찰이나 비보존력이 있으면 그 일이 에너지식에 포함되어야 합니다.")
    if re.search(r"작용\s*반작용|action\s*reaction", sol, flags=re.I) and re.search(r"같은\s*물체|same\s+body", sol, flags=re.I):
        add("작용-반작용 힘을 같은 FBD에 그림", "작용-반작용 쌍은 서로 다른 물체에 작용하므로 한 물체의 FBD에 동시에 그리면 안 됩니다.")
    return hits


def expected_fbd_items(cues: Dict[str, bool]) -> List[str]:
    items: List[str] = ["중력 mg"]
    if cues.get("incline") or cues.get("friction") or cues.get("no_friction") or cues.get("circular") or cues.get("force"):
        items.append("수직항력 N")
    if cues.get("tension"):
        items.append("장력 T")
    if cues.get("friction"):
        items.append("마찰력 f = μN 또는 f ≤ μ_s N")
    if cues.get("spring"):
        items.append("스프링 힘 kx")
    if cues.get("incline"):
        items.extend(["경사면 방향 좌표축", "mg sinθ / mg cosθ 분해"])
    if cues.get("circular"):
        items.append("반지름 중심 방향 표시")
    if cues.get("rotation") or cues.get("rolling") or cues.get("torque"):
        items.append("회전 방향과 토크 방향")
    if cues.get("instant_center"):
        items.append("각 점 속도 방향과 순간중심 위치")
    return list(dict.fromkeys(items))


def analyze_solution_elements(solution: str, features: FeatureReport, rec: Recommendation) -> Tuple[List[str], List[str]]:
    text = solution.lower()
    cues = features.cues
    good: List[str] = []
    missing: List[str] = []

    def has_any(words: List[str]) -> bool:
        return any(w.lower() in text for w in words)

    if has_any(["좌표", "축", "방향", "부호", "+"]):
        good.append("좌표축과 부호를 의식한 흔적이 있습니다.")
    else:
        missing.append("좌표축과 양의 방향을 먼저 정했는지 적어야 합니다.")

    if has_any(["단위", "m/s", "m/s^2", "kg", "n", "j", "rad/s"]):
        good.append("단위를 확인하려는 흔적이 있습니다.")
    else:
        missing.append("마지막 값의 단위와 물리적 의미를 확인해야 합니다.")

    if rec.primary in ["뉴턴 제2법칙 F=ma", "복합 풀이"] or cues.get("force") or cues.get("tension") or cues.get("friction"):
        if has_any(["fbd", "자유물체도", "힘도", "Σf", "sum f", "ma", "뉴턴"]):
            good.append("힘 문제에서 FBD 또는 ΣF=ma를 고려했습니다.")
        else:
            missing.append("힘/장력/마찰이 있으면 자유물체도(FBD)를 먼저 그려야 합니다.")

    if rec.primary in ["일-에너지 원리", "복합 풀이"] or cues.get("height") or cues.get("spring"):
        if has_any(["에너지", "일", "mgh", "1/2mv", "보존", "손실", "kx"]):
            good.append("에너지 관점이 풀이에 들어가 있습니다.")
        else:
            missing.append("높이/스프링/거리-속도 단서가 있으면 에너지식 후보를 써봐야 합니다.")
        if cues.get("friction") and not has_any(["마찰", "손실", "μ", "mu", "마찰일"]):
            missing.append("마찰이 있으면 단순 에너지 보존이 아니라 마찰이 한 일을 포함해야 합니다.")

    if rec.primary in ["충격량-운동량", "복합 풀이"] or cues.get("collision") or cues.get("momentum"):
        if has_any(["운동량", "mv", "충격량", "impulse", "반발", "e="]):
            good.append("충돌/운동량 관점을 고려했습니다.")
        else:
            missing.append("충돌 또는 운동량 문제는 운동량 보존/충격량-운동량부터 확인해야 합니다.")

    if rec.primary in ["원운동 조건", "복합 풀이"] or cues.get("circular"):
        if has_any(["mv^2/r", "mv²/r", "v^2/r", "v²/r", "구심", "반지름", "n=0"]):
            good.append("원운동의 반지름 방향 조건을 고려했습니다.")
        else:
            missing.append("원운동은 반지름 방향 식 ΣF_r = mv²/R을 확인해야 합니다.")

    if rec.primary in ["강체 평면운동", "복합 풀이"] or cues.get("rotation") or cues.get("rolling") or cues.get("torque"):
        if has_any(["토크", "모멘트", "iα", "관성모멘트", "각가속도", "ω", "v=ωr", "v=wr"]):
            good.append("회전 요소를 고려했습니다.")
        else:
            missing.append("회전/굴림이 있으면 ΣM=Iα, 관성모멘트, 구름 조건을 확인해야 합니다.")

    if rec.primary == "상대속도/순간중심" or cues.get("instant_center"):
        if has_any(["순간중심", "상대속도", "v=ωr", "속도 방향"]):
            good.append("순간중심/상대속도 관점을 고려했습니다.")
        else:
            missing.append("순간중심 문제는 각 점의 속도 방향을 표시하고 v=ωr로 연결해야 합니다.")

    if not solution.strip():
        missing.insert(0, "학생 풀이가 비어 있어 문제 단서 중심으로만 진단했습니다.")
    return list(dict.fromkeys(good)), list(dict.fromkeys(missing))


def next_questions(features: FeatureReport, rec: Recommendation) -> List[str]:
    cues = features.cues
    questions = [
        "이 문제에서 분석할 물체 하나를 고르면 무엇인가?",
        "구하려는 값은 시간과 연결되는가, 거리/높이/힘과 연결되는가?",
    ]
    if rec.primary == "뉴턴 제2법칙 F=ma" or "뉴턴 제2법칙 F=ma" in rec.combined_methods:
        questions.append("FBD에서 빠진 힘이나 잘못 그린 힘 방향은 없는가?")
    if rec.primary == "일-에너지 원리" or "일-에너지 원리" in rec.combined_methods:
        questions.append("처음 상태와 마지막 상태의 에너지 항을 각각 적으면 무엇이 남는가?")
    if rec.primary == "원운동 조건" or "원운동 조건" in rec.combined_methods:
        questions.append("반지름 중심 방향으로 실제 힘의 합은 무엇인가?")
    if rec.primary == "강체 평면운동" or "강체 평면운동" in rec.combined_methods:
        questions.append("질점 모델로 충분한가, 아니면 관성모멘트 I가 필요한가?")
    if cues.get("instant_center"):
        questions.append("각 점의 속도 방향에 수직인 선을 그었을 때 만나는 순간중심은 어디인가?")
    return list(dict.fromkeys(questions))[:5]




def _beginner_insufficient_blueprint_details(family: str) -> tuple[list[str], list[str], list[str]]:
    """Family-specific safe guidance when equation recommendation is stopped."""
    if family == "경사면":
        return (
            ["경사면 문제는 보통 FBD를 그리고 축을 경사면 평행/수직으로 잡습니다."],
            [
                "ΣF_parallel = ma : 경사각·마찰·운동방향 확인 전 구체식 확정 금지",
                "f = μN : 마찰이 있는지와 μ_s/μ_k가 주어졌는지 확인 전 적용 금지",
                "mg sinθ = ma : 마찰 없는 경사면이라는 조건이 명확할 때만 사용",
            ],
            ["경사각, 마찰 여부, 운동 방향, 외력 여부를 먼저 확인하세요."],
        )
    if family == "수직 원운동":
        return (
            ["원운동 문제는 먼저 중심 방향을 정하고 실제 힘의 중심방향 성분을 더합니다."],
            [
                "T - mg = mv²/R : 최저점 줄/끈 장력 문제일 때만 확정 사용",
                "T + mg = mv²/R : 최고점 줄/끈 장력 문제일 때만 확정 사용",
                "N - mg = mv²/R : 트랙/레일 최저점 수직항력 문제일 때만 확정 사용",
                "구심력을 FBD에 별도 힘으로 추가하는 것 금지",
            ],
            ["수평/수직 원운동, 최고점/최저점, 줄/트랙 모델을 먼저 확인하세요."],
        )
    if family == "구름 운동":
        return (
            ["구름 운동은 병진운동과 회전운동을 함께 고려합니다."],
            [
                "v_G = ωR : no slip/without slipping 조건 확인 전 사용 금지",
                "a_G = αR : no slip/without slipping 조건 확인 전 사용 금지",
                "순수 구름으로 확정 : 미끄럼 없음 조건이 명시될 때만 가능",
            ],
            ["rolling이라는 단어만으로 순수 구름을 뜻하지 않습니다. 접촉점 미끄럼 여부를 확인하세요."],
        )
    if family == "커브 주행":
        return (
            ["커브 문제는 중심 방향 힘을 확인하되, 도로가 평평한지 경사진지 먼저 구분합니다."],
            [
                "v_max = √(μ_s g R) : 평평한 커브와 마찰 한계 조건이 명확할 때만 사용",
                "tanθ = v²/(gR) : 마찰 없는 경사진 커브 설계속도 조건일 때만 사용",
                "경사진 커브 최대/최소속도 식 : 경사각과 마찰 방향이 정해진 뒤 사용",
            ],
            ["평평한 커브인지 경사진 커브인지, μ_s와 R이 있는지 먼저 확인하세요."],
        )
    return (
        ["FBD를 그리고 실제 힘과 구속조건을 먼저 정리합니다."],
        ["현재 정보만으로 특정 공식 또는 풀이법을 확정 적용하지 마세요.", "낮은 신뢰도의 추측성 풀이를 확정처럼 사용하지 마세요."],
        ["조건을 보완한 뒤 다시 진단을 실행하세요."],
    )


def _auto_wrong_reason_tags(problem: str, bp, missing_elements: list[str], misconception_hits: list[tuple[str, str]]) -> list[str]:
    """Map detected warnings/forbidden formulas to beginner-friendly review tags."""
    text = "\n".join([problem, *getattr(bp, "not_applicable_equations", []), *getattr(bp, "cautions", []), *getattr(bp, "ambiguity_notes", []), *missing_elements, *[x[0] for x in misconception_hits]])
    rules = [
        (r"v_G\s*=\s*ωR|a_G\s*=\s*αR|순수\s*구름|no slip|미끄럼", "구름 조건 착각"),
        (r"운동에너지\s*보존|에너지.*충돌|충돌.*에너지", "운동량/에너지 보존 조건 착각"),
        (r"마찰|μ|mu|friction", "마찰 방향/마찰 조건 오류"),
        (r"최고점|최저점|바닥점|원운동.*위치|중심\s*방향|구심력", "원운동 방향/위치 오류"),
        (r"경사각|경사면|FBD.*조건|좌표축|물체 개수|정보 부족", "FBD 조건 누락"),
        (r"구심력을 FBD에 별도|구심력.*별도", "원운동 힘 개념 오류"),
        (r"각운동량|H_O|운동량|충돌", "운동량 보존 조건 착각"),
        (r"관성모멘트|I_G|ΣM", "관성모멘트/회전식 오류"),
    ]
    out: list[str] = []
    for pattern, tag in rules:
        if re.search(pattern, text, flags=re.I) and tag not in out:
            out.append(tag)
    return out

def build_diagnosis(problem: str, solution: str, user_method: str, features: FeatureReport, rec: Recommendation, ai_model: str | None = None, enable_ai_assist: bool = True) -> Diagnosis:
    info = assess_information_sufficiency(problem)
    if info.status == "insufficient":
        from .models import ProblemModel, SolutionBlueprint

        title = "정보가 부족하여 풀이 추천을 멈췄습니다."
        body = info.message
        model = ProblemModel(
            problem_type="정보 부족: 추가 조건 필요",
            requested_quantity="추가 정보 필요",
            assumptions=[info.message],
            risky_methods=["낮은 신뢰도의 추측성 풀이를 확정처럼 사용하는 것"],
        )
        safe_principles, blocked_equations, family_cautions = _beginner_insufficient_blueprint_details(info.detected_family)
        blueprint = SolutionBlueprint(
            title="정보 부족 · 추가 조건 필요",
            fbd_forces=[],
            coordinate_guide=["FBD를 그리기 전에 그림 속 물체, 연결, 힘, 마찰, 운동 방향을 텍스트로 먼저 정리하세요."],
            applicable_equations=[],
            governing_equations=[],
            auxiliary_equations=safe_principles,
            not_applicable_equations=blocked_equations,
            cautions=[info.message, "정보가 부족한 상태에서 추측으로 공식을 고르면 오답으로 이어질 수 있습니다.", *family_cautions],
            warnings=["정보 부족"],
            ambiguity_notes=list(info.missing_items),
            next_steps=["그림 정보를 텍스트로 옮겨 적습니다.", "물체 개수, 질량, 마찰 여부, 연결 구조, 구하려는 값을 추가합니다.", "조건을 보완한 뒤 다시 진단을 실행합니다."],
            support_level="정보 부족: 풀이 추천 중단",
        )
        blueprint.forbidden_formula_guard_applied = True  # type: ignore[attr-defined]
        blueprint.consistency_check_passed = True  # type: ignore[attr-defined]
        return Diagnosis(features, rec, title, body, [], [info.message], [], [], info.suggested_questions, model, blueprint)

    good, missing = analyze_solution_elements(solution, features, rec)
    fbd = expected_fbd_items(features.cues)
    qs = next_questions(features, rec)

    if user_method == rec.primary or (rec.primary == "복합 풀이" and user_method in rec.combined_methods):
        title = "풀이 방향은 대체로 좋습니다."
        body = f"선택한 {user_method}은/는 현재 단서와 잘 맞습니다. 이제 좌표축, FBD, 적용 조건을 검산하면 됩니다."
    elif user_method == "자동 추정":
        title = "앱이 먼저 풀이 방향을 추정했습니다."
        body = f"현재 추천은 {rec.primary}입니다. 추천 이유와 주의사항을 보고 직접 풀이법을 다시 골라보세요."
    else:
        title = "풀이 방향을 다시 점검해보는 게 좋습니다."
        body = f"선택한 방법은 {user_method}이지만, 현재 단서상 추천은 {rec.primary}입니다. 공식 이름보다 어떤 물리량을 연결해야 하는지 먼저 보세요."

    model = build_problem_model(problem, features, rec, user_method)
    blueprint = build_solution_blueprint(model, features, rec, problem)
    _apply_beginner_v11_special_cases(problem, model, blueprint)
    confirm_question = _ambiguous_pulley_confirmation_question(problem, model.problem_type, blueprint)
    if confirm_question and confirm_question not in qs:
        qs.insert(0, confirm_question)
    misconceptions = detect_misconceptions(problem, solution, model.problem_type, blueprint)

    scope = detect_unsupported_scope(problem)
    if scope.status == "unsupported":
        model.problem_type = scope.category
        model.allowed_methods = []
        model.risky_methods = [
            "2D 평면운동 공식으로 3D 강체 운동을 억지 풀이하는 것",
            "관성텐서를 스칼라 I 하나로 단순화하는 것",
            "오일러 방정식/세차 운동 문제를 일반 원운동으로 처리하는 것",
        ]
        model.assumptions = [scope.message]
        blueprint.title = "현재 미지원 범위 안내"
        blueprint.fbd_forces = []
        blueprint.coordinate_guide = [
            "3차원 각속도 성분, 관성텐서, 회전좌표계 또는 오일러 방정식이 필요한 문제입니다.",
            "현재 앱은 2차원 입자/강체 평면운동 대표 유형을 중심으로 지원합니다.",
        ]
        blueprint.applicable_equations = []
        blueprint.governing_equations = []
        blueprint.not_applicable_equations = [
            "2D ΣM_G = I_Gα 하나만으로 3D 강체 운동을 풀이하는 것 금지",
            "평면 원운동/순수 구름/경사진 커브 공식으로 대체 적용 금지",
        ]
        blueprint.cautions = [scope.message]
        blueprint.warnings = list(blueprint.cautions)
        blueprint.ambiguity_notes = [
            "3D 강체 운동은 자이로스코프, 세차/장동, 관성텐서, 오일러 방정식 등 별도 단원 지식이 필요합니다.",
            "문제를 2D 평면운동으로 단순화할 수 있는 조건이 명시되어 있으면 그 조건을 텍스트로 추가하세요.",
        ]
        blueprint.next_steps = [
            "문제가 정말 3D 강체 운동인지 확인합니다.",
            "평면운동으로 단순화할 수 있는 대칭 조건이나 구속 조건이 있는지 확인합니다.",
            "3D 문제라면 교재의 오일러 방정식/관성텐서 단원 해설을 함께 참고하세요.",
        ]
        blueprint.support_level = "미지원: 안내만 제공"
        blueprint.forbidden_formula_guard_applied = True  # type: ignore[attr-defined]
        blueprint.consistency_check_passed = True  # type: ignore[attr-defined]
        return Diagnosis(features, rec, title, body, good, missing, misconceptions, fbd, qs, model, blueprint)

    # 선택적 GPT mini 보조 판별: API key가 없거나 실패해도 규칙 기반 결과로 안전하게 fallback합니다.
    blueprint = maybe_apply_ai_assist(problem, features, rec, model, blueprint, enable_api=enable_ai_assist, model_name=ai_model or None or "gpt-4o-mini")
    return Diagnosis(features, rec, title, body, good, missing, misconceptions, fbd, qs, model, blueprint)
