from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol, Tuple

from .models import FeatureReport, ProblemModel, Recommendation, SolutionBlueprint
from .parser import normalize_text
from .semantic_normalizer import semantic_flags, normalize_symbols
from .template_rebuild import GPT_CANDIDATE_TO_TEMPLATE_ID, reconcile_and_rebuild, rebuild_from_template_id


AI_MODEL_DEFAULT = os.getenv("DYNAMICS_AI_MODEL", "gpt-4o-mini")
CACHE_PATH_DEFAULT = Path(os.getenv("DYNAMICS_AI_CACHE", "data/ai_assist_cache.json"))
LOG_PATH_DEFAULT = Path(os.getenv("DYNAMICS_AI_LOG", "data/gpt_call_log.jsonl"))

KNOWN_CANDIDATES = [
    "horizontal_block_hanging_mass",
    "inclined_block_hanging_mass",
    "massive_pulley",
    "banked_curve_frictionless",
    "banked_curve_with_friction_max_speed",
    "banked_curve_with_friction_min_speed",
    "conical_pendulum",
    "sliding_rotation",
    "pure_rolling",
    "vertical_circle_string_bottom",
    "vertical_circle_string_top",
    "vertical_circle_track_bottom",
    "frictionless_pulley_block",
    "cartesian_position_vector",
    "polar_motion",
    "bullet_rotating_body_collision",
    "collision_restitution",
    "general_planar_rigid_body",
    "ambiguous_or_insufficient_information",
]

GPT_ASSIST_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "primary_candidate",
        "secondary_candidates",
        "confidence",
        "detected_features",
        "evidence_phrases",
        "missing_information",
        "must_use_tags",
        "must_not_use_tags",
        "warnings",
    ],
    "properties": {
        "primary_candidate": {"type": "string", "enum": KNOWN_CANDIDATES},
        "secondary_candidates": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "detected_features": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "has_rolling": {"type": "boolean"},
                "has_slipping": {"type": "boolean"},
                "has_string": {"type": "boolean"},
                "has_track": {"type": "boolean"},
                "has_fixed_axis": {"type": "boolean"},
                "has_collision": {"type": "boolean"},
                "has_cartesian_vector": {"type": "boolean"},
                "has_polar_vector": {"type": "boolean"},
                "friction_mode": {"type": "string"},
            },
        },
        "evidence_phrases": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "missing_information": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "must_use_tags": {"type": "array", "items": {"type": "string"}, "maxItems": 12},
        "must_not_use_tags": {"type": "array", "items": {"type": "string"}, "maxItems": 12},
        "warnings": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
    },
}


@dataclass
class GPTAssistResult:
    primary_candidate: str = "ambiguous_or_insufficient_information"
    secondary_candidates: List[str] = field(default_factory=list)
    confidence: float = 0.0
    detected_features: Dict[str, Any] = field(default_factory=dict)
    evidence_phrases: List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)
    must_use_tags: List[str] = field(default_factory=list)
    must_not_use_tags: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "GPTAssistResult":
        primary = str(data.get("primary_candidate") or "ambiguous_or_insufficient_information")
        if primary not in KNOWN_CANDIDATES:
            primary = "ambiguous_or_insufficient_information"
        return cls(
            primary_candidate=primary,
            secondary_candidates=[str(x) for x in data.get("secondary_candidates", [])[:5]],
            confidence=float(data.get("confidence") or 0.0),
            detected_features=dict(data.get("detected_features") or {}),
            evidence_phrases=[str(x) for x in data.get("evidence_phrases", [])[:8]],
            missing_information=[str(x) for x in data.get("missing_information", [])[:8]],
            must_use_tags=[str(x) for x in data.get("must_use_tags", [])[:12]],
            must_not_use_tags=[str(x) for x in data.get("must_not_use_tags", [])[:12]],
            warnings=[str(x) for x in data.get("warnings", [])[:8]],
        )


@dataclass
class RuleConfidence:
    score: float
    reasons: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)


@dataclass
class AIAssistDecision:
    should_call: bool
    confidence: RuleConfidence
    reasons: List[str] = field(default_factory=list)


class GPTClient(Protocol):
    def __call__(self, payload: Dict[str, Any], schema: Dict[str, Any], model: str, max_output_tokens: int, temperature: float) -> Dict[str, Any]:
        ...


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


def _has_hangul(text: str) -> bool:
    return any("가" <= ch <= "힣" for ch in text)


def _has_ascii_word(text: str) -> bool:
    return any(("a" <= ch.lower() <= "z") for ch in text)


def estimate_rule_confidence(problem: str, features: FeatureReport, rec: Recommendation, model: ProblemModel, bp: SolutionBlueprint) -> RuleConfidence:
    text = normalize_text(problem)
    sem = semantic_flags(text)
    score = 0.58
    reasons: List[str] = []
    risk_flags: List[str] = []

    if model.problem_type and not model.problem_type.startswith("일반") and "정보 부족" not in model.problem_type and "가능성" not in model.problem_type:
        score += 0.23
        reasons.append("전용 물리 템플릿이 선택됨")
    if bp.applicable_equations:
        score += 0.08
        reasons.append("적용식이 구조화되어 있음")
    if bp.not_applicable_equations:
        score += 0.04
        reasons.append("비적용식/금지식이 분리되어 있음")
    if model.problem_type in {"마찰 없는 경사진 커브 문제", "위치 함수 기반 입자 운동학", "미끄럼을 동반한 구름 운동", "원뿔진자 원운동 문제"}:
        score += 0.06
        reasons.append("고신뢰 대표 구조로 판정됨")
    if "정보 부족" in model.problem_type or "가능성" in model.problem_type or bp.ambiguity_notes:
        score -= 0.22
        risk_flags.append("ambiguous_or_insufficient_information")
    if sem.slip_present and (sem.rolling_word or sem.rotation_word):
        score -= 0.05
        risk_flags.append("rolling_slipping_conflict")
    if sem.frictionless and (features.cues.get("friction") or "μ" in problem or "mu" in problem.lower()):
        score -= 0.08
        risk_flags.append("friction_present_and_absent_conflict")
    if sem.cartesian_position_vector and sem.polar_motion:
        score -= 0.14
        risk_flags.append("cartesian_polar_conflict")
    if sem.string_support and sem.track_support:
        score -= 0.11
        risk_flags.append("string_track_force_conflict")
    if sem.banked_curve and not (sem.max_speed or sem.min_speed or sem.frictionless or sem.friction_present):
        score -= 0.10
        risk_flags.append("banked_curve_direction_or_friction_unclear")
    if sem.conical_candidate and not (sem.conical_explicit or sem.conical_structural):
        score -= 0.16
        risk_flags.append("conical_pendulum_candidate_unclear")
    if _has_hangul(problem) and _has_ascii_word(problem):
        score -= 0.05
        risk_flags.append("mixed_korean_english")
    if len(problem.strip()) < 28:
        score -= 0.12
        risk_flags.append("short_input_missing_conditions")
    clear_template = bool(model.problem_type and not model.problem_type.startswith("일반") and "정보 부족" not in model.problem_type and "가능성" not in model.problem_type)
    if rec.confidence == "낮음" and not clear_template:
        score -= 0.12
        risk_flags.append("low_strategy_confidence")
    elif rec.confidence == "낮음" and clear_template:
        # 전략 점수표가 낮더라도 전용 구조 템플릿이 확정된 경우에는
        # 불필요한 GPT 호출을 줄입니다.
        score += 0.04
        reasons.append("전략 점수는 낮지만 전용 구조 템플릿이 우선됨")
    if any("적용 불가" in x for x in bp.not_applicable_equations) and not bp.applicable_equations:
        score -= 0.10
        risk_flags.append("forbidden_formula_risk_without_clear_applicable_formula")

    score = max(0.0, min(0.98, score))
    if score >= 0.90:
        reasons.append("규칙 기반 판별로 충분히 확실함")
    elif score >= 0.70:
        reasons.append("대체로 분류되었지만 일부 위험 단서 확인 필요")
    else:
        reasons.append("분류 신뢰도가 낮아 AI 보조 판별 권장")
    return RuleConfidence(score=round(score, 3), reasons=_uniq(reasons), risk_flags=_uniq(risk_flags))


def decide_ai_assist(problem: str, features: FeatureReport, rec: Recommendation, model: ProblemModel, bp: SolutionBlueprint) -> AIAssistDecision:
    confidence = estimate_rule_confidence(problem, features, rec, model, bp)
    sem = semantic_flags(problem)
    reasons: List[str] = []
    if confidence.score < 0.70:
        reasons.append("confidence < 0.70")
    elif confidence.score < 0.90 and confidence.risk_flags:
        reasons.append("0.70 ≤ confidence < 0.90이고 위험 단서 존재")
    for flag in confidence.risk_flags:
        reasons.append(flag)
    # 사용자가 요청한 자동 호출 조건: 특정 위험 조합은 점수가 조금 높아도 호출 후보입니다.
    if sem.slip_present and sem.rolling_word:
        reasons.append("순수 구름/미끄럼 동반 회전 충돌 가능성")
    if sem.string_support and sem.track_support:
        reasons.append("줄/트랙 힘 이름 충돌 가능성")
    if sem.frictionless and (features.cues.get("friction") or "μ" in problem or "mu" in problem.lower()):
        reasons.append("마찰 있음/없음 단서 충돌")
    if sem.cartesian_position_vector and sem.polar_motion:
        reasons.append("직교좌표/극좌표 단서 충돌")
    if sem.bullet_rotating_body_collision and "탄환" not in model.problem_type and "회전강체" not in model.problem_type:
        reasons.append("projectile/bullet + embedded + fixed axis 회전충돌 고위험")
    if sem.bottom_position and sem.string_support and ("최저점" not in model.problem_type):
        reasons.append("줄/로프 수직 원운동 최저점 고위험")
    if sem.frictionless and ("마찰 없는" not in model.problem_type) and (sem.horizontal_table or sem.pulley or sem.friction_present):
        reasons.append("마찰 없음 단서 우선 확인 필요")
    if sem.slip_present and ("미끄럼" not in model.problem_type):
        reasons.append("미끄럼 동반 회전/구름 고위험")
    if sem.cartesian_position_vector and "위치" not in model.problem_type:
        reasons.append("i/j 위치벡터 고위험")
    if sem.conical_candidate and "원뿔진자" not in model.problem_type:
        reasons.append("원뿔진자 구조 후보 고위험")
    if _has_hangul(problem) and _has_ascii_word(problem):
        reasons.append("한국어/영어 혼합 입력")
    forced_risk = (
        bool(sem.slip_present and (sem.rolling_word or sem.rotation_word))
        or bool(sem.string_support and sem.track_support)
        or bool(sem.cartesian_position_vector and sem.polar_motion)
        or bool(sem.bullet_rotating_body_collision and "회전강체" not in model.problem_type)
        or bool(sem.bottom_position and sem.string_support and "최저점" not in model.problem_type)
        or bool(sem.conical_candidate and "원뿔진자" not in model.problem_type)
    )
    should_call = (bool(reasons) and confidence.score < 0.92) or forced_risk
    return AIAssistDecision(should_call=should_call, confidence=confidence, reasons=_uniq(reasons))


def _cache_key(problem: str, features: FeatureReport, rec: Recommendation, model_name: str) -> str:
    payload = {
        "problem": normalize_symbols(normalize_text(problem)),
        "cues": {k: bool(v) for k, v in sorted(features.cues.items())},
        "requested_quantity": features.requested_quantity,
        "rec_primary": rec.primary,
        "model": model_name,
        "schema_version": 2,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _read_cache(path: Path) -> Dict[str, Any]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {}


def _write_cache(path: Path, cache: Dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _append_log(path: Path, record: Dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


def build_ai_payload(problem: str, features: FeatureReport, rec: Recommendation, model_obj: ProblemModel, bp: SolutionBlueprint, decision: AIAssistDecision) -> Dict[str, Any]:
    sem = semantic_flags(problem)
    return {
        "task": "classify_dynamics_problem_for_template_selection_only",
        "instruction": "Return only JSON matching schema. Do not invent final equations. Select candidate tags, evidence, missing info, and must_not_use_tags.",
        "problem": problem[:1600],
        "rule_engine": {
            "problem_type": model_obj.problem_type,
            "template_title": bp.title,
            "primary_strategy": rec.primary,
            "confidence_score": decision.confidence.score,
            "risk_flags": decision.confidence.risk_flags,
            "detected_cues": [k for k, v in features.cues.items() if v][:30],
            "applicable_equations": bp.applicable_equations[:10],
            "not_applicable_equations": bp.not_applicable_equations[:10],
        },
        "semantic_flags": {
            "frictionless": sem.frictionless,
            "friction_present": sem.friction_present,
            "slip_present": sem.slip_present,
            "explicit_pure_rolling": sem.explicit_pure_rolling,
            "rolling_word": sem.rolling_word,
            "rotation_word": sem.rotation_word,
            "string_support": sem.string_support,
            "track_support": sem.track_support,
            "cartesian_position_vector": sem.cartesian_position_vector,
            "polar_motion": sem.polar_motion,
            "bullet_rotating_body_collision": sem.bullet_rotating_body_collision,
            "banked_curve": sem.banked_curve,
            "max_speed": sem.max_speed,
            "min_speed": sem.min_speed,
        },
        "allowed_candidates": KNOWN_CANDIDATES,
        "allowed_tags": [
            "pure_rolling_constraint",
            "sliding_rotation",
            "kinetic_friction",
            "sum_forces",
            "sum_moments_about_center",
            "tension_force",
            "normal_force",
            "cartesian_differentiation",
            "polar_kinematics",
            "angular_momentum_about_fixed_axis",
            "linear_momentum_only",
            "banked_curve_friction",
            "flat_curve_friction",
            "conical_pendulum",
        ],
    }


def default_openai_client(payload: Dict[str, Any], schema: Dict[str, Any], model: str, max_output_tokens: int, temperature: float) -> Dict[str, Any]:
    try:
        from openai import OpenAI  # type: ignore
    except Exception as exc:
        raise RuntimeError("openai 패키지가 설치되어 있지 않습니다. `pip install openai` 후 다시 시도하세요.") from exc

    client = OpenAI()
    system = (
        "You are a dynamics problem classifier. You do not solve numerically. "
        "Return compact JSON only. Choose template tags and forbidden tags. "
        "Never create final physics equations outside the known tags."
    )
    user = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    try:
        response = client.responses.create(
            model=model,
            input=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            text={"format": {"type": "json_schema", "name": "dynamics_ai_assist", "schema": schema, "strict": True}},
        )
        raw = getattr(response, "output_text", None) or ""
    except TypeError:
        # SDK 버전 차이를 위한 보수적 fallback. 그래도 JSON만 요구합니다.
        response = client.responses.create(
            model=model,
            input=[{"role": "system", "content": system}, {"role": "user", "content": user + "\nReturn JSON only."}],
            max_output_tokens=max_output_tokens,
        )
        raw = getattr(response, "output_text", None) or ""
    if not raw:
        raise RuntimeError("OpenAI 응답에서 output_text를 읽지 못했습니다.")
    return json.loads(raw)


def _contains_equation(items: List[str], needle: str) -> bool:
    compact = lambda s: s.replace(" ", "").replace("·", "")
    n = compact(needle)
    return any(n in compact(x) for x in items)


def _remove_applicable_by_tag(bp: SolutionBlueprint, tag: str) -> List[str]:
    removed: List[str] = []
    if tag == "pure_rolling_constraint":
        patterns = ["v_G = ωR", "a_G = αR", "v=ωR", "a=αR"]
    elif tag == "linear_momentum_only":
        patterns = ["m1v1i + m2v2i", "m_1v_1", "(m_1+m_2)v"]
    elif tag == "flat_curve_friction":
        patterns = ["μ_s ≥ v²/(gR)", "N = mg", "f_s = mv²/R"]
    elif tag == "polar_kinematics":
        patterns = ["e_r", "e_θ", "r theta_dot", "r_dot e_r"]
    else:
        patterns = []
    keep: List[str] = []
    for eq in bp.applicable_equations:
        if any(p.replace(" ", "") in eq.replace(" ", "") for p in patterns):
            removed.append(eq)
        else:
            keep.append(eq)
    bp.applicable_equations = keep
    bp.governing_equations = list(keep)
    return removed


def apply_forbidden_formula_guard(bp: SolutionBlueprint, problem: str, ai_result: Optional[GPTAssistResult] = None) -> SolutionBlueprint:
    """규칙 기반 안전장치. GPT 결과보다 항상 우선합니다."""
    sem = semantic_flags(problem)
    must_not_tags = set(ai_result.must_not_use_tags if ai_result else [])
    if sem.slip_present and (sem.rolling_word or sem.rotation_word):
        must_not_tags.add("pure_rolling_constraint")
    if sem.bullet_rotating_body_collision:
        must_not_tags.add("linear_momentum_only")
    if sem.cartesian_position_vector:
        must_not_tags.add("polar_kinematics")
    if sem.banked_curve and (sem.max_speed or sem.min_speed or sem.friction_present):
        must_not_tags.add("flat_curve_friction")

    for tag in sorted(must_not_tags):
        removed = _remove_applicable_by_tag(bp, tag)
        for eq in removed:
            bp.not_applicable_equations.append(f"{eq} : GPT/규칙 안전장치에 의해 적용식에서 제거")
        if tag == "pure_rolling_constraint":
            bp.not_applicable_equations.extend(["v_G = ωR : 미끄럼 단서가 있으면 적용식으로 사용 금지", "a_G = αR : 미끄럼 단서가 있으면 적용식으로 사용 금지"])
            bp.cautions.append("미끄럼 단서가 있으므로 순수 구름 조건은 적용식이 아니라 비적용식으로만 표시합니다.")
        if tag == "linear_momentum_only":
            bp.not_applicable_equations.append("단순 1차원 선운동량 보존식만 우선 출력 금지: 회전축 충돌은 각운동량 보존을 우선 확인")
            bp.cautions.append("회전축 충돌에서는 축 반력의 외부 충격량 때문에 선운동량 보존이 일반적으로 성립하지 않을 수 있습니다.")
        if tag == "polar_kinematics":
            bp.not_applicable_equations.append("극좌표 가속도식 : i, j 위치벡터가 명시된 문제에서는 우선 적용 금지")
        if tag == "flat_curve_friction":
            bp.not_applicable_equations.append("평평한 커브 마찰계수 식 : 경사진 커브 문제에서는 적용식으로 사용 금지")

    if sem.frictionless:
        # f=μN이 적용식에 남아 있으면 제거하고 f=0을 추가합니다.
        keep = []
        for eq in bp.applicable_equations:
            if "μN" in eq or "μm" in eq or "mu" in eq.lower():
                bp.not_applicable_equations.append(f"{eq} : 마찰 없음/무시 조건이 있으므로 적용식에서 제거")
            else:
                keep.append(eq)
        bp.applicable_equations = _uniq([*keep, "f = 0"])
        bp.governing_equations = list(bp.applicable_equations)
        bp.cautions.append("마찰 없음/무시 조건은 μ 또는 마찰계수 언급보다 우선합니다.")
    if sem.string_support and "수직 원운동" in (bp.title + " " + " ".join(bp.applicable_equations)):
        for eq in list(bp.applicable_equations):
            if eq.startswith("N ") or "N - mg" in eq or "mg + N" in eq:
                bp.applicable_equations.remove(eq)
                bp.not_applicable_equations.append(f"{eq} : 줄/끈/로프 문제에서는 힘 이름을 장력 T로 우선 사용")
        bp.governing_equations = list(bp.applicable_equations)
    bp.not_applicable_equations = _uniq(bp.not_applicable_equations)
    bp.cautions = _uniq(bp.cautions)
    bp.warnings = _uniq([*bp.warnings, *bp.cautions])
    try:
        from .consistency_guard import apply_final_consistency_guard
        apply_final_consistency_guard(bp, problem)
    except Exception:
        # Guard failure must never break the rule-based fallback path.
        pass
    return bp


def apply_gpt_assist_result(bp: SolutionBlueprint, model_obj: ProblemModel, ai: GPTAssistResult) -> None:
    """GPT는 식을 직접 쓰지 않고 후보/태그만 제안합니다.

    후보 자체는 뒤의 reconciliation 단계에서 검증 후 템플릿 재생성에 사용됩니다.
    이 함수는 투명성/모호성 정보만 기록합니다.
    """
    bp.ai_primary_candidate = ai.primary_candidate  # type: ignore[attr-defined]
    bp.ai_confidence = ai.confidence  # type: ignore[attr-defined]
    bp.ai_secondary_candidates = ai.secondary_candidates  # type: ignore[attr-defined]
    bp.ai_detected_features = ai.detected_features  # type: ignore[attr-defined]
    bp.ai_must_use_tags = ai.must_use_tags  # type: ignore[attr-defined]
    bp.ai_must_not_use_tags = ai.must_not_use_tags  # type: ignore[attr-defined]
    if ai.confidence < 0.50:
        bp.ambiguity_notes.append("AI 보조 판별 confidence가 낮아 하나의 유형으로 확정하지 않습니다.")
    if ai.secondary_candidates:
        bp.ambiguity_notes.append("AI 보조 후보: " + ", ".join(ai.secondary_candidates[:4]))
    for item in ai.missing_information:
        bp.ambiguity_notes.append("AI 보조 판별 — 추가 확인 필요: " + item)
    for warning in ai.warnings:
        bp.cautions.append("AI 보조 판별: " + warning)


def maybe_apply_ai_assist(
    problem: str,
    features: FeatureReport,
    rec: Recommendation,
    model_obj: ProblemModel,
    bp: SolutionBlueprint,
    *,
    enable_api: bool = True,
    model_name: str = AI_MODEL_DEFAULT,
    client: Optional[GPTClient] = None,
    cache_path: Path = CACHE_PATH_DEFAULT,
    log_path: Path = LOG_PATH_DEFAULT,
    max_output_tokens: int = 550,
    temperature: float = 0.1,
) -> SolutionBlueprint:
    """선택적 GPT mini 보조 판별을 적용합니다.

    - 확실한 문제는 API를 호출하지 않습니다.
    - API key가 없거나 호출 실패 시 규칙 엔진으로 안전하게 fallback합니다.
    - GPT 결과는 JSON Schema 기반 구조화 데이터로만 받고, 최종 식 선택은 guard가 검증합니다.
    """
    decision = decide_ai_assist(problem, features, rec, model_obj, bp)
    bp.classification_confidence = decision.confidence.score  # type: ignore[attr-defined]
    bp.classification_risk_flags = decision.confidence.risk_flags  # type: ignore[attr-defined]
    bp.ai_assist_status = "not_needed"  # type: ignore[attr-defined]
    bp.ai_call_reasons = decision.reasons  # type: ignore[attr-defined]
    bp.ai_cache_hit = False  # type: ignore[attr-defined]
    bp.ai_model = model_name  # type: ignore[attr-defined]

    if not decision.should_call:
        bp.cautions.append("규칙 기반 판별로 충분히 확실합니다. AI 보조 판별은 호출하지 않았습니다.")
        return apply_forbidden_formula_guard(bp, problem)

    if not enable_api:
        bp.ai_assist_status = "disabled_fallback"  # type: ignore[attr-defined]
        bp.cautions.append("표현이 애매하지만 AI 보조 판별이 비활성화되어 규칙 기반 결과를 사용합니다.")
        return apply_forbidden_formula_guard(bp, problem)

    if client is None and not os.getenv("OPENAI_API_KEY"):
        bp.ai_assist_status = "no_api_key_fallback"  # type: ignore[attr-defined]
        bp.cautions.append("표현이 애매하지만 OPENAI_API_KEY가 없어 규칙 기반 결과를 사용합니다.")
        return apply_forbidden_formula_guard(bp, problem)

    key = _cache_key(problem, features, rec, model_name)
    cache = _read_cache(cache_path)
    raw_result: Optional[Dict[str, Any]] = None
    if key in cache:
        raw_result = cache[key].get("result")
        bp.ai_cache_hit = True  # type: ignore[attr-defined]
        bp.ai_assist_status = "cache_hit"  # type: ignore[attr-defined]
    else:
        payload = build_ai_payload(problem, features, rec, model_obj, bp, decision)
        start = time.time()
        try:
            caller = client or default_openai_client
            raw_result = caller(payload, GPT_ASSIST_JSON_SCHEMA, model_name, max_output_tokens, temperature)
            cache[key] = {"created_at": time.time(), "payload_hash": key, "result": raw_result}
            _write_cache(cache_path, cache)
            bp.ai_assist_status = "called"  # type: ignore[attr-defined]
            _append_log(log_path, {
                "ts": time.time(),
                "model": model_name,
                "cache_hit": False,
                "latency_sec": round(time.time() - start, 3),
                "prompt_chars": len(json.dumps(payload, ensure_ascii=False)),
                "output_chars": len(json.dumps(raw_result, ensure_ascii=False)),
                "decision_reasons": decision.reasons,
            })
        except Exception as exc:
            bp.ai_assist_status = "error_fallback"  # type: ignore[attr-defined]
            bp.cautions.append(f"AI 보조 판별 실패, 규칙 기반 결과를 사용함: {type(exc).__name__}")
            _append_log(log_path, {"ts": time.time(), "model": model_name, "error": type(exc).__name__, "decision_reasons": decision.reasons})
            return apply_forbidden_formula_guard(bp, problem)

    try:
        ai = GPTAssistResult.from_json(raw_result or {})
    except Exception as exc:
        bp.ai_assist_status = "invalid_json_fallback"  # type: ignore[attr-defined]
        bp.cautions.append(f"AI 보조 판별 JSON schema 불일치, 규칙 기반 결과를 사용함: {type(exc).__name__}")
        return apply_forbidden_formula_guard(bp, problem)

    apply_gpt_assist_result(bp, model_obj, ai)
    rebuild = reconcile_and_rebuild(
        problem=problem,
        model=model_obj,
        bp=bp,
        ai_candidate=ai.primary_candidate,
        ai_confidence=ai.confidence,
        detected_features=ai.detected_features,
        rule_confidence=decision.confidence.score,
        risk_flags=decision.confidence.risk_flags,
    )
    bp.ai_rebuild_applied = rebuild.applied  # type: ignore[attr-defined]
    bp.final_template_id = rebuild.final_template_id  # type: ignore[attr-defined]
    bp.reconciliation_reason = rebuild.reason  # type: ignore[attr-defined]
    if rebuild.applied:
        bp.cautions.append(f"AI 후보를 검증해 최종 템플릿을 {rebuild.final_template_id}로 재생성했습니다.")
    else:
        bp.cautions.append(f"AI 후보는 기록했지만 템플릿 재선택 기준을 만족하지 않아 기존/후보를 함께 검토합니다: {rebuild.reason}")
    bp.cautions.append("표현이 애매하여 AI 보조 판별을 사용했습니다. 최종 적용식은 규칙 엔진의 금지식 검사를 통과한 항목만 표시합니다.")
    guarded = apply_forbidden_formula_guard(bp, problem, ai)
    _append_log(log_path, {
        "ts": time.time(),
        "input_hash": key,
        "model": model_name,
        "cache_hit": bool(getattr(guarded, "ai_cache_hit", False)),
        "rule_candidate": getattr(guarded, "rule_template_id", model_obj.problem_type),
        "rule_confidence": decision.confidence.score,
        "trigger_reason": decision.reasons,
        "ai_called": True,
        "ai_candidate": ai.primary_candidate,
        "ai_confidence": ai.confidence,
        "final_template": getattr(guarded, "final_template_id", guarded.title),
        "rebuild_applied": bool(getattr(guarded, "ai_rebuild_applied", False)),
        "fallback_used": False,
        "estimated_prompt_chars": len(problem),
        "estimated_output_chars": len(json.dumps(raw_result or {}, ensure_ascii=False)),
    })
    return guarded
