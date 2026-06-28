from __future__ import annotations

from dynamics_core.models import ProblemModel, SolutionBlueprint
from dynamics_core.template_rebuild import rebuild_from_template_id, reconcile_and_rebuild
from dynamics_core.ai_assist import apply_forbidden_formula_guard, GPTAssistResult


def fresh():
    return ProblemModel(), SolutionBlueprint(title="초기")


def test_rebuild_remaining_template_builders():
    for tid, must in [
        ("pure_rolling", "v_G = ωR"),
        ("vertical_circle_string_top", "v_min = √(gR)"),
        ("vertical_circle_track_bottom", "N - mg = mv²/R"),
        ("polar_motion", "e_r"),
        ("banked_curve_with_friction_min_speed", "N cosθ + f sinθ = mg"),
        ("general_planar_rigid_body", "ΣM_G = I_Gα"),
    ]:
        m, bp = fresh()
        assert rebuild_from_template_id(tid, "test", m, bp) is True
        assert must in "\n".join(bp.applicable_equations)
        assert getattr(bp, "final_template_id") == tid


def test_rebuild_unknown_template_returns_false():
    m, bp = fresh()
    assert rebuild_from_template_id("missing_template", "test", m, bp) is False


def test_reconcile_no_mapping_and_low_confidence_paths():
    m, bp = fresh()
    dec = reconcile_and_rebuild(problem="test", model=m, bp=bp, ai_candidate="unknown", ai_confidence=0.95)
    assert dec.applied is False
    assert getattr(bp, "reconciliation_status") == "no_mapping"

    m2, bp2 = fresh()
    dec2 = reconcile_and_rebuild(problem="줄에 매단 물체가 원을 돈다", model=m2, bp=bp2, ai_candidate="conical_pendulum", ai_confidence=0.2)
    assert dec2.applied is False
    assert getattr(bp2, "reconciliation_status") == "low_ai_confidence"


def test_forbidden_guard_removes_flat_curve_from_banked_friction():
    m, bp = fresh()
    rebuild_from_template_id("banked_curve_with_friction_max_speed", "마찰 있는 경사진 커브 최대속도", m, bp)
    bp.applicable_equations.append("μ_s ≥ v²/(gR)")
    out = apply_forbidden_formula_guard(bp, "마찰 있는 경사진 커브에서 최대속도")
    assert "μ_s ≥ v²/(gR)" not in "\n".join(out.applicable_equations)


def test_forbidden_guard_respects_ai_must_not_tags():
    m, bp = fresh()
    rebuild_from_template_id("polar_motion", "극좌표", m, bp)
    ai = GPTAssistResult(primary_candidate="cartesian_position_vector", confidence=0.9, must_not_use_tags=["polar_kinematics"])
    out = apply_forbidden_formula_guard(bp, "r(t)=3t i + 2t^2 j", ai)
    assert "e_r" not in "\n".join(out.applicable_equations)
