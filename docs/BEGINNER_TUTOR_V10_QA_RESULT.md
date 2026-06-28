# Beginner Tutor v1.0 QA Result

This QA pass implements the beginner-learning requirements focused on preventing plausible but wrong formulas from appearing as applicable equations.

## Highest-priority fix

Input:

```text
마찰 없는 수평면 위 블록 A와 매달린 블록 B가 질량 없는 줄과 도르래로 연결되어 있다. 가속도와 장력을 구하라.
```

Expected applicable equations:

```text
N_A = m_Ag
f = 0
T = m_Aa
m_Bg - T = m_Ba
```

Forbidden contamination removed from the entire output:

```text
T cosθ = mg
T sinθ = mω²r
r = L sinθ
```

## Added learning-support features

- Stronger conical-pendulum confirmation conditions.
- Type-priority rule: block + horizontal surface + pulley + hanging mass dominates generic string/hanging cues.
- Student-solution misconception detection for frictionless, rolling, banked curve, vertical circle, pulley constraints, collision, and energy misuse.
- More explicit beginner equation explanations for `N_A=m_Ag`, `T=m_Aa`, `f=μN`, `ΣM_G=I_Gα`, rolling constraints, and vertical-circle force balance.
- Unit conversion helper for `g`, `km/h`, `cm`, and `rpm`.
- Beginner helper calculators for representative template drills.
- Wrong-note auto tags and spaced review helper.
- Difficulty helper from Level 1 to Level 5.

## Validation

```text
pytest -q
427 passed

coverage report -m
TOTAL 4678 statements, 95% coverage

python regression_tests.py
OK

python expert_regression_tests.py
OK

python fourth_regression_tests.py
OK

python final_quality_tests.py
OK

python expression_variation_tests.py
OK

python tools/ui_smoke_test.py
passed

python live_smoke_test.py
API key 없음 상태 fallback passed

python -m compileall -q .
success
```
