from __future__ import annotations

from pathlib import Path

from dynamics_core.ai_assist import GPT_ASSIST_JSON_SCHEMA, maybe_apply_ai_assist
from dynamics_core.modeling import build_problem_model, build_solution_blueprint
from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy
from dynamics_core.template_rebuild import GPT_CANDIDATE_TO_TEMPLATE_ID


def base_objects(problem: str):
    features = analyze_text(problem)
    rec = recommend_strategy(features, "자동 추정")
    model = build_problem_model(problem, features, rec, "자동 추정")
    bp = build_solution_blueprint(model, features, rec, problem)
    return features, rec, model, bp


def mock_for(candidate: str, confidence: float = 0.90, detected=None, must_not=None):
    def _client(payload, schema, model, max_output_tokens, temperature):
        assert schema is GPT_ASSIST_JSON_SCHEMA
        return {
            "primary_candidate": candidate,
            "secondary_candidates": [],
            "confidence": confidence,
            "detected_features": detected or {},
            "evidence_phrases": ["mock evidence"],
            "missing_information": [],
            "must_use_tags": [],
            "must_not_use_tags": must_not or [],
            "warnings": ["mock warning"],
        }
    return _client


def run_hybrid(problem: str, candidate: str, tmp_path: Path, confidence: float = 0.90, detected=None, must_not=None, force_generic: bool = False):
    features, rec, model, bp = base_objects(problem)
    if force_generic:
        model.problem_type = "일반 동역학 문제"
        bp.title = "일반 동역학 문제 풀이 골격"
        bp.applicable_equations = ["ΣF = ma", "일반식 후보"]
        bp.not_applicable_equations = []
    return maybe_apply_ai_assist(
        problem,
        features,
        rec,
        model,
        bp,
        enable_api=True,
        client=mock_for(candidate, confidence, detected, must_not),
        cache_path=tmp_path / f"{candidate}.cache.json",
        log_path=tmp_path / "hybrid.jsonl",
    )


def test_candidate_mapping_table_contains_required_templates():
    required = {
        "conical_pendulum",
        "sliding_rotation",
        "vertical_circle_string_bottom",
        "cartesian_position_vector",
        "bullet_rotating_body_collision",
        "frictionless_pulley_block",
        "banked_curve_with_friction_max_speed",
        "banked_curve_with_friction_min_speed",
    }
    assert required.issubset(GPT_CANDIDATE_TO_TEMPLATE_ID.keys())


def test_mock_gpt_bullet_candidate_rebuilds_template(tmp_path: Path):
    problem = "projectile embeds in a wheel and they rotate together about a fixed axle."
    out = run_hybrid(problem, "bullet_rotating_body_collision", tmp_path, detected={"has_collision": True, "has_fixed_axis": True}, force_generic=True)
    assert getattr(out, "ai_rebuild_applied", False) is True
    assert getattr(out, "final_template_id") == "bullet_rotating_body_collision"
    joined = "\n".join(out.applicable_equations)
    assert "H_O(before) = H_O(after)" in joined
    assert "m_b v r = I_totalω" in joined
    assert "선운동량" in "\n".join(out.not_applicable_equations + out.cautions)


def test_mock_gpt_conical_candidate_rebuilds_template(tmp_path: Path):
    problem = "줄에 매단 물체가 원을 돈다. 각속도?"
    out = run_hybrid(problem, "conical_pendulum", tmp_path, detected={"has_string": True, "has_horizontal_circle": True})
    assert getattr(out, "final_template_id") == "conical_pendulum"
    joined = "\n".join(out.applicable_equations)
    assert "T cosθ = mg" in joined
    assert "T sinθ = mω²r" in joined
    assert "ΣM_G = I_Gα" not in joined


def test_mock_gpt_vertical_bottom_rebuilds_template(tmp_path: Path):
    problem = "줄에 매단 공이 vertical circle을 한다. lowest에서 tension?"
    out = run_hybrid(problem, "vertical_circle_string_bottom", tmp_path)
    assert getattr(out, "final_template_id") == "vertical_circle_string_bottom"
    joined = "\n".join(out.applicable_equations)
    assert "T - mg = mv²/R" in joined
    assert "T = mg + mv²/R" in joined
    assert "N - mg" not in joined


def test_mock_gpt_cartesian_candidate_rebuilds_and_blocks_polar(tmp_path: Path):
    problem = "r(t)=<3t,2t^2> 이다. v와 a를 구하라."
    out = run_hybrid(problem, "cartesian_position_vector", tmp_path, detected={"has_cartesian_vector": True}, force_generic=True)
    assert getattr(out, "final_template_id") == "cartesian_position_vector"
    joined = "\n".join(out.applicable_equations)
    assert "v(t) = dr/dt" in joined
    assert "a(t) = d²r/dt²" in joined
    assert "e_r" not in joined and "e_θ" not in joined


def test_mock_gpt_sliding_rotation_rebuilds_and_guard_blocks_pure_rolling(tmp_path: Path):
    problem = "wheel rolls but skids."
    out = run_hybrid(problem, "sliding_rotation", tmp_path, detected={"has_rolling": True, "has_slipping": True}, must_not=["pure_rolling_constraint"])
    assert getattr(out, "final_template_id") == "sliding_rotation"
    joined = "\n".join(out.applicable_equations)
    assert "ΣF = ma_G" in joined
    assert "ΣM_G = I_Gα" in joined
    assert "v_G = ωR" not in joined
    assert "a_G = αR" not in joined
    assert "v_G = ωR" in "\n".join(out.not_applicable_equations)


def test_low_confidence_ai_does_not_force_rebuild(tmp_path: Path):
    problem = "줄에 매단 물체가 원을 돈다."
    out = run_hybrid(problem, "conical_pendulum", tmp_path, confidence=0.42, detected={"has_string": True})
    assert getattr(out, "ai_rebuild_applied", False) is False
    assert any("confidence" in x for x in out.ambiguity_notes)
