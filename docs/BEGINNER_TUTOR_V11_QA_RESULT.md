# Beginner Tutor v1.1 QA Result

## 목적

v1.1 패치는 학생 풀이 오개념 탐지가 공통 키워드(`줄`, `매달린`, `장력`, `수평`, `각도`)에 과민반응하여 원뿔진자/단진자/단일 줄 문제에 도르래 전용 경고를 표시하는 문제를 막기 위한 안전 패치입니다.

## 반영 사항

- 오개념 탐지 기준을 단순 키워드가 아니라 최종 문제 유형 우선으로 변경했습니다.
- 원뿔진자 문제에서는 도르래 전용 오개념 경고를 비활성화했습니다.
- 단진자 문제에서는 도르래 전용 오개념 경고를 비활성화했습니다.
- 단일 줄 평형 문제에서는 도르래 전용 오개념 경고를 비활성화했습니다.
- 블록-도르래로 확정된 문제에서는 가속도 관계 및 매달린 물체 B 운동방정식 누락 경고를 유지했습니다.
- 애매한 줄 문제에서는 경고 대신 `확인 필요` 질문을 표시합니다.

## 추가 회귀 테스트

추가 파일: `tests/test_beginner_v11_misconception_scoping.py`

| ID | 검증 내용 | 결과 |
|---|---|---|
| TEST-006 | 원뿔진자에서 도르래 오개념 경고 금지 | 통과 |
| TEST-007 | 블록-도르래에서는 가속도 관계/매달린 물체 식 누락 경고 허용 | 통과 |
| TEST-008 | 단일 줄 평형 문제에서 도르래 경고 금지 | 통과 |
| TEST-009 | 단진자 문제에서 도르래 경고 금지 | 통과 |
| TEST-010 | 애매한 줄 문제에서는 경고 대신 확인 필요 출력 | 통과 |

## 대표 기대 동작

### 원뿔진자

입력:

```text
질량 m인 물체가 길이 L인 줄에 매달려 수직선과 각도 θ를 이루며 수평 원운동한다. 각속도를 구하라.
```

적용식:

```text
T cosθ = mg
T sinθ = mω²r
r = L sinθ
ω² = g/(L cosθ)
```

출력되지 않음:

```text
도르래 문제의 가속도 관계 누락
두 물체 가속도 관계 누락
블록-도르래 연립방정식 누락
```

### 블록-도르래

입력 문제:

```text
마찰 없는 수평면 위 블록 A와 매달린 블록 B가 질량 없는 줄과 도르래로 연결되어 있다. 가속도와 장력을 구하라.
```

학생 풀이:

```text
블록 A에는 T = m_Aa를 쓰고, 블록 B에는 힘 식을 세우지 않았다.
```

오개념 경고:

```text
도르래 문제의 가속도 관계 누락
매달린 물체 B의 운동방정식 누락
```

적용식에 포함되지 않음:

```text
T cosθ = mg
T sinθ = mω²r
r = L sinθ
```

### 애매한 줄 문제

입력:

```text
줄에 매달린 물체가 움직인다. 가속도를 구하라.
```

출력:

```text
확인 필요: 이 문제가 도르래로 연결된 두 물체 문제라면 두 물체의 가속도 관계를 세워야 합니다. 하지만 현재 문장만으로는 도르래 문제인지 확정하기 어렵습니다.
```

출력되지 않음:

```text
오개념 경고: 도르래 문제의 가속도 관계를 누락했습니다.
```

## 검증 결과

```text
pytest -q
432 passed

coverage report -m
TOTAL 4818 statements, 95% coverage

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

`tools/ui_app_test_smoke.py`는 현재 실행 환경에 Streamlit 패키지가 없어 `skipped_missing_streamlit`로 기록됩니다. 실제 사용 환경에서 `pip install -r requirements.txt` 후 다시 실행할 수 있습니다.
