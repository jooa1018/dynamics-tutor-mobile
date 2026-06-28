from __future__ import annotations

from dynamics_core.scope_limits import ASCII_SYMBOL_GUIDE, INPUT_TEMPLATES, SYMBOL_HELPERS, insert_helper_text


def test_symbol_helper_buttons_have_safe_ascii_insertions():
    for helper in SYMBOL_HELPERS:
        assert helper.label
        assert helper.insert_text
        assert "sk-" not in helper.insert_text
        assert "OPENAI_API_KEY" not in helper.insert_text


def test_ascii_symbol_aliases_cover_common_dynamics_symbols():
    expected = {
        "theta": "θ",
        "omega": "ω",
        "alpha": "α",
        "mu_s": "μ_s",
        "mu_k": "μ_k",
        "sum F": "ΣF",
        "sum M_G": "ΣM_G",
    }
    for k, v in expected.items():
        assert ASCII_SYMBOL_GUIDE[k] == v


def test_problem_templates_are_personal_app_safe():
    text = "\n".join(t.text for t in INPUT_TEMPLATES)
    for phrase in ["frictionless horizontal table", "incline", "vertical circle", "horizontal circle", "banked curve", "without slipping", "projectile"]:
        assert phrase.lower() in text.lower()
    assert "OPENAI_API_KEY" not in text
    assert "APP_PASSWORD" not in text


def test_insert_helper_text_preserves_existing_input_spacing():
    assert insert_helper_text("", "theta ") == "theta "
    assert insert_helper_text("mass m", "theta ") == "mass m theta "
    assert insert_helper_text("mass m ", "theta ") == "mass m theta "
