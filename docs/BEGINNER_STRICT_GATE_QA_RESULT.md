# Beginner strict gate QA result

## Summary

이번 패치는 동역학 입문자가 문제 키워드만 보고 공식을 확정하는 위험을 줄이기 위해 추가되었습니다.

## Added tests

- `tests/test_beginner_strict_condition_gates.py`

## Key cases

정보 부족으로 처리:

- `블록이 경사면 위에 있다. 가속도를 구하라.`
- `원운동하는 물체의 장력을 구하라.`
- `원통이 굴러간다. 가속도를 구하라.`
- `A cylinder is rolling. Find acceleration.`
- `A car moves on a curve. Find maximum speed.`
- `공이 원운동한다. 속도를 구하라.`

식 제시 허용:

- `원통이 미끄러지지 않고 굴러간다.`
- `A cylinder rolls without slipping.`
- `A disk rolls without slipping down an incline.`
- `원통이 미끄러지며 굴러간다.`
- `A cylinder is rolling while slipping.`
- `A disk slips as it rolls.`
- `줄에 매단 공이 수직 원운동을 한다. 최저점에서 장력을 구하라.`
- `줄에 매단 공이 수직 원운동을 한다. 최고점에서 장력을 구하라.`
- `평평한 원형 도로에서 자동차가 미끄러지기 직전 최대 속도를 구하라.`

## Test result

```text
pytest -q
402 passed

coverage report -m
TOTAL 4319 statements, 95% coverage

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

## Distribution hygiene

배포 ZIP에서는 다음을 제외합니다.

- `data/study_records.sqlite3`
- `data/gpt_call_log.jsonl`
- `data/ai_assist_cache.json`
- `.env`, `.streamlit/secrets.toml`
- `__pycache__`, `.pytest_cache`, `.coverage`
