"""Pytest discovery wrapper for legacy script-style regression suites."""

import regression_tests
import expert_regression_tests
import fourth_regression_tests
import final_quality_tests
import expression_variation_tests


def test_regression_suite():
    regression_tests.run_all()


def test_expert_regression_suite():
    expert_regression_tests.run_all()


def test_fourth_regression_suite():
    fourth_regression_tests.run_all()


def test_final_quality_suite():
    final_quality_tests.run_all()


def test_expression_variation_suite():
    expression_variation_tests.run_all()
