from __future__ import annotations

from pathlib import Path

from dynamics_core.feedback import build_diagnosis
from dynamics_core.parser import analyze_text
from dynamics_core.scope_limits import (
    ASCII_SYMBOL_GUIDE,
    FIGURE_TEXT_CHECKLIST,
    IMAGE_INPUT_NOTICE,
    INPUT_TEMPLATES,
    NUMERIC_SOLVER_NOTICE,
    STREAMLIT_MOBILE_NOTICE,
    SUPPORTED_SCOPE_ROWS,
    SYMBOL_HELPERS,
    detect_unsupported_scope,
    insert_helper_text,
)
from dynamics_core.strategy_engine import recommend_strategy


def diagnose(problem: str):
    features = analyze_text(problem, "")
    rec = recommend_strategy(features, "자동 추정")
    return build_diagnosis(problem, "", "자동 추정", features, rec, enable_ai_assist=False)


def test_3d_unsupported_scope_detection_blocks_2d_formulas():
    cases = [
        "A rigid body rotates in 3D with angular velocity components omega_x, omega_y, omega_z.",
        "Use Euler's equations to find the precession rate of a gyroscope.",
        "A disk undergoes gyroscopic precession about a vertical axis.",
        "Find the motion using the inertia tensor matrix.",
    ]
    for problem in cases:
        scope = detect_unsupported_scope(problem)
        assert scope.status == "unsupported"
        diagnosis = diagnose(problem)
        assert "미지원" in diagnosis.problem_model.problem_type
        assert diagnosis.blueprint.support_level.startswith("미지원")
        joined_app = "\n".join(diagnosis.blueprint.applicable_equations)
        assert "v_G = ωR" not in joined_app
        assert "N sinθ" not in joined_app
        assert diagnosis.blueprint.not_applicable_equations
        assert diagnosis.blueprint.cautions


def test_limitation_docs_exist_and_contain_core_notices():
    required = [
        "docs/LIMITATIONS.md",
        "docs/IMAGE_INPUT_LIMITATION.md",
        "docs/NUMERIC_SOLVER_LIMITATION.md",
        "docs/UNSUPPORTED_3D_DYNAMICS.md",
        "docs/SUPPORT_SCOPE_MATRIX.md",
        "docs/INPUT_GUIDE.md",
        "docs/STREAMLIT_MOBILE_LIMITATION.md",
        "docs/MOBILE_QA_CHECKLIST.md",
    ]
    for rel in required:
        text = Path(rel).read_text(encoding="utf-8")
        assert len(text) > 100, rel
    readme = Path("README.md").read_text(encoding="utf-8")
    for phrase in ["이미지/그림", "완전 자동", "3D 강체", "Streamlit 기반 모바일 웹앱", "기호 입력 도우미"]:
        assert phrase in readme


def test_support_scope_and_limitations_are_user_facing_constants():
    assert "이미지/그림" in IMAGE_INPUT_NOTICE
    assert "완전 자동" in NUMERIC_SOLVER_NOTICE
    assert "Streamlit 기반" in STREAMLIT_MOBILE_NOTICE
    assert len(FIGURE_TEXT_CHECKLIST) >= 8
    assert any(row[2] == "미지원" or row[1] == "미지원" for row in SUPPORTED_SCOPE_ROWS)


def test_symbol_helper_and_ascii_guide_constants():
    labels = {s.label for s in SYMBOL_HELPERS}
    for label in ["θ", "ω", "α", "μ", "ΣF", "ΣM_G", "e_θ", "theta_dot"]:
        assert label in labels
    assert ASCII_SYMBOL_GUIDE["theta"] == "θ"
    assert ASCII_SYMBOL_GUIDE["mu_s"] == "μ_s"
    assert insert_helper_text("A block", "theta ").endswith("theta ")


def test_input_templates_cover_required_mobile_problem_families():
    labels = {t.label for t in INPUT_TEMPLATES}
    for label in ["수평면 블록-도르래", "경사면 물체", "수직 원운동", "원뿔진자", "경사진 커브", "순수 구름", "회전충돌"]:
        assert label in labels
    for tmpl in INPUT_TEMPLATES:
        assert len(tmpl.text) > 30


def test_app_exposes_limitations_and_input_helper_ui():
    app = Path("app.py").read_text(encoding="utf-8")
    for needle in [
        "render_limitations_brief",
        "render_symbol_input_helpers",
        "기호 입력 도우미",
        "자주 쓰는 문제 템플릿",
        "지원 범위와 한계",
        "그림 정보 체크리스트",
    ]:
        assert needle in app
