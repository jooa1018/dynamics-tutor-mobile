from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, asdict
from typing import Any, Iterable, Mapping

from .semantic_normalizer import semantic_flags

EXAMPLE_LIBRARY: dict[str, str] = {
    "순수 구름": "Cylinder rolls without any slipping down the ramp. Find the acceleration.",
    "미끄럼 동반 회전": "The cylinder is rolling while slipping on the plane. Find the acceleration.",
    "원뿔진자": "A stone tied to a string moves in a horizontal circle making angle theta with vertical. Find angular speed.",
    "수직 원운동 장력": "A ball attached to a cord moves in a vertical loop. Find tension at the bottom.",
    "수직 원운동 수직항력": "원형 레일의 최하점에서 수직항력을 구하라.",
    "경사진 커브 최대속도": "Car on a sloped curve with friction, find highest speed before sliding up the bank.",
    "경사진 커브 최소속도": "경사각 theta인 커브에서 아래로 미끄러지지 않는 최소 speed를 구하라.",
    "수평면 블록-도르래": "Block A lies on a friction-free table and is tied to hanging block B over a pulley.",
    "위치벡터 미분": "particle position equals (3t, 2t^2); compute acceleration.",
    "탄환-회전강체 충돌": "A projectile strikes a hinged bar and sticks; determine angular speed after impact.",
}

INTERNAL_DEBUG_KEYS = {
    "template_id", "final_template_id", "raw_json", "raw_response", "ai_raw_response",
    "ai_confidence", "rule_confidence", "cache_hit", "fallback_log", "internal_flags",
    "forbidden_guard_raw", "consistency_check_raw", "model_name", "estimated_tokens",
    "estimated_cost", "traceback", "OPENAI_API_KEY", "api_key",
}

@dataclass(frozen=True)
class FBDContext:
    kind: str
    force_symbol: str | None = None
    show_friction: bool = False
    friction_label: str = ""
    rolling_mode: str = ""
    banked_speed_case: str = ""
    friction_direction: str = ""
    ambiguity_note: str = ""


def _blueprint(diagnosis: Any) -> Any:
    return getattr(diagnosis, "blueprint", diagnosis)


def _template_text(problem: str, diagnosis: Any) -> str:
    bp = _blueprint(diagnosis)
    model = getattr(diagnosis, "problem_model", None)
    return " ".join(str(x) for x in [
        problem,
        getattr(bp, "title", ""),
        getattr(bp, "final_template_id", ""),
        getattr(bp, "template_id", ""),
        getattr(model, "problem_type", ""),
    ]).lower()


def choose_fbd_context(problem: str, diagnosis: Any | None = None) -> FBDContext:
    sem = semantic_flags(problem)
    text = _template_text(problem, diagnosis) if diagnosis is not None else problem.lower()
    bp = _blueprint(diagnosis) if diagnosis is not None else None
    template_id = str(getattr(bp, "final_template_id", getattr(bp, "template_id", "")) or "").lower() if bp is not None else ""

    if sem.bullet_rotating_body_collision or "bullet_rotating_body_collision" in template_id:
        return FBDContext("bullet_rotating_body_collision")
    if sem.banked_curve or "banked_curve" in template_id:
        case = "max" if sem.max_speed or "max" in template_id else "min" if sem.min_speed or "min" in template_id else "ambiguous"
        direction = {
            "max": "최대속도: 위/바깥쪽으로 미끄러지려는 경향 → 마찰은 경사면 아래쪽 저항 방향",
            "min": "최소속도: 아래/안쪽으로 미끄러지려는 경향 → 마찰은 경사면 위쪽 저항 방향",
            "ambiguous": "최대/최소속도에 따라 마찰 방향이 달라집니다. 속도 한계 방향 확인 필요",
        }[case]
        return FBDContext("banked_curve", show_friction=sem.friction_present or case != "ambiguous", friction_label="f_s", banked_speed_case=case, friction_direction=direction)
    if sem.conical_explicit or sem.conical_structural or sem.conical_candidate or "conical" in template_id:
        return FBDContext("conical_pendulum", force_symbol="T")
    if sem.cartesian_position_vector or "cartesian" in template_id:
        return FBDContext("cartesian_vector")
    string_force_requested = bool(re.search(r"장력|tension|tensile|cord|rope|string|줄|끈|실", problem, re.I))
    normal_force_requested = bool(re.search(r"수직항력|법선반력|normal force|normal reaction|track force|rail force", problem, re.I))
    explicit_rail_track = bool(re.search(r"rail|track|레일|트랙|원형\s*궤도", problem, re.I))
    if string_force_requested and explicit_rail_track:
        return FBDContext("generic", ambiguity_note="rail/track은 수직항력 N, tension은 줄 장력 T를 뜻하므로 지지 방식 확인이 필요합니다.")
    if string_force_requested and re.search(r"vertical|수직|loop|원운동|원형|bottom|최저|최하|하단|바닥", text):
        return FBDContext("vertical_circle_string", force_symbol="T")
    if sem.track_support and (sem.bottom_position or "vertical_circle_track" in template_id or normal_force_requested):
        return FBDContext("vertical_circle_track", force_symbol="N")
    if sem.explicit_pure_rolling or "pure_rolling" in template_id:
        return FBDContext("pure_rolling", show_friction=True, friction_label="f_s", rolling_mode="pure_rolling")
    if sem.slip_present and (sem.rolling_word or sem.rotation_word or "sliding_rotation" in template_id):
        return FBDContext("sliding_rotation", show_friction=True, friction_label="f_k", rolling_mode="sliding_rotation")
    if (sem.horizontal_table or re.search(r"table|테이블|수평면|horizontal", problem, re.I)) and (sem.hanging_mass or re.search(r"hanging|매달", problem, re.I)):
        if sem.frictionless:
            return FBDContext("block_pulley", force_symbol="T", show_friction=False, friction_label="f = 0", friction_direction="마찰 없음: FBD에 마찰력 화살표를 표시하지 않습니다.")
        if sem.friction_present:
            return FBDContext("block_pulley", force_symbol="T", show_friction=True, friction_label="f", friction_direction="마찰은 블록의 운동 또는 미끄러지려는 방향의 반대")
        return FBDContext("block_pulley", force_symbol="T", show_friction=False, friction_label="마찰 조건 확인 필요", ambiguity_note="테이블은 수평면으로 해석했으며, 마찰 유무가 불명확하면 확인이 필요합니다.")
    if re.search(r"incline|경사면", problem, re.I):
        return FBDContext("incline", show_friction=not sem.frictionless, friction_label="f" if not sem.frictionless else "f = 0")
    return FBDContext("generic")


def public_student_payload(diagnosis: Any) -> dict[str, Any]:
    bp = _blueprint(diagnosis)
    model = getattr(diagnosis, "problem_model", None)
    payload = {
        "problem_type": getattr(model, "problem_type", ""),
        "title": getattr(bp, "title", ""),
        "evidence": getattr(bp, "evidence_phrases", []),
        "fbd_forces": getattr(bp, "fbd_forces", []),
        "coordinate_guide": getattr(bp, "coordinate_guide", []),
        "applicable_equations": getattr(bp, "applicable_equations", []) or getattr(bp, "governing_equations", []),
        "not_applicable_equations": getattr(bp, "not_applicable_equations", []),
        "cautions": getattr(bp, "cautions", []) or getattr(bp, "warnings", []),
        "steps": getattr(bp, "next_steps", []),
        "ambiguity_notes": getattr(bp, "ambiguity_notes", []),
    }
    return payload


def assert_no_student_debug_leak(payload: Mapping[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    leaked = [key for key in INTERNAL_DEBUG_KEYS if key.lower() in serialized]
    if leaked:
        raise AssertionError(f"student payload leaked internal debug keys: {leaked}")


def unique_equation_sections(applicable: Iterable[str], blocked: Iterable[str]) -> tuple[list[str], list[str]]:
    app = [str(x).strip() for x in applicable if str(x).strip()]
    block = [str(x).strip() for x in blocked if str(x).strip()]
    app_norm = {_normalize_equation(x) for x in app}
    filtered_block = [x for x in block if _normalize_equation(x) not in app_norm]
    return app, filtered_block


def _normalize_equation(text: str) -> str:
    out = re.sub(r"\s+", "", text.lower())
    out = out.replace("적용불가", "").replace("사용불가", "").replace("금지", "")
    return out


def build_markdown_export(problem: str, solution: str, diagnosis: Any) -> str:
    payload = public_student_payload(diagnosis)
    app, block = unique_equation_sections(payload["applicable_equations"], payload["not_applicable_equations"])
    lines = [
        "# DynaTutor 풀이 진단 요약", "", "## 문제", problem.strip() or "(입력 없음)", "",
        "## 문제 유형", str(payload["problem_type"]), "", "## FBD / 좌표축",
    ]
    lines.extend([f"- {x}" for x in payload["fbd_forces"] or ["기록 없음"]])
    lines.extend(["", "## 적용식"])
    lines.extend([f"- {x}" for x in app or ["기록 없음"]])
    lines.extend(["", "## 이 문제에서 쓰면 안 되는 식"])
    lines.extend([f"- {x}" for x in block or ["해당 없음"]])
    lines.extend(["", "## 단계별 풀이"])
    lines.extend([f"{i}. {x}" for i, x in enumerate(payload["steps"] or ["적용식과 조건을 먼저 확인합니다."], 1)])
    if solution.strip():
        lines.extend(["", "## 학생 풀이", solution.strip()])
    return "\n".join(lines)


def build_html_export(problem: str, solution: str, diagnosis: Any) -> str:
    md = build_markdown_export(problem, solution, diagnosis)
    return "<!doctype html><html lang='ko'><meta charset='utf-8'><title>DynaTutor Summary</title><body>" + html.escape(md).replace("\n", "<br>") + "</body></html>"


def build_equations_only_export(diagnosis: Any) -> str:
    payload = public_student_payload(diagnosis)
    app, block = unique_equation_sections(payload["applicable_equations"], payload["not_applicable_equations"])
    return "[적용식]\n" + "\n".join(app or ["기록 없음"]) + "\n\n[비적용식]\n" + "\n".join(block or ["해당 없음"])


def friendly_error_message(area: str) -> str:
    table = {
        "ai": "AI 피드백을 불러오지 못했습니다. 규칙 기반 진단 결과는 정상적으로 표시됩니다. 잠시 후 다시 시도하거나 API 설정을 확인해주세요.",
        "save": "저장에 실패했습니다. 다시 시도해 주세요.",
        "export": "내보내기에 실패했습니다. 잠시 후 다시 시도해 주세요.",
        "empty": "문제를 입력해 주세요.",
        "short": "문제가 조금 짧습니다. 조건을 더 입력하면 더 정확히 분석할 수 있습니다.",
    }
    return table.get(area, "요청을 처리하지 못했습니다. 입력 조건을 확인한 뒤 다시 시도해주세요.")


def to_jsonable(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    return dict(obj)

# ---------------------------------------------------------------------------
# Beginner tutor explanations
# ---------------------------------------------------------------------------

def equation_explanation(equation: str) -> str:
    eq = str(equation)
    low = eq.lower().replace(" ", "")
    if "n_a=m_ag" in low or "n=mg" in low or "n_a = m_a" in eq:
        return "블록은 수직방향으로 움직이지 않으므로 수직방향 가속도는 0입니다. 위쪽 수직항력 N_A와 아래쪽 중력 m_Ag가 평형이므로 N_A = m_Ag입니다."
    if "f=μn" in low or "f=mun" in low or "f = μn" in low or "f = μN" in eq:
        return "접촉면에서 미끄러지고 있거나 미끄러지기 직전일 때 마찰력은 수직항력에 비례합니다. 운동마찰이면 f_k = μ_kN, 최대 정지마찰이면 f_s,max = μ_sN입니다."
    if "m_bg-t=m_ba" in low or "m_b g - t" in eq:
        return "매달린 물체 B를 아래쪽 양의 방향으로 잡으면 아래쪽 중력 m_Bg, 위쪽 장력 T가 작용하므로 ΣF = m_Ba에서 나오는 식입니다."
    if "t=m_aa" in low or "t = m_a" in eq or "t=m_a" in low:
        return "수평면의 블록 A에 수평방향 힘이 장력 T뿐이면, 그 방향 힘의 합이 m_Aa가 되어 T = m_Aa가 됩니다."
    if "t-mg=mv" in low or "t - mg" in eq:
        return "최저점에서 중심 방향은 위쪽입니다. 위쪽 장력 T에서 아래쪽 중력 mg를 빼면 중심방향 힘의 합이 되어 T - mg = mv²/R이 됩니다."
    if "n-mg=mv" in low or "n - mg" in eq:
        return "트랙 최저점에서는 중심 방향이 위쪽입니다. 레일의 수직항력 N이 위쪽, 중력 mg가 아래쪽이므로 N - mg = mv²/R입니다."
    if "v_g=ωr" in low or "v_g=omegar" in low or "v_g = ωr" in eq:
        return "접촉점에서 미끄럼이 없는 순수 구름에서는 접촉점의 상대속도가 0이므로 질량중심 속도와 회전 속도가 v_G = ωR로 연결됩니다."
    if "a_g=αr" in low or "a_g=alphar" in low or "a_g = αr" in eq:
        return "순수 구름 조건이 가속도에도 유지되면 접선방향 질량중심 가속도와 각가속도가 a_G = αR로 연결됩니다."
    if "σf" in eq or "sum f" in low or "ΣF" in eq or "ma_g" in low:
        return "먼저 FBD를 그리고 선택한 양의 방향으로 실제 힘들을 더합니다. 그 힘의 합이 질량과 가속도의 곱 ΣF = ma입니다."
    if "σm" in eq or "sum m" in low or "ΣM" in eq or "i_gα" in low or "i_g α" in eq:
        return "강체가 회전하면 기준점에 대한 토크의 합을 관성모멘트와 각가속도의 곱으로 연결합니다. 회전축과 부호를 먼저 정해야 합니다."
    if "t cosθ" in eq or "t cos" in low:
        return "원뿔진자에서는 수직방향 가속도가 0이므로 장력의 수직성분 T cosθ가 중력 mg와 평형을 이룹니다."
    if "t sinθ" in eq or "t sin" in low:
        return "원뿔진자에서는 장력의 수평성분 T sinθ가 원운동 중심 방향 힘이 되어 mω²r 또는 mv²/r과 같아집니다."
    if "h_o(before)" in low or "h_o" in low:
        return "고정축 충돌에서는 축 반력의 충격량 때문에 선운동량보다 고정점 O 기준 각운동량 보존을 먼저 확인합니다."
    if "f = 0" in eq or "f=0" in low:
        return "문제에서 마찰 없음, smooth, frictionless, neglect friction이 명시되면 접촉면의 마찰력은 0으로 둡니다."
    if "f_k" in eq or "μ_k" in eq:
        return "접촉점이 실제로 미끄러지면 정지마찰 구름 조건이 아니라 운동마찰 또는 미끄럼 마찰 모델을 써야 합니다."
    if "energy" in low or "t_1" in low or "v_1" in low or "mgh" in low:
        return "에너지식은 시작 상태와 끝 상태의 운동에너지·위치에너지·일을 비교하는 식입니다. 마찰이나 비보존력이 있으면 그 일을 포함해야 합니다."
    return "이 식은 선택한 물체의 FBD, 좌표축, 구속조건을 뉴턴 법칙이나 보존 법칙에 연결해 얻습니다. 힘 방향과 적용 조건을 함께 확인하세요."


def forbidden_explanation(equation: str) -> str:
    eq = str(equation)
    low = eq.lower()
    compact = re.sub(r"\s+", "", eq.lower())
    if "v_g=ωr" in compact or "a_g=αr" in compact or "v_g=omegar" in compact or "a_g=alphar" in compact or "순수 구름" in eq:
        return "접촉점에 미끄럼이 있으면 순수 구름 구속식은 일반적으로 성립하지 않습니다."
    if "f = μ" in eq or "f=μ" in low:
        return "마찰 없음이 명시된 문제에서는 마찰계수식 자체를 적용식으로 두면 안 됩니다."
    if "n" in eq and "장력" in eq:
        return "줄/끈 문제에서 물어보는 힘은 수직항력 N이 아니라 장력 T입니다."
    if "t" in low and "레일" in eq:
        return "레일/트랙 접촉력은 보통 장력 T가 아니라 수직항력 N으로 표시합니다."
    if "운동에너지 보존" in eq or "energy" in low:
        return "충돌이나 마찰 문제가 있으면 운동에너지가 항상 보존되는 것이 아닙니다."
    if "구심력" in eq and "별도" in eq:
        return "구심력은 새 힘이 아니라 중심 방향 실제 힘들의 합입니다."
    return "이 식은 현재 문제 조건과 맞지 않거나 추가 조건이 필요합니다. 적용 조건을 확인하세요."


def beginner_first_equation(applicable: Iterable[str]) -> str:
    for eq in applicable or []:
        s = str(eq).strip()
        if s:
            return s
    return "먼저 FBD를 그리고 ΣF = ma 또는 해당 유형의 핵심 원리를 세웁니다."
