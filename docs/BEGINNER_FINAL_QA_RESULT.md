# 입문자 튜터 최종 QA 결과

## 자동 테스트

```text
pytest -q
383 passed

coverage run -m pytest -q
383 passed

coverage report -m
TOTAL 4114 statements, 95% coverage
```

## 기존 회귀 테스트

```text
python regression_tests.py
OK: all 2nd-rework regression tests passed

python expert_regression_tests.py
OK: expert regression tests passed — 100 representative cases, 50 counterexamples, and equation skeleton checks

python fourth_regression_tests.py
OK: fourth regression tests passed — 20 complex cases, ambiguity handling, and area-aware forbidden-equation checks

python final_quality_tests.py
OK: final quality tests passed — 7 final condition-branch corrections with area-aware checks

python expression_variation_tests.py
OK: expression variation tests passed — robust natural-language variants for final expert templates
```

## UI / live smoke

```text
python tools/ui_smoke_test.py
passed

python tools/ui_app_test_smoke.py
skipped_missing_streamlit in this execution environment

python live_smoke_test.py
API key 없음 상태 fallback passed

python -m compileall -q .
success
```

## 반영 확인

- 정보 부족 문제는 풀이 추천을 중단하고 체크리스트를 표시합니다.
- 입문자 모드는 단계별 접기/펼치기 결과 구조를 제공합니다.
- 적용식과 비적용식에 초보자용 설명을 붙입니다.
- 오답노트/복습에서 자주 틀리는 실수 유형 Top 5를 표시합니다.
- 배포용 ZIP에서 개인 DB와 GPT 로그를 제외합니다.
