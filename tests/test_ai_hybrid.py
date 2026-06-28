from __future__ import annotations

from pathlib import Path

from dynamics_core.ai_assist import (
    GPT_ASSIST_JSON_SCHEMA,
    apply_forbidden_formula_guard,
    decide_ai_assist,
    maybe_apply_ai_assist,
)
from dynamics_core.feedback import build_diagnosis
from dynamics_core.modeling import build_problem_model, build_solution_blueprint
from dynamics_core.models import SolutionBlueprint
from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy


def base_objects(problem: str):
    features = analyze_text(problem)
    rec = recommend_strategy(features, "자동 추정")
    model = build_problem_model(problem, features, rec, "자동 추정")
    bp = build_solution_blueprint(model, features, rec, problem)
    return features, rec, model, bp


def test_ai_not_called_for_clear_rule_case():
    problem = "마찰 없는 경사진 커브에서 필요한 경사각을 구하라."
    features, rec, model, bp = base_objects(problem)
    decision = decide_ai_assist(problem, features, rec, model, bp)
    assert decision.confidence.score >= 0.90
    assert decision.should_call is False


def test_ai_called_for_ambiguous_short_pulley_case():
    problem = "두 물체가 도르래로 연결되어 있다."
    features, rec, model, bp = base_objects(problem)
    decision = decide_ai_assist(problem, features, rec, model, bp)
    assert decision.should_call is True
    assert decision.confidence.score < 0.70
    assert any("ambiguous" in x or "short_input" in x for x in decision.confidence.risk_flags)


def test_no_api_key_falls_back_without_crashing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    problem = "두 물체가 도르래로 연결되어 있다."
    features, rec, model, bp = base_objects(problem)
    out = maybe_apply_ai_assist(problem, features, rec, model, bp, enable_api=True)
    assert getattr(out, "ai_assist_status") == "no_api_key_fallback"
    assert any("OPENAI_API_KEY" in c for c in out.cautions)


def test_mock_gpt_result_applies_tags_and_caches(tmp_path: Path):
    calls = {"n": 0}

    def mock_client(payload, schema, model, max_output_tokens, temperature):
        calls["n"] += 1
        assert schema is GPT_ASSIST_JSON_SCHEMA
        assert len(str(payload)) < 10000
        assert max_output_tokens <= 600
        return {
            "primary_candidate": "sliding_rotation",
            "secondary_candidates": ["general_planar_rigid_body"],
            "confidence": 0.88,
            "detected_features": {"has_rolling": True, "has_slipping": True, "friction_mode": "kinetic_or_slipping"},
            "evidence_phrases": ["굴러 내려가지만", "미끄럼이 발생한다"],
            "missing_information": ["운동마찰계수 μ_k"],
            "must_use_tags": ["sum_forces", "sum_moments_about_center", "kinetic_friction"],
            "must_not_use_tags": ["pure_rolling_constraint"],
            "warnings": ["미끄럼이 있으므로 순수 구름 조건을 적용하면 안 됩니다."],
        }

    problem = "원통이 경사면을 굴러 내려가지만 미끄럼이 발생한다."
    features, rec, model, bp = base_objects(problem)
    out = maybe_apply_ai_assist(problem, features, rec, model, bp, enable_api=True, client=mock_client, cache_path=tmp_path / "cache.json", log_path=tmp_path / "log.jsonl")
    assert calls["n"] == 1
    assert getattr(out, "ai_assist_status") == "called"
    assert getattr(out, "ai_primary_candidate") == "sliding_rotation"
    assert "v_G = ωR" not in "\n".join(out.applicable_equations)
    assert "a_G = αR" not in "\n".join(out.applicable_equations)
    assert "v_G = ωR" in "\n".join(out.not_applicable_equations)
    assert (tmp_path / "log.jsonl").exists()

    # 같은 정규화 입력은 캐시를 사용해야 합니다.
    features2, rec2, model2, bp2 = base_objects(problem)
    out2 = maybe_apply_ai_assist(problem, features2, rec2, model2, bp2, enable_api=True, client=mock_client, cache_path=tmp_path / "cache.json", log_path=tmp_path / "log.jsonl")
    assert calls["n"] == 1
    assert getattr(out2, "ai_assist_status") == "cache_hit"
    assert getattr(out2, "ai_cache_hit") is True


def test_gpt_error_fallback_keeps_forbidden_guard(tmp_path: Path):
    def bad_client(payload, schema, model, max_output_tokens, temperature):
        raise RuntimeError("network down")

    problem = "원통이 경사면을 굴러 내려가지만 미끄럼이 발생한다."
    features, rec, model, bp = base_objects(problem)
    # 일부러 잘못된 적용식을 넣어도 fallback guard가 제거해야 합니다.
    bp.applicable_equations.append("v_G = ωR")
    bp.applicable_equations.append("a_G = αR")
    out = maybe_apply_ai_assist(problem, features, rec, model, bp, enable_api=True, client=bad_client, cache_path=tmp_path / "cache.json", log_path=tmp_path / "log.jsonl")
    assert getattr(out, "ai_assist_status") == "error_fallback"
    assert "v_G = ωR" not in "\n".join(out.applicable_equations)
    assert "a_G = αR" not in "\n".join(out.applicable_equations)
    assert any("AI 보조 판별 실패" in c for c in out.cautions)


def test_forbidden_formula_guard_blocks_gpt_risk_tags():
    bp = SolutionBlueprint(
        title="가짜 순수 구름 골격",
        applicable_equations=["v_G = ωR", "a_G = αR", "ΣF = ma_G"],
    )
    out = apply_forbidden_formula_guard(bp, "원통이 굴러가지만 미끄럼이 있다.")
    assert "v_G = ωR" not in "\n".join(out.applicable_equations)
    assert "a_G = αR" not in "\n".join(out.applicable_equations)
    assert "v_G = ωR" in "\n".join(out.not_applicable_equations)


def test_build_diagnosis_marks_ai_status_for_clear_case():
    problem = "질점의 위치는 r(t)=3t\\hat{i}+2t^2\\hat{j} 이다. 속도와 가속도는?"
    features = analyze_text(problem)
    rec = recommend_strategy(features, "자동 추정")
    d = build_diagnosis(problem, "", "자동 추정", features, rec)
    assert d.problem_model.problem_type == "위치 함수 기반 입자 운동학"
    assert getattr(d.blueprint, "classification_confidence") >= 0.80
    assert "극좌표" not in "\n".join(d.blueprint.applicable_equations)
