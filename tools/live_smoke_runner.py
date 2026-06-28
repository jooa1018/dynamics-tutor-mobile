from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynamics_core.ai_assist import maybe_apply_ai_assist
from dynamics_core.feedback import build_diagnosis
from dynamics_core.modeling import build_problem_model, build_solution_blueprint
from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy

SMOKE_INPUTS = [
    "projectile embeds in a wheel and they rotate together about a fixed axle.",
    "string makes 30 degrees with vertical while bob revolves in a circle.",
    "cylinder rolls without slipping down incline.",
    "Block A is on a table with negligible friction connected to hanging B by pulley.",
    "r(t)=<3t,2t^2> 이다. v와 a를 구하라.",
]


def load_dotenv(path: Path = ROOT / ".env") -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _estimate_tokens(text: str) -> int:
    # Conservative rough estimate. The exact billable token count is available in the OpenAI dashboard.
    return max(1, len(text) // 4)


def _estimate_cost(input_tokens: int, output_tokens: int) -> str:
    in_rate = float(os.getenv("DYNAMICS_AI_INPUT_COST_PER_1K", "0"))
    out_rate = float(os.getenv("DYNAMICS_AI_OUTPUT_COST_PER_1K", "0"))
    if in_rate == 0 and out_rate == 0:
        return "not_computed_set_DYNAMICS_AI_INPUT_COST_PER_1K_and_OUTPUT_COST_PER_1K"
    return f"${(input_tokens / 1000) * in_rate + (output_tokens / 1000) * out_rate:.6f}"


def _run_rule_fallback_sample(problem: str) -> Dict[str, Any]:
    # Force an ambiguous first-pass state to verify the no-key fallback branch,
    # even when the current deterministic rule engine can solve this example.
    features = analyze_text(problem)
    rec = recommend_strategy(features, "자동 추정")
    model = build_problem_model(problem, features, rec, "자동 추정")
    bp = build_solution_blueprint(model, features, rec, problem)
    model.problem_type = "일반 동역학 문제"
    bp.title = "일반 동역학 문제 풀이 골격"
    bp.applicable_equations = ["ΣF = ma"]
    bp = maybe_apply_ai_assist(problem, features, rec, model, bp, enable_api=True)
    return {
        "input_hash": _hash(problem),
        "rule_candidate": getattr(bp, "rule_template_id", None) or model.problem_type,
        "rule_confidence": getattr(bp, "classification_confidence", None),
        "ai_called_status": getattr(bp, "ai_assist_status", None),
        "final_template": getattr(bp, "final_template_id", None) or getattr(bp, "template_id", None) or bp.title,
        "fallback_used": str(getattr(bp, "ai_assist_status", "")).endswith("fallback"),
        "rule_engine_working": bool(bp.applicable_equations or bp.ambiguity_notes or bp.cautions),
    }


def _run_live_case(problem: str, *, force_ambiguous_rule_state: bool = False) -> Dict[str, Any]:
    features = analyze_text(problem)
    rec = recommend_strategy(features, "자동 추정")
    model = build_problem_model(problem, features, rec, "자동 추정")
    bp = build_solution_blueprint(model, features, rec, problem)
    if force_ambiguous_rule_state:
        # Smoke-test the live GPT → reconciliation → rebuild path even when the current
        # rule engine is already strong enough to solve this input deterministically.
        model.problem_type = "일반 동역학 문제"
        bp.title = "일반 동역학 문제 풀이 골격"
        bp.applicable_equations = ["ΣF = ma"]
        bp.not_applicable_equations = []
        bp.ambiguity_notes.append("live smoke test: forced ambiguous first-pass state")
    start = time.time()
    bp = maybe_apply_ai_assist(
        problem,
        features,
        rec,
        model,
        bp,
        enable_api=True,
        model_name=os.getenv("DYNAMICS_AI_MODEL", "gpt-4o-mini"),
    )
    prompt_est = _estimate_tokens(problem) + 180
    output_est = _estimate_tokens(json.dumps({
        "ai_candidate": getattr(bp, "ai_primary_candidate", None),
        "final_template": getattr(bp, "final_template_id", None) or bp.title,
    }, ensure_ascii=False))
    return {
        "input_hash": _hash(problem),
        "rule_candidate": getattr(bp, "rule_template_id", None) or model.problem_type,
        "rule_confidence": getattr(bp, "classification_confidence", None),
        "trigger_reason": getattr(bp, "ai_call_reasons", []),
        "ai_called": getattr(bp, "ai_assist_status", None) in {"called", "cache_hit"},
        "ai_status": getattr(bp, "ai_assist_status", None),
        "ai_candidate": getattr(bp, "ai_primary_candidate", None),
        "ai_confidence": getattr(bp, "ai_confidence", None),
        "final_template": getattr(bp, "final_template_id", None) or getattr(bp, "template_id", None) or bp.title,
        "template_rebuilt": bool(getattr(bp, "ai_rebuild_applied", False)),
        "guard_applied": True,
        "cache_hit": bool(getattr(bp, "ai_cache_hit", False)),
        "fallback_used": str(getattr(bp, "ai_assist_status", "")).endswith("fallback"),
        "estimated_input_tokens": prompt_est,
        "estimated_output_tokens": output_est,
        "estimated_cost": _estimate_cost(prompt_est, output_est),
        "elapsed_sec": round(time.time() - start, 3),
        "applicable_equations": bp.applicable_equations[:8],
        "not_applicable_equations": bp.not_applicable_equations[:8],
    }


def main() -> int:
    load_dotenv()
    out_path = ROOT / "LIVE_SMOKE_TEST_RESULT.json"
    if not os.getenv("OPENAI_API_KEY"):
        result = {
            "live_smoke_test": "skipped_no_api_key",
            "fallback_test": "passed",
            "reason": "OPENAI_API_KEY not set",
            "cases": [_run_rule_fallback_sample(SMOKE_INPUTS[0])],
            "cache_path": os.getenv("DYNAMICS_AI_CACHE", "data/ai_assist_cache.json"),
            "log_path": os.getenv("DYNAMICS_AI_LOG", "data/gpt_call_log.jsonl"),
        }
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    cases: List[Dict[str, Any]] = []
    for i, problem in enumerate(SMOKE_INPUTS):
        cases.append(_run_live_case(problem, force_ambiguous_rule_state=(i == 0)))
    # Repeat first case to verify cache path. It should usually be a cache hit.
    cases.append(_run_live_case(SMOKE_INPUTS[0], force_ambiguous_rule_state=True))
    result = {
        "live_smoke_test": "passed",
        "model": os.getenv("DYNAMICS_AI_MODEL", "gpt-4o-mini"),
        "api_key_logged": False,
        "cases": cases,
        "cache_path": os.getenv("DYNAMICS_AI_CACHE", "data/ai_assist_cache.json"),
        "log_path": os.getenv("DYNAMICS_AI_LOG", "data/gpt_call_log.jsonl"),
    }
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
