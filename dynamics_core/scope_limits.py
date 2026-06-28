from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ScopeDecision:
    status: str
    category: str
    message: str
    detected: list[str]
    support_level: str


@dataclass(frozen=True)
class SymbolHelper:
    label: str
    insert_text: str
    description: str = ""


@dataclass(frozen=True)
class InputTemplate:
    label: str
    text: str
    description: str = ""


IMAGE_INPUT_NOTICE = (
    "현재 버전은 이미지/그림을 직접 인식하지 않습니다. 교재 그림에 포함된 치수, 각도, 힘 방향, "
    "접촉 조건, 도르래 연결 구조 등을 텍스트로 입력해야 정확한 진단이 가능합니다."
)

NUMERIC_SOLVER_NOTICE = (
    "이 앱은 동역학 문제의 유형을 판별하고, 적용식과 풀이 순서를 안내하는 학습 보조 도구입니다. "
    "모든 문제의 최종 수치 답을 자동으로 계산하는 완전 자동 풀이기는 아닙니다."
)

STREAMLIT_MOBILE_NOTICE = (
    "이 앱은 Streamlit 기반 모바일 웹앱입니다. 모바일 브라우저에서 사용할 수 있지만 iOS/Android 네이티브 앱이나 "
    "완성형 PWA가 아니며, 오프라인 사용·푸시 알림·앱스토어 설치·네이티브 수준 제스처는 지원하지 않습니다."
)

FIGURE_TEXT_CHECKLIST = [
    "물체 개수와 각 물체의 질량",
    "경사각 θ, 반지름 R, 끈 길이 L 등 그림 속 치수",
    "끈/도르래/레일/트랙/접촉면 연결 구조",
    "마찰 있음/없음, μ_s 또는 μ_k",
    "회전축·피벗·힌지·충돌 위치",
    "힘 방향 또는 운동 방향",
    "초기속도/각속도와 구하려는 값",
    "좌표축 또는 양의 방향 선택",
]

CALCULATION_SUPPORT_LEVELS = {
    "유형 판별": "가능",
    "적용식 제시": "가능",
    "풀이 골격 제시": "가능",
    "자동 수치 답 계산": "제한적",
    "단위/유효숫자 포함 최종 답": "제한적",
}

SUPPORTED_SCOPE_ROWS = [
    ("직교좌표 위치벡터", "A", "i/j, <x,y>, (x,y) 성분 위치벡터 미분"),
    ("극좌표 운동", "B", "r(t), θ(t), e_r/e_θ 단서가 명확한 경우"),
    ("수평면 블록-도르래", "A", "마찰 있음/없음, 매달린 블록 연결 문제"),
    ("경사면 물체", "B", "기본 FBD와 마찰 조건 안내 중심"),
    ("순수 구름", "A", "no slip/without slipping/skidding 계열"),
    ("미끄럼 동반 회전", "A", "contact slip/slipping/skidding 계열"),
    ("수직 원운동", "A", "줄 장력과 트랙 수직항력, 최고/최저점"),
    ("원뿔진자", "A", "끈+수평 원운동+수직선 각도 또는 cone 표현"),
    ("경사진 커브", "A", "마찰 없음/최대속도/최소속도 대표식"),
    ("loop-the-loop", "B", "접촉 유지 조건과 에너지식 안내"),
    ("탄환-회전강체 충돌", "A", "고정축 기준 각운동량 보존"),
    ("일반 강체 평면운동", "B", "ΣF=ma_G, ΣM_G=I_Gα 골격 중심"),
    ("3D 강체 운동/자이로스코프", "미지원", "오일러 방정식, 관성텐서, 세차/장동 등"),
]

UNSUPPORTED_3D_PATTERNS = [
    r"\b3\s*d\b|three[-\s]?dimensional|3차원|공간\s*강체",
    r"angular\s+velocity\s+components|ωx|ω_y|ωz|omega[_\s-]?[xyz]|\bwx\b|\bwy\b|\bwz\b",
    r"euler'?s?\s+equations?|오일러\s*방정식",
    r"gyroscope|gyroscopic|자이로스코프|자이로",
    r"precession|nutation|세차|장동",
    r"inertia\s+tensor|tensor\s+matrix|관성\s*텐서|관성텐서|관성\s*행렬",
    r"rotating\s+reference\s+frame|회전\s*좌표계",
    r"coriolis|코리올리",
]

SYMBOL_HELPERS = [
    SymbolHelper("θ", "theta ", "각도"),
    SymbolHelper("ω", "omega ", "각속도"),
    SymbolHelper("α", "alpha ", "각가속도"),
    SymbolHelper("μ", "mu ", "마찰계수"),
    SymbolHelper("μ_s", "mu_s ", "정지마찰계수"),
    SymbolHelper("μ_k", "mu_k ", "운동마찰계수"),
    SymbolHelper("ΣF", "sum F ", "힘의 합"),
    SymbolHelper("ΣM_G", "sum M_G ", "질량중심 기준 모멘트"),
    SymbolHelper("v_G", "v_G ", "질량중심 속도"),
    SymbolHelper("a_G", "a_G ", "질량중심 가속도"),
    SymbolHelper("I_G", "I_G ", "질량중심 관성모멘트"),
    SymbolHelper("e_r", "e_r ", "극좌표 반지름 방향"),
    SymbolHelper("e_θ", "e_theta ", "극좌표 횡방향"),
    SymbolHelper("r_dot", "r_dot ", "r 미분"),
    SymbolHelper("theta_dot", "theta_dot ", "theta 미분"),
]

ASCII_SYMBOL_GUIDE = {
    "theta": "θ",
    "omega": "ω",
    "alpha": "α",
    "mu_s": "μ_s",
    "mu_k": "μ_k",
    "sum F": "ΣF",
    "sum M_G": "ΣM_G",
    "e_theta": "e_θ",
    "theta_dot": "θ_dot",
}

INPUT_TEMPLATES = [
    InputTemplate(
        "수평면 블록-도르래",
        "Block A of mass m_A is on a frictionless horizontal table. Block B of mass m_B hangs over an ideal pulley. Find the acceleration and tension.",
        "마찰 없음 수평면 + 매달린 블록",
    ),
    InputTemplate(
        "경사면 물체",
        "A block of mass m slides on an incline of angle theta. State whether the surface is frictionless or has coefficient mu. Find acceleration along the incline.",
        "경사각, 마찰 조건 입력",
    ),
    InputTemplate(
        "수직 원운동",
        "A ball attached to a string moves in a vertical circle of radius R. Find the tension at the bottom when speed is v.",
        "최고점/최저점과 힘 기호 명시",
    ),
    InputTemplate(
        "원뿔진자",
        "A bob tied to a string of length L moves in a horizontal circle. The string makes angle theta with the vertical. Find omega.",
        "수평 원운동 + 수직선 각도",
    ),
    InputTemplate(
        "경사진 커브",
        "A car moves on a banked curve of radius R and bank angle theta with static friction coefficient mu_s. Find maximum or minimum speed.",
        "최대/최소속도 명시",
    ),
    InputTemplate(
        "순수 구름",
        "A cylinder rolls without slipping down an incline of angle theta. Use v_G = omega R and a_G = alpha R.",
        "no slip 조건 명시",
    ),
    InputTemplate(
        "회전충돌",
        "A projectile of mass m_b hits and sticks to a rod pivoted at O. Find angular velocity just after impact using angular momentum about O.",
        "고정축 기준 각운동량 보존",
    ),
]


def _matches(text: str, patterns: Iterable[str]) -> list[str]:
    out: list[str] = []
    for p in patterns:
        if re.search(p, text, flags=re.I):
            out.append(p)
    return out


def detect_unsupported_scope(text: str) -> ScopeDecision:
    detected = _matches(text, UNSUPPORTED_3D_PATTERNS)
    if detected:
        return ScopeDecision(
            status="unsupported",
            category="현재 미지원 범위: 3차원 강체 운동",
            message=(
                "이 문제는 3차원 강체 운동, 자이로스코프/세차, 오일러 방정식, 관성텐서, 회전좌표계 또는 "
                "코리올리 가속도 유형으로 보입니다. 현재 버전은 2차원 평면 동역학 중심이므로 이 유형은 지원하지 않습니다."
            ),
            detected=detected,
            support_level="미지원",
        )
    return ScopeDecision("supported", "지원 범위 내 후보", "대표 2D 동역학 유형으로 분석을 시도합니다.", [], "유형별 상이")


def calculation_support_summary() -> list[str]:
    return [f"{k}: {v}" for k, v in CALCULATION_SUPPORT_LEVELS.items()]


def limitation_cards() -> list[tuple[str, str]]:
    return [
        ("이미지/그림 인식", IMAGE_INPUT_NOTICE),
        ("계산 지원 수준", NUMERIC_SOLVER_NOTICE),
        ("3차원 강체 운동", "자이로스코프, 오일러 방정식, 3D 관성텐서 기반 운동은 현재 미지원입니다."),
        ("Streamlit 모바일 웹앱", STREAMLIT_MOBILE_NOTICE),
    ]


def insert_helper_text(current: str, token: str) -> str:
    current = current or ""
    sep = "" if not current or current.endswith((" ", "\n")) else " "
    return current + sep + token

# ---------------------------------------------------------------------------
# Beginner safety / input-completeness helpers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InformationCompletenessDecision:
    status: str
    message: str
    missing_items: list[str]
    suggested_questions: list[str]
    detected_family: str = "일반"


COMMON_REQUIRED_INPUTS = [
    "분석할 물체가 무엇인지",
    "물체 개수와 각 물체의 질량",
    "힘, 장력, 마찰, 접촉 조건",
    "경사각·반지름·끈 길이 등 그림 속 치수",
    "운동 방향 또는 양의 방향",
    "구하려는 값",
]

PROBLEM_FAMILY_CHECKLISTS: dict[str, list[str]] = {
    "수평면 블록-도르래": [
        "블록 A가 수평면인지 경사면인지",
        "매달린 블록 B가 있는지",
        "각 물체의 질량 m_A, m_B",
        "마찰 있음/없음 또는 마찰계수",
        "끈과 도르래를 이상적으로 볼 수 있는지",
        "구하려는 값이 가속도인지 장력인지",
    ],
    "경사면": [
        "경사각 theta",
        "마찰 있음/없음 또는 μ_s/μ_k",
        "물체가 위/아래 어느 방향으로 움직이는지",
        "외력이 있는지",
        "정지 상태인지 운동 중인지",
        "구하려는 값",
    ],
    "수직 원운동": [
        "줄/끈 문제인지 트랙/레일 문제인지",
        "최저점/최고점/임의각도 중 어느 위치인지",
        "반지름 R 또는 줄 길이 L",
        "속력 v 또는 각속도 ω",
        "구하려는 힘이 장력 T인지 수직항력 N인지",
    ],
    "원뿔진자": [
        "줄/끈/로프 길이 L",
        "줄과 수직선 사이 각도 theta",
        "수평 원운동 반지름 r",
        "구하려는 값이 장력인지 각속도인지",
    ],
    "구름 운동": [
        "순수 구름인지 미끄럼 동반 회전인지",
        "물체 형상과 관성모멘트 I_G",
        "반지름 R",
        "경사각/외력/마찰 조건",
        "구하려는 값",
    ],
    "커브 주행": [
        "도로가 평평한지 경사진/banked 커브인지",
        "커브 반지름 R",
        "마찰 있음/없음과 정지마찰계수 μ_s",
        "경사진 커브라면 경사각 θ",
        "최대속도/최소속도/설계속도 중 무엇인지",
        "미끄러지기 직전 조건과 미끄러짐 방향",
    ],
    "회전충돌": [
        "충돌 물체와 강체 종류",
        "충돌 위치와 고정축/피벗 위치",
        "충돌 전 속도 v",
        "충돌 후 붙는지/튕기는지",
        "구하려는 값이 충돌 직후 각속도인지",
    ],
}

_FIGURE_ONLY_PATTERNS = [
    r"그림과\s*같은", r"그림\s*처럼", r"도식과\s*같은", r"shown\s+in\s+the\s+figure",
    r"as\s+shown", r"diagram", r"figure", r"시스템에서\s*가속도", r"system.*acceleration",
]

_MEANINGFUL_PHYSICS_PATTERNS = [
    r"block|mass|particle|cylinder|disk|wheel|rod|bar|bob|bead|car|vehicle|ball|projectile|bullet",
    r"블록|물체|질점|원통|원반|바퀴|막대|구슬|공|자동차|탄환|투사체",
    r"incline|table|pulley|string|rope|cord|track|rail|curve|bank|loop|circle|pivot|hinge",
    r"경사|수평|도르래|줄|끈|실|레일|트랙|커브|원운동|회전축|피벗|힌지",
    r"friction|smooth|rough|tension|normal|force|gravity|weight|mu|μ|theta|angle|radius|velocity|speed",
    r"마찰|장력|수직항력|힘|중력|각도|반지름|속도|속력|가속도|질량",
]


def detect_problem_family_for_checklist(text: str) -> str:
    low = text.lower()
    if re.search(r"conical|cone|원뿔", low) or (re.search(r"수평\s*원운동|horizontal\s+circle|수평\s*원을", low) and re.search(r"수직선|vertical|각도|theta|θ", low)):
        return "원뿔진자"
    if re.search(r"pulley|hanging|도르래|매달", low):
        return "수평면 블록-도르래"
    if re.search(r"incline|경사면|slope", low):
        return "경사면"
    # Curve/road context must be detected before generic slip/rolling, because
    # "slipping before maximum speed" on a road curve is not rolling-contact slip.
    if re.search(r"banked|flat\s+curve|curve|turn|circular\s+road|roadway|커브|곡선\s*도로|원형\s*도로|경사진\s*도로|도로.*곡선|뱅크", low) and re.search(r"car|vehicle|자동차|차량|road|도로|curve|turn|커브", low):
        return "커브 주행"
    if re.search(r"vertical.*circle|loop|수직.*원|최저점|최고점|bottom|top", low):
        return "수직 원운동"
    if re.search(r"conical|cone|원뿔", low):
        return "원뿔진자"
    if re.search(r"rolling|rolls|구름|굴러|skid|slip", low):
        return "구름 운동"
    if re.search(r"projectile|bullet|collision|impact|탄환|투사체|충돌", low):
        return "회전충돌"
    return "일반"


def input_checklist_for_text(text: str) -> list[str]:
    family = detect_problem_family_for_checklist(text)
    return PROBLEM_FAMILY_CHECKLISTS.get(family, COMMON_REQUIRED_INPUTS)




def _has_required(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.I) is not None


def question_wizard_for_text(text: str) -> list[str]:
    """Return step-by-step beginner questions for the likely problem family."""
    family = detect_problem_family_for_checklist(text)
    table: dict[str, list[str]] = {
        "경사면": [
            "경사각 theta가 주어졌나요?",
            "마찰이 없나요, 있나요? 있다면 μ_s 또는 μ_k가 주어졌나요?",
            "물체가 위로 움직이나요, 아래로 움직이나요, 아니면 정지 직전인가요?",
            "외력이 작용하나요? 작용한다면 방향과 크기는 무엇인가요?",
            "구하려는 값은 가속도, 마찰력, 장력, 수직항력 중 무엇인가요?",
        ],
        "수직 원운동": [
            "수평 원운동인가요, 수직 원운동인가요?",
            "수직 원운동이라면 최저점, 최고점, 중간 위치 중 어디인가요?",
            "줄/끈 장력 문제인가요, 트랙/레일 수직항력 문제인가요?",
            "반지름 R과 속력 v 또는 각속도 omega가 주어졌나요?",
            "중력을 포함해야 하는 위치인가요?",
        ],
        "구름 운동": [
            "미끄러지지 않는 순수 구름이라고 명시되어 있나요?",
            "접촉점에서 미끄럼이 있다고 명시되어 있나요?",
            "물체의 반지름 R과 관성모멘트 I_G가 주어졌나요?",
            "경사각, 외력, 마찰계수 중 어떤 조건이 주어졌나요?",
            "구하려는 값은 a_G, alpha, 마찰력, 속도 중 무엇인가요?",
        ],
        "커브 주행": [
            "도로는 평평한가요, 경사져 있나요?",
            "커브 반지름 R이 주어졌나요?",
            "마찰이 있나요? 있다면 정지마찰계수 μ_s가 주어졌나요?",
            "경사진 커브라면 경사각 theta가 주어졌나요?",
            "구하는 값은 최대속도인가요, 최소속도인가요, 설계속도인가요?",
            "미끄러지기 직전 조건인가요?",
            "경사진 커브라면 차량이 위쪽으로 미끄러지려 하나요, 아래쪽으로 미끄러지려 하나요?",
        ],
        "수평면 블록-도르래": [
            "물체는 몇 개인가요?",
            "각 물체는 수평면, 경사면, 매달림 중 어디에 있나요?",
            "줄과 도르래는 이상적인가요?",
            "마찰이 있나요? 있다면 마찰계수는 무엇인가요?",
            "구하려는 값은 가속도인가요, 장력인가요?",
        ],
        "회전충돌": [
            "충돌체가 붙나요, 튕기나요?",
            "고정축, 힌지, 피벗 위치는 어디인가요?",
            "충돌 위치와 축까지의 거리 r이 주어졌나요?",
            "충돌 직후 각속도 omega를 구하나요?",
        ],
        "원뿔진자": [
            "줄 길이 L이 주어졌나요?",
            "줄과 수직선 사이 각도 theta가 주어졌나요?",
            "물체가 수평 원운동한다고 명시되어 있나요?",
            "구하려는 값은 장력 T, 반지름 r, 각속도 omega 중 무엇인가요?",
        ],
    }
    return table.get(family, [
        "분석할 물체는 무엇인가요?",
        "그 물체에 작용하는 실제 힘은 무엇인가요?",
        "마찰, 줄, 도르래, 레일, 회전축 같은 구속조건이 있나요?",
        "구하려는 값은 무엇인가요?",
    ])


def _type_specific_insufficiency(cleaned: str, family: str, checklist: list[str]) -> InformationCompletenessDecision | None:
    """Conservative beginner-mode gate.

    A keyword such as rolling/curve/incline is not enough to present equations.
    If the key conditions for that family are missing, stop formula recommendation
    and ask for the missing conditions instead.
    """
    from .semantic_normalizer import semantic_flags

    sem = semantic_flags(cleaned)
    low = cleaned.lower()
    questions = question_wizard_for_text(cleaned)

    def decision(message: str, missing: list[str], fam: str) -> InformationCompletenessDecision:
        return InformationCompletenessDecision("insufficient", message, missing, questions, fam)

    # Incline: a bare "block on an incline, find acceleration" is unsafe.
    incline_context = _has_required(cleaned, r"경사면|빗면|incline|inclined\s+plane|slope")
    asks_accel = _has_required(cleaned, r"가속도|acceleration|accelerate")
    has_angle = _has_required(cleaned, r"theta|θ|\b\d+\s*(?:deg|degree|°)|경사각|각도")
    has_friction_mode = sem.frictionless or sem.friction_present or _has_required(cleaned, r"마찰\s*(?:있|없|무시)|frictionless|smooth|rough|with\s+friction|no\s+friction|mu|μ")
    has_motion_dir = _has_required(cleaned, r"아래|위로|내려|올라|down|up|slides?|moving|initially|정지")
    asks_skeleton = _has_required(cleaned, r"기본\s*방정식\s*골격|equation\s+skeleton|general\s+equation|자유물체도|좌표계|FBD|coordinate|적용\s*조건|주의점|질량\s*m|mass\s*m")
    has_connection_context = _has_required(cleaned, r"도르래|pulley|매달|hanging|connected|줄로\s*연결")
    bare_incline_prompt = incline_context and asks_accel and _has_required(cleaned, r"block|블록|물체") and not asks_skeleton and not has_connection_context
    if bare_incline_prompt and not (has_angle and has_friction_mode):
        missing = []
        if not has_angle:
            missing.append("경사각 theta 또는 수치 각도")
        if not has_friction_mode:
            missing.append("마찰 있음/없음 또는 μ_s/μ_k")
        if not has_motion_dir:
            missing.append("물체의 운동 방향 또는 정지/미끄러짐 상태")
        missing.extend(["외력 작용 여부", "일반식인지 수치값인지"])
        return decision("경사면 문제 후보이지만 필수 조건이 부족합니다. 조건을 확인하기 전에는 구체 방정식을 확정하지 않습니다.", missing, "경사면")

    # Circular/tension: need horizontal/vertical model and position before T formulas.
    circular_context = _has_required(cleaned, r"원운동|circular\s+motion|circle|loop|원형")
    asks_tension = _has_required(cleaned, r"장력|tension")
    enough_circle_model = _has_required(cleaned, r"수평|horizontal|수직|vertical|최저|최하|바닥|하단|최고|top|bottom|lowest|highest")
    if circular_context and asks_tension and not enough_circle_model:
        return decision(
            "원운동 장력 문제 후보이지만 위치와 운동면이 불명확합니다. 최고점/최저점/수평 원운동을 구분한 뒤 식을 세우세요.",
            ["수평 원운동인지 수직 원운동인지", "최저점/최고점/중간 위치", "줄/끈 모델인지", "반지름 R", "속력 v 또는 각속도 omega"],
            "수직 원운동",
        )
    if circular_context and _has_required(cleaned, r"속도|속력|speed|velocity") and not _has_required(cleaned, r"반지름|radius|R\b|수평|수직|평평|flat|banked|경사|마찰|friction|최대|최소|maximum|minimum|미끄러"):
        return decision(
            "원운동 문제 후보이지만 반지름, 운동면, 힘 모델이 부족합니다. 조건 확인 전에는 원운동 식을 확정하지 않습니다.",
            ["반지름 R", "수평/수직 원운동 여부", "줄/트랙/도로/레일 중 어떤 모델인지", "구하려는 값과 주어진 속도/각속도"],
            "수직 원운동",
        )

    # Rolling: the word rolling alone is not pure rolling.
    round_body = _has_required(cleaned, r"원통|원반|원판|바퀴|공|구슬|cylinder|disk|wheel|sphere|ball")
    rolling_context = round_body and _has_required(cleaned, r"굴러|구르|구름|rolling|rolls?\b")
    if rolling_context and not sem.explicit_pure_rolling and not sem.slip_present:
        return decision(
            "구름 운동 후보이지만 미끄럼 여부가 명확하지 않습니다. 순수 구름 조건식을 적용하기 전 no slip/without slipping 조건을 확인하세요.",
            ["접촉점에서 미끄러짐이 없는지", "미끄럼 동반 회전인지", "반지름 R", "관성모멘트 I_G", "마찰 조건과 경사각/외력"],
            "구름 운동",
        )

    # Curve driving: need flat/banked geometry AND radius/friction/limit
    # conditions before presenting formula-like equations. A bare phrase such as
    # "banked curve" or "flat curve" is a family hint, not enough information for
    # a beginner-safe equation recommendation.
    curve_context = (
        (_has_required(cleaned, r"curve|turn|커브|곡선\s*도로|원형\s*도로|circular\s+road|roadway|뱅크")
         and _has_required(cleaned, r"car|vehicle|자동차|차량|도로|road|curve|turn|커브"))
        or sem.flat_curve or sem.banked_curve
    )
    asks_limit_speed = sem.max_speed or sem.min_speed or _has_required(cleaned, r"maximum|minimum|highest|lowest|fastest|최대|최소|최고|최저|speed|velocity|속도|속력|설계속도|design\s+speed")
    if curve_context and asks_limit_speed:
        has_radius = _has_required(cleaned, r"반지름|radius|\bR\b|r\s*=")
        has_static_friction = sem.friction_present or _has_required(cleaned, r"정지마찰|static\s+friction|coefficient\s+of\s+static\s+friction|μ_s|mu_s|mu\s*_?s|마찰계수|마찰\s*방향|friction\s+direction")
        has_frictionless = sem.frictionless or _has_required(cleaned, r"\bsmooth(?=\b|[가-힣])")
        has_angle = _has_required(cleaned, r"경사각|bank\s+angle|angle\s*(?:θ|theta)|theta|θ|\b\d+\s*(?:deg|degree|°)")
        asks_design = _has_required(cleaned, r"설계\s*속도|design\s+speed|design\s+velocity|필요한\s*경사각|경사각.*구|속도.*경사각.*관계|경사각.*관계")
        has_slip_limit = _has_required(cleaned, r"미끄러지기\s*직전|before\s+(?:slipping|sliding)|impending\s+(?:slip|sliding)|한계|limit") or sem.max_speed or sem.min_speed
        # A road-curve statement that explicitly says the vehicle is just about
        # to slide outward/inward/up/down is already a friction-limit case even
        # if the coefficient symbol is left implicit. This is different from a
        # bare 'banked curve, maximum speed' prompt.
        limit_direction_implied = _has_required(cleaned, r"(?:미끄러지기\s*직전|미끄러지지\s*않|sliding\s+(?:outward|inward|up|down)|slipping\s+(?:outward|inward|up|down)|before\s+(?:slipping|sliding)|마찰\s*방향)")
        flat_min_mu_query = sem.flat_curve and _has_required(cleaned, r"최소\s*마찰계수|minimum\s+coefficient|minimum\s+friction|마찰계수.*구하")
        wants_friction_limit_speed = has_static_friction and _has_required(cleaned, r"limiting\s+speed|speed\s+limit|limit(?:ing)?\s+of\s+speed|속도\s*한계|한계\s*속도")

        missing: list[str] = []
        message = "커브 주행 원운동 문제 후보이지만 추가 조건이 필요합니다. 조건이 충분해질 때까지 구체식을 적용식처럼 제시하지 않습니다."

        if not (sem.flat_curve or sem.banked_curve):
            missing.append("도로가 평평한 커브인지 경사진/banked 커브인지")
            if not has_radius:
                missing.append("커브 반지름 R")

        if sem.flat_curve:
            # For maximum-speed prompts, a flat-curve formula is unsafe unless
            # the friction limit is part of the statement. Symbolic derivation of
            # the required/minimum friction coefficient is allowed.
            if not flat_min_mu_query:
                if not has_static_friction:
                    missing.append("정지마찰계수 μ_s 또는 마찰 한계 조건")
                    if not has_radius:
                        missing.append("커브 반지름 R")
                if not has_slip_limit:
                    missing.append("미끄러지기 직전/최대속도 한계 조건")
        elif sem.banked_curve:
            # Symbolic banked-curve formulas can use R and θ as symbols, but the
            # physical case must be identified: frictionless design speed or
            # friction-limited max/min speed. Bare 'banked curve, max speed' stays
            # gated until friction/angle/radius conditions are clarified.
            if sem.max_speed or sem.min_speed:
                # Beginner strict gate: a bare "banked curve, max speed" stays
                # gated, but a statement with static friction or an explicit
                # impending-sliding direction may use symbolic R and θ formulas.
                # The formula itself reminds the learner that R and θ are needed.
                if not (has_static_friction or limit_direction_implied):
                    missing.append("정지마찰계수 μ_s")
                    if not has_radius:
                        missing.append("커브 반지름 R")
                    if not has_angle:
                        missing.append("경사진 커브의 경사각 θ")
                if not has_slip_limit and not (has_static_friction or limit_direction_implied):
                    missing.append("미끄러지기 직전 조건과 미끄러짐 방향")
            elif wants_friction_limit_speed:
                # Friction is present and a limiting speed is requested, but the
                # direction/max/min may still be ambiguous. Let the banked-curve
                # template show a safe "speed-limit information needed" card
                # instead of blocking the whole family.
                pass
            elif asks_design or _has_required(cleaned, r"속도\s*조건|speed\s+condition|속도.*경사각.*관계|경사각.*관계|관계"):
                if not has_frictionless:
                    missing.append("마찰 없는 설계속도 문제인지, 또는 마찰 있는 한계속도 문제인지")
            else:
                missing.append("구하는 값이 설계속도/최대속도/최소속도 중 무엇인지")
        else:
            # Unknown road shape: still ask for all discriminating conditions.
            if not has_static_friction and not has_frictionless:
                missing.append("마찰 있음/없음과 마찰계수 μ_s")
            if not has_slip_limit and not asks_design:
                missing.append("최대/최소/설계속도 조건")

        if missing:
            # Preserve order while removing duplicates.
            missing = list(dict.fromkeys(missing))
            return decision(message, missing, "커브 주행")

    return None

def assess_information_sufficiency(text: str) -> InformationCompletenessDecision:
    cleaned = (text or "").strip()
    family = detect_problem_family_for_checklist(cleaned)
    checklist = input_checklist_for_text(cleaned)
    if not cleaned:
        return InformationCompletenessDecision(
            "insufficient",
            "문제를 입력해 주세요.",
            checklist,
            ["물체, 힘, 마찰 여부, 운동 방향, 구하려는 값을 문장으로 적어 주세요."],
            family,
        )
    figure_only = any(re.search(p, cleaned, re.I) for p in _FIGURE_ONLY_PATTERNS)
    meaningful_hits = sum(1 for p in _MEANINGFUL_PHYSICS_PATTERNS if re.search(p, cleaned, re.I))
    strong_short_physics = bool(re.search(r"(장력|tension|수직항력|normal)", cleaned, re.I) and re.search(r"(바닥|최저|최하|하단|bottom|lowest|lower)", cleaned, re.I))
    strong_short_rolling = bool(re.search(r"(원판|원통|바퀴|wheel|disk|cylinder)", cleaned, re.I) and re.search(r"(구르|굴러|roll|미끄러|slip|skid|스키딩)", cleaned, re.I))
    too_short = len(cleaned) < 14 and meaningful_hits < 2 and not strong_short_physics and not strong_short_rolling
    if figure_only and meaningful_hits < 3:
        return InformationCompletenessDecision(
            "insufficient",
            "현재 정보만으로는 풀이법을 판단할 수 없습니다. 그림 속 조건을 텍스트로 더 적어 주세요.",
            checklist,
            [
                "물체는 몇 개인가요?",
                "각 물체의 질량과 연결 구조는 무엇인가요?",
                "마찰, 경사각, 반지름, 힘 방향, 구하려는 값이 주어졌나요?",
            ],
            family,
        )
    if too_short:
        return InformationCompletenessDecision(
            "insufficient",
            "문제가 너무 짧습니다. 물체의 운동 조건, 힘, 마찰 여부, 회전 여부 등을 조금 더 적어 주세요.",
            checklist,
            ["그림 속 조건을 한 문장씩 풀어서 설명해 주세요."],
            family,
        )
    specific = _type_specific_insufficiency(cleaned, family, checklist)
    if specific is not None:
        return specific
    return InformationCompletenessDecision("sufficient", "분석을 진행할 수 있는 기본 단서가 있습니다.", [], [], family)


def beginner_scope_summary() -> list[str]:
    return [
        "이 앱은 자동 정답 생성기가 아니라 풀이 방향을 잡아주는 튜터형 도구입니다.",
        "정보가 부족한 문제는 억지로 공식을 추천하지 않고 추가 조건을 요구합니다.",
        "그림 정보는 텍스트로 옮겨 적어야 정확합니다.",
    ]
