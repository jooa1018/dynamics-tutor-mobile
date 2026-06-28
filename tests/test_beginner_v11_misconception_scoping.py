from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy
from dynamics_core.feedback import build_diagnosis


def diagnose(problem: str, solution: str = ""):
    features = analyze_text(problem, solution)
    rec = recommend_strategy(features, "자동 추정")
    return build_diagnosis(problem, solution, "자동 추정", features, rec, enable_ai_assist=False)


def _joined(items):
    if isinstance(items, list):
        return "\n".join(str(x) for x in items)
    return str(items)


def _all_output(d):
    bp = d.blueprint
    parts = [
        d.problem_model.problem_type,
        bp.title,
        *bp.applicable_equations,
        *bp.governing_equations,
        *bp.auxiliary_equations,
        *bp.not_applicable_equations,
        *bp.cautions,
        *d.next_questions,
        *[name for name, _ in d.misconception_hits],
        *[explain for _, explain in d.misconception_hits],
    ]
    return "\n".join(str(x) for x in parts)


def test_006_conical_pendulum_does_not_show_pulley_misconception_warning():
    d = diagnose("질량 m인 물체가 길이 L인 줄에 매달려 수직선과 각도 θ를 이루며 수평 원운동한다. 각속도를 구하라.")
    assert "원뿔진자" in d.problem_model.problem_type
    app = _joined(d.blueprint.applicable_equations)
    assert "T cosθ = mg" in app
    assert "T sinθ = mω²r" in app
    assert "r = L sinθ" in app
    out = _all_output(d)
    forbidden = ["도르래 문제의 가속도 관계 누락", "두 물체 가속도 관계 누락", "블록-도르래 연립방정식 누락"]
    for phrase in forbidden:
        assert phrase not in out


def test_007_block_pulley_allows_pulley_specific_missing_equation_warnings_without_conical_formulas():
    problem = "마찰 없는 수평면 위 블록 A와 매달린 블록 B가 질량 없는 줄과 도르래로 연결되어 있다. 가속도와 장력을 구하라."
    solution = "블록 A에는 T = m_Aa를 쓰고, 블록 B에는 힘 식을 세우지 않았다."
    d = diagnose(problem, solution)
    assert "블록" in d.problem_model.problem_type and ("도르래" in d.problem_model.problem_type or "매달린" in d.problem_model.problem_type)
    names = _joined([name for name, _ in d.misconception_hits])
    explains = _joined([explain for _, explain in d.misconception_hits])
    assert "도르래 문제의 가속도 관계 누락" in names
    assert "매달린 물체 B" in names or "m_Bg - T = m_Ba" in explains
    out = _all_output(d)
    for formula in ["T cosθ = mg", "T sinθ = mω²r", "r = L sinθ"]:
        assert formula not in _joined(d.blueprint.applicable_equations)


def test_008_single_string_equilibrium_does_not_show_pulley_warning():
    d = diagnose("질량 m인 물체가 천장에 매단 줄에 정지해 있다. 줄의 장력을 구하라.")
    assert "단일 줄 평형" in d.problem_model.problem_type
    assert "T = mg" in _joined(d.blueprint.applicable_equations)
    out = _all_output(d)
    for phrase in ["도르래 문제의 가속도 관계 누락", "두 물체 가속도 관계 누락", "움직도르래 구속조건 누락"]:
        assert phrase not in out


def test_009_simple_pendulum_does_not_show_pulley_warning():
    d = diagnose("길이 L인 줄에 매달린 질량 m인 물체가 작은 각도로 진동한다. 주기를 구하라.")
    assert "단진자" in d.problem_model.problem_type
    assert "T_period = 2π√(L/g)" in _joined(d.blueprint.applicable_equations)
    out = _all_output(d)
    for phrase in ["도르래 문제의 가속도 관계 누락", "블록-도르래 연립방정식 누락"]:
        assert phrase not in out


def test_010_ambiguous_string_problem_asks_for_confirmation_instead_of_warning():
    d = diagnose("줄에 매달린 물체가 움직인다. 가속도를 구하라.")
    out = _all_output(d)
    assert "확인 필요" in out
    assert "도르래로 연결된 두 물체 문제라면" in out
    assert "오개념 경고: 도르래 문제의 가속도 관계를 누락했습니다" not in out
    assert "도르래 문제의 가속도 관계 누락" not in _joined([name for name, _ in d.misconception_hits])
