from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy
from dynamics_core.feedback import build_diagnosis
from dynamics_core import lexicon


def diagnose(problem: str, solution: str = ""):
    features = analyze_text(problem, solution)
    rec = recommend_strategy(features, "자동 추정")
    return build_diagnosis(problem, solution, "자동 추정", features, rec, enable_ai_assist=False)


def joined(items):
    return "\n".join(str(x) for x in items)


def all_output(d):
    bp = d.blueprint
    return joined([
        d.problem_model.problem_type,
        bp.title,
        *bp.applicable_equations,
        *bp.governing_equations,
        *bp.auxiliary_equations,
        *bp.not_applicable_equations,
        *bp.cautions,
        *d.next_questions,
        *[n for n, _ in d.misconception_hits],
        *[e for _, e in d.misconception_hits],
    ])


FORBIDDEN_PULLEY_WARNINGS = [
    "도르래 문제의 가속도 관계 누락",
    "두 물체 가속도 관계 누락",
    "블록-도르래 연립방정식 누락",
]


def assert_no_pulley_warning(d):
    out = all_output(d)
    for phrase in FORBIDDEN_PULLEY_WARNINGS:
        assert phrase not in out


def test_011_sil_single_string_equilibrium():
    d = diagnose("질량 m인 물체가 천장에 연결된 실에 매달려 가만히 있다. 장력을 구하라.")
    assert "단일 줄 평형" in d.problem_model.problem_type
    assert "T = mg" in joined(d.blueprint.applicable_equations)
    assert_no_pulley_warning(d)


def test_012_kkeun_single_string_equilibrium():
    d = diagnose("질량 m인 추가 끈 끝에 달려 움직이지 않는다. 끈의 장력을 구하라.")
    assert "단일 줄 평형" in d.problem_model.problem_type
    assert "T = mg" in joined(d.blueprint.applicable_equations)
    assert_no_pulley_warning(d)


def test_013_small_amplitude_simple_pendulum():
    d = diagnose("길이 L의 실에 매단 추가 작은 진폭으로 흔들린다. 주기를 구하라.")
    assert "단진자" in d.problem_model.problem_type
    assert "T_period = 2π√(L/g)" in joined(d.blueprint.applicable_equations)
    assert_no_pulley_warning(d)


def test_014_small_oscillation_simple_pendulum():
    d = diagnose("길이 L인 줄에 매달린 추가 소진동한다. 주기를 구하라.")
    assert "단진자" in d.problem_model.problem_type
    assert "T_period = 2π√(L/g)" in joined(d.blueprint.applicable_equations)
    assert_no_pulley_warning(d)


def test_015_circle_phrase_conical_pendulum():
    d = diagnose("질량 m인 추가 길이 L의 실에 매달려 연직선과 θ만큼 기울어진 채 원을 그리며 돈다. 각속도를 구하라.")
    assert "원뿔진자" in d.problem_model.problem_type
    app = joined(d.blueprint.applicable_equations)
    for formula in ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"]:
        assert formula in app
    assert_no_pulley_warning(d)


def test_016_colloquial_simple_pendulum():
    d = diagnose("실에 매단 추가 살짝 흔들림. 주기?")
    assert "단진자" in d.problem_model.problem_type
    assert "T_period = 2π√(L/g)" in joined(d.blueprint.applicable_equations)
    assert_no_pulley_warning(d)


def test_017_colloquial_single_string_equilibrium():
    d = diagnose("추가 실에 달려서 가만히 있음. 장력?")
    assert "단일 줄 평형" in d.problem_model.problem_type
    assert "T = mg" in joined(d.blueprint.applicable_equations)
    assert_no_pulley_warning(d)


def test_018_colloquial_conical_pendulum():
    d = diagnose("로프에 매달린 물체가 연직선과 각도 θ를 유지하며 원을 그리며 돎. 각속도?")
    assert "원뿔진자" in d.problem_model.problem_type
    app = joined(d.blueprint.applicable_equations)
    for formula in ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"]:
        assert formula in app
    assert_no_pulley_warning(d)


def test_019_synonym_expansion_does_not_reintroduce_pulley_warning_for_pendulum():
    d = diagnose("길이 L의 실에 매단 추가 작은 진폭으로 흔들린다. 주기를 구하라.")
    assert "단진자" in d.problem_model.problem_type
    assert_no_pulley_warning(d)


def test_020_ambiguous_sil_problem_asks_confirmation_not_warning():
    d = diagnose("실에 매달린 물체가 움직인다. 가속도를 구하라.")
    out = all_output(d)
    assert "확인 필요" in out
    assert "도르래로 연결된 두 물체 문제라면" in out
    assert "오개념 경고: 도르래 문제의 가속도 관계를 누락했습니다" not in out
    assert "도르래 문제의 가속도 관계 누락" not in joined([name for name, _ in d.misconception_hits])


def test_lexicon_module_centralizes_synonyms():
    assert lexicon.has_rope("실과 로프로 연결")
    assert lexicon.has_rest("가만히 있음")
    assert lexicon.has_pendulum("작은 진폭으로 흔들림")
    assert lexicon.has_conical("연직선과 각도 θ를 유지하며 원을 그리며 돎")
