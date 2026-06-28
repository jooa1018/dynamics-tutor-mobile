from __future__ import annotations

import re
from typing import Iterable, Sequence

from .semantic_normalizer import semantic_flags


def _uniq(items: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not item:
            continue
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out




def _semantic_unique(items: Iterable[str]) -> list[str]:
    """Deduplicate repeated beginner warnings/formulas by meaning, not exact wording."""
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not item:
            continue
        text = str(item).strip()
        compact = re.sub(r"\s+", "", text.lower())
        if "v_g=ωr" in compact or "v_g=omegar" in compact:
            key = "forbid_vg_omega_r" if ("불가" in text or "금지" in text or "사용" in text) else "vg_omega_r"
        elif "a_g=αr" in compact or "a_g=alphar" in compact:
            key = "forbid_ag_alpha_r" if ("불가" in text or "금지" in text or "사용" in text) else "ag_alpha_r"
        elif "f=μ" in compact or "f_k=μ_k" in compact or "f=mu" in compact:
            key = "friction_formula_" + ("forbid" if ("금지" in text or "불가" in text) else "use")
        elif "구심력" in text and "별도" in text:
            key = "centripetal_not_separate_force"
        else:
            key = re.sub(r"[\s:：·,.;]+", "", compact)
        if key not in seen:
            out.append(text)
            seen.add(key)
    return out

def _contains_any(text: str, needles: Sequence[str]) -> bool:
    low = text.lower()
    return any(n.lower() in low for n in needles)


def apply_final_consistency_guard(bp, problem: str) -> None:
    """Final output-level consistency and forbidden-formula guard.

    This is intentionally conservative: it never creates an unverified numeric
    answer, but it removes equations from the applicable area when the semantic
    flags prove that those equations belong only in the not-applicable area.
    """
    sem = semantic_flags(problem)
    app = list(getattr(bp, "applicable_equations", []) or getattr(bp, "governing_equations", []) or [])
    not_app = list(getattr(bp, "not_applicable_equations", []) or [])
    cautions = list(getattr(bp, "cautions", []) or [])
    ambiguity = list(getattr(bp, "ambiguity_notes", []) or [])

    def remove_app_if(pred):
        nonlocal app
        app = [eq for eq in app if not pred(eq)]

    def add_app(eq: str) -> None:
        if eq not in app:
            app.append(eq)

    def add_not(eq: str) -> None:
        if eq not in not_app:
            not_app.append(eq)

    def add_caution(msg: str) -> None:
        if msg not in cautions:
            cautions.append(msg)

    # Rolling/contact slip guard. Negated slip signals have already been resolved
    # by semantic_flags: explicit_pure_rolling and slip_present are mutually safe.
    if sem.explicit_pure_rolling and not sem.slip_present:
        add_app("v_G = ωR")
        add_app("a_G = αR")
        remove_app_if(lambda eq: "적용 불가" in eq and ("v_G = ωR" in eq or "a_G = αR" in eq))
        not_app = [eq for eq in not_app if not (("v_G = ωR" in eq or "a_G = αR" in eq) and "적용" in eq)]
        cautions = [c for c in cautions if not ((("미끄럼" in c) or ("미끄러" in c)) and ("v_G = ωR" in c or "a_G = αR" in c))]
        add_caution("순수 구름 조건이 명시되어 있으므로 v_G = ωR, a_G = αR을 사용할 수 있습니다.")
    if sem.slip_present and (sem.rolling_word or sem.rotation_word):
        remove_app_if(lambda eq: "v_G = ωR" in eq or "a_G = αR" in eq or "mgh = 1/2mv_G²" in eq)
        add_app("ΣF = ma_G")
        add_app("ΣM_G = I_Gα")
        add_app("f_k = μ_kN")
        add_not("v_G = ωR : 미끄럼이 있으면 적용식으로 사용 불가")
        add_not("a_G = αR : 미끄럼이 있으면 적용식으로 사용 불가")
        if re.search(r"contact point|point of contact|접촉점", problem, flags=re.I):
            add_caution("접촉점 미끄럼 단서가 있으므로 순수 구름 조건을 적용식으로 쓰면 안 됩니다.")

    # Banked-curve slip is not rolling-contact slip; suppress irrelevant rolling guard.
    if sem.banked_curve and not (sem.rolling_word or re.search(r"wheel|cylinder|disk|원통|원반|바퀴", problem, flags=re.I)):
        not_app = [eq for eq in not_app if not ("v_G = ωR" in eq or "a_G = αR" in eq)]
        cautions = [c for c in cautions if not ("구름" in c or "v_G = ωR" in c or "a_G = αR" in c)]

    # Frictionless dominates rough/mu/coefficient wording.
    if sem.frictionless:
        remove_app_if(lambda eq: any(x in eq for x in ["f = μN", "f = μN_A", "f = μ_sN", "f_s ≤ μ_sN", "μ_s ≥ v²/(gR)", "f_k = μ_kN", "μ_kN"]))
        add_app("f = 0")
        add_not("f = μN : 마찰 없음/무시 조건에서는 최종 적용식으로 사용 금지")

    # Simple frictionless incline support. This is still a scaffold, not a full numeric solver.
    if sem.frictionless and re.search(r"경사면|incline|inclined\s+plane", problem, flags=re.I) and re.search(r"theta|θ|경사각|각도|\d+\s*(?:deg|degree|°)", problem, flags=re.I):
        add_app("mg sinθ = ma")
        add_app("a = g sinθ")
        add_not("f = μN : 마찰 없는 경사면에서는 사용 금지")

    # Coordinate-system split.
    if sem.cartesian_position_vector:
        remove_app_if(lambda eq: any(x in eq for x in ["e_r", "e_θ", "e_theta", "theta_dot", "thetȧ", "r theta_dot"] ))
        add_app("r(t) = x(t)i + y(t)j")
        add_app("v(t) = dr/dt")
        add_app("a(t) = d²r/dt²")
        add_not("극좌표 가속도식 : i, j 또는 <x,y> 직교좌표 위치벡터에서는 우선 적용 금지")
    elif sem.polar_motion:
        # Avoid a polar result with only Cartesian formulas.
        if not any("e_r" in eq or "e_θ" in eq or "theta" in eq for eq in app):
            add_app("v = r_dot e_r + r theta_dot e_theta")
            add_app("a = (r_ddot - r theta_dot²)e_r + (r theta_ddot + 2r_dot theta_dot)e_theta")

    # Force-symbol guard for vertical circle.
    asks_tension = re.search(r"장력|tension|tensile force|string force|rope force|cord force", problem, flags=re.I)
    asks_normal = re.search(r"수직항력|normal force|normal reaction|track force|rail force", problem, flags=re.I)
    vertical_circle_context = re.search(r"수직\s*원|vertical\s+(?:circle|loop)|원형\s*(?:레일|트랙|궤도)|circular\s+(?:rail|track)", problem, flags=re.I)
    if sem.bottom_position and vertical_circle_context:
        explicit_track_support = re.search(r"rail|track|레일|트랙|원형\s*(?:레일|트랙|궤도)", problem, flags=re.I)
        if (sem.string_support or asks_tension) and not (explicit_track_support or asks_normal):
            remove_app_if(lambda eq: "N - mg" in eq or "N = mg" in eq or "트랙/레일 문제라면" in eq)
            add_app("T - mg = mv²/R")
            add_app("T = mg + mv²/R")
            add_not("N - mg = mv²/R : 줄/끈 장력 문제에서는 N이 아니라 T를 사용")
        elif (explicit_track_support or asks_normal) and not asks_tension:
            remove_app_if(lambda eq: "T - mg" in eq or "T = mg" in eq or "줄/끈 문제라면" in eq)
            add_app("N - mg = mv²/R")
            add_app("N = mg + mv²/R")
            add_not("T - mg = mv²/R : 트랙/레일 문제에서는 장력 T가 아니라 수직항력 N 사용")
        elif (explicit_track_support or asks_normal) and asks_tension and not sem.string_support:
            add_app("트랙/레일 문제라면 N - mg = mv²/R")
            add_app("줄/끈 문제라면 T - mg = mv²/R")
            if "rail/track 단서와 tension/장력 단서가 충돌합니다. 지지 방식 확인 필요" not in ambiguity:
                ambiguity.append("rail/track 단서와 tension/장력 단서가 충돌합니다. 지지 방식 확인 필요")

    # Banked-curve guard and default formulas.
    if sem.banked_curve:
        remove_app_if(lambda eq: eq.strip() in {"N = mg", "μ_s ≥ v²/(gR)", "f_s = mv²/R"})
        if sem.max_speed and not any("N cosθ - f sinθ = mg" in eq for eq in app):
            add_app("N cosθ - f sinθ = mg")
            add_app("N sinθ + f cosθ = mv²/R")
            add_app("f = μ_sN")
        if sem.min_speed and not any("N cosθ + f sinθ = mg" in eq for eq in app):
            add_app("N cosθ + f sinθ = mg")
            add_app("N sinθ - f cosθ = mv²/R")
            add_app("f = μ_sN")

    # Block-pulley dominance: confirmed horizontal-table/hanging-mass/pulley
    # problems must not be contaminated by conical-pendulum equations merely
    # because they contain words such as string, hanging, or horizontal.
    block_pulley_context = sem.horizontal_table and sem.hanging_mass and sem.pulley
    if block_pulley_context:
        remove_app_if(lambda eq: "T cosθ = mg" in eq or "T sinθ" in eq or "r = L sinθ" in eq or "ω² = g" in eq)
        not_app = [eq for eq in not_app if "원뿔진자" not in eq and "T cosθ" not in eq and "T sinθ" not in eq and "r = L sinθ" not in eq]
        add_not("원뿔진자 성분식 : 수평면 블록-도르래 문제에는 사용하지 않음")
        add_not("원뿔진자 반지름-줄길이 기하식 : 원뿔진자 조건이 없으므로 사용하지 않음")
        add_caution("블록+도르래+매달린 물체 조건이 우선하므로 원뿔진자 후보를 배제합니다.")
    # Conical pendulum candidates should never be formula-empty, but only when
    # the conical geometry is actually present and no block-pulley structure has
    # priority.
    elif sem.conical_explicit or sem.conical_structural or sem.conical_candidate:
        if not any("T cosθ = mg" in eq for eq in app):
            add_app("T cosθ = mg")
            add_app("T sinθ = mω²r")
            add_app("r = L sinθ")
        add_not("ΣM_G = I_Gα : 원뿔진자는 질점 원운동으로 우선 처리")

    # Bullet/projectile embedded in rotating body.
    if sem.bullet_rotating_body_collision:
        add_app("H_O(before) = H_O(after)")
        add_app("m_b v r = I_totalω")
        remove_app_if(lambda eq: "x = x0" in eq or "y = y0" in eq or "m1v1i + m2v2i" in eq)
        add_not("단순 1차원 선운동량 보존식만 우선 적용 금지")

    # Never leave selected specialist result formula-empty.
    title = f"{getattr(bp, 'title', '')} {getattr(bp, 'template_id', '')} {getattr(bp, 'final_template_id', '')}"
    if not app:
        if sem.explicit_pure_rolling:
            app.extend(["v_G = ωR", "a_G = αR"])
        elif sem.slip_present:
            app.extend(["ΣF = ma_G", "ΣM_G = I_Gα", "f_k = μ_kN"])
        elif sem.banked_curve and sem.max_speed:
            app.extend(["N cosθ - f sinθ = mg", "N sinθ + f cosθ = mv²/R", "f = μ_sN"])
        elif sem.banked_curve and sem.min_speed:
            app.extend(["N cosθ + f sinθ = mg", "N sinθ - f cosθ = mv²/R", "f = μ_sN"])
        elif sem.track_support and sem.bottom_position:
            app.extend(["N - mg = mv²/R", "N = mg + mv²/R"])
        elif (sem.conical_explicit or sem.conical_structural or sem.conical_candidate) and not (sem.horizontal_table and sem.hanging_mass and sem.pulley):
            app.extend(["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"])
        elif sem.cartesian_position_vector:
            app.extend(["r(t) = x(t)i + y(t)j", "v(t) = dr/dt", "a(t) = d²r/dt²"])

    bp.applicable_equations = _uniq(app)
    bp.governing_equations = list(bp.applicable_equations)
    bp.not_applicable_equations = _semantic_unique(not_app)
    bp.cautions = _semantic_unique(cautions)
    bp.warnings = _semantic_unique([*getattr(bp, "warnings", []), *bp.cautions])
    bp.ambiguity_notes = _semantic_unique(ambiguity)
    bp.forbidden_formula_guard_applied = True  # type: ignore[attr-defined]
    bp.consistency_check_passed = True  # type: ignore[attr-defined]
