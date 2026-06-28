# Beginner Tutor v1.2 QA Result

## 목적

v1.2는 기존 v1.1의 오개념 탐지 스코핑 안전장치를 유지하면서, 실제 학생이 자연스럽게 입력하는 표현 다양성을 강화한 패치입니다.

핵심 원칙은 다음과 같습니다.

- 동의어는 넓게 인식한다.
- 문제 유형 확정은 여러 단서 조합으로 신중하게 한다.
- 오개념 경고는 확실할 때만 출력한다.
- 애매하면 경고 대신 확인 질문을 출력한다.
- 단진자, 원뿔진자, 단일 줄 평형 문제에서는 도르래 전용 오개념 경고를 출력하지 않는다.

## 추가 구현

- `dynamics_core/lexicon.py` 추가
  - `ROPE_TERMS`: 줄, 실, 끈, 로프, 케이블, 와이어, cord, string, rope, cable
  - `REST_TERMS`: 정지, 가만히, 움직이지 않음, 평형, stationary, at rest, equilibrium
  - `PENDULUM_TERMS`: 작은 각도, 작은 진폭, 소진동, 살짝 흔들림, pendulum, small oscillation
  - `HANGING_TERMS`: 매달린, 매단, 달린, 천장에 연결된, hanging, suspended
  - `CONICAL_TERMS`: 연직선/수직선과 각도, 원을 그리며 돈다/돎, 수평 원운동, conical pendulum
- 구어체 정규화 추가
  - `장력?` → `장력을 구하라`
  - `주기?` → `주기를 구하라`
  - `각속도?` → `각속도를 구하라`
  - `돎` → `돈다`
  - `살짝 흔들림` → `작은 진폭으로 흔들린다`
  - `가만히 있음` → `가만히 있다`
- 단일 줄 평형 / 단진자 / 원뿔진자 special case 판별을 동의어 사전 기반으로 보강
- 원뿔진자 ambiguous 문장(`확인`, `여부`, `정보가 없다`, `명확하지 않다`)은 확정식 대신 후보/확인 필요 상태 유지
- `로프`, `실`, `끈`만으로 도르래 구조를 확정하지 않도록 유지

## 신규 테스트

추가 파일:

```text
테스트: tests/test_beginner_v12_synonym_robustness.py
```

테스트 항목:

1. TEST-011: `실` 표현을 단일 줄 평형으로 인식
2. TEST-012: `끈` 표현을 단일 줄 평형으로 인식
3. TEST-013: `작은 진폭` 표현을 단진자로 인식
4. TEST-014: `소진동` 표현을 단진자로 인식
5. TEST-015: `원을 그리며 돈다` 표현을 원뿔진자로 인식
6. TEST-016: `실에 매단 추가 살짝 흔들림. 주기?` 구어체 단진자 처리
7. TEST-017: `추가 실에 달려서 가만히 있음. 장력?` 구어체 단일 줄 평형 처리
8. TEST-018: `로프에 매달린 물체가 ... 원을 그리며 돎. 각속도?` 구어체 원뿔진자 처리
9. TEST-019: 동의어 추가 후 단진자에서 도르래 오개념 경고 재발 방지
10. TEST-020: 애매한 `실` 문제는 경고 대신 확인 필요 출력
11. 동의어 사전 모듈이 공통 용어를 중앙 관리하는지 확인

## 대표 결과

### 단일 줄 평형

입력:

```text
질량 m인 물체가 천장에 연결된 실에 매달려 가만히 있다. 장력을 구하라.
```

결과:

```text
문제 유형: 단일 줄 평형 문제
적용식: ΣF_y = 0, T = mg
도르래 문제의 가속도 관계 누락: 출력 안 됨
```

### 단진자

입력:

```text
길이 L의 실에 매단 추가 작은 진폭으로 흔들린다. 주기를 구하라.
```

결과:

```text
문제 유형: 단진자 문제
적용식: T_period = 2π√(L/g)
도르래 전용 경고: 출력 안 됨
```

### 원뿔진자

입력:

```text
질량 m인 추가 길이 L의 실에 매달려 연직선과 θ만큼 기울어진 채 원을 그리며 돈다. 각속도를 구하라.
```

결과:

```text
문제 유형: 원뿔진자 원운동 문제
적용식: T cosθ = mg, T sinθ = mω²r, r = L sinθ, ω² = g/(L cosθ)
도르래 전용 경고: 출력 안 됨
```

### 애매한 실 문제

입력:

```text
실에 매달린 물체가 움직인다. 가속도를 구하라.
```

결과:

```text
확인 필요: 이 문제가 도르래로 연결된 두 물체 문제라면 두 물체의 가속도 관계를 세워야 합니다. 하지만 현재 문장만으로는 도르래 문제인지 확정하기 어렵습니다.
오개념 경고: 출력 안 됨
```

## 전체 검증 결과

```text
pytest -q
443 passed

coverage run -m pytest -q
443 passed

coverage report -m
TOTAL 4980 statements, 95% coverage

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
