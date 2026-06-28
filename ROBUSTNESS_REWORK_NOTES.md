# 6차 검토 후 전반적 품질 고도화 보정 노트

## 핵심 변경 요약

이번 보정은 특정 문장 몇 개를 하드코딩하는 방식이 아니라, 공통 자연어 의미 정규화 계층과 물리 상황 우선순위를 추가해 같은 물리 상황이 다양한 표현으로 입력되어도 같은 구조로 분류되도록 개선했습니다.

## 추가된 공통 정규화 계층

새 파일 `dynamics_core/semantic_normalizer.py`를 추가했습니다. 이 모듈은 다음 표현군을 공통 의미 플래그로 묶습니다.

- 속도/속력/speed/velocity와 최대·최소 속도 표현
- 줄/끈/실/로프/string/rope/cord
- 최저점/가장 아래/맨 아래/bottom/lowest point
- 최고점/가장 위/top/highest point
- 미끄러짐/slip/slipping/not pure rolling
- 회전/돈다/돌아간다/spin/rotate
- 마찰 없음/smooth/frictionless/no friction/ignore friction/neglect friction
- 경사진 커브/banked curve/뱅크 커브
- 원뿔진자 구조 단서
- 직교좌표 위치벡터 r(t)=...i+...j와 극좌표 r, θ 구분
- 탄환/총알 + 회전강체 + 고정축 충돌 단서

## 물리 상황 우선순위 보강

다음 우선순위를 명시적으로 반영했습니다.

1. `미끄럼 있음`은 `구른다`보다 우선합니다. 미끄럼이 있으면 `v_G = ωR`, `a_G = αR`을 적용식 영역에 두지 않습니다.
2. `smooth/frictionless/ignore friction`은 `μ` 또는 `friction` 단어보다 우선합니다. 명시적 마찰 무시 조건이면 `f = 0`입니다.
3. 줄/끈/실/로프 문제의 수직 원운동에서는 장력 `T`를 사용하고, 트랙/레일 문제에서는 수직항력 `N`을 사용합니다.
4. `i, j, \hat{i}, \hat{j}` 위치벡터는 직교좌표 미분으로 처리하고, 극좌표 템플릿은 `θ/theta/e_r/e_θ/polar` 단서가 명확할 때 우선합니다.
5. `탄환/총알 + 박힘 + 회전판/원판/막대/바퀴 + 고정축`은 선운동량보다 기준점 각운동량 보존을 우선합니다.
6. 원뿔진자는 단어 자체뿐 아니라 `줄/끈/로프 + 매단 물체 + 수평 원운동 + 수직/연직 각도` 구조로 감지합니다. 조건이 부족하면 확정하지 않고 “원뿔진자 가능성 있음”을 표시합니다.

## 추가된 테스트

새 pytest 테스트 파일을 추가했습니다.

- `tests/test_existing_suites.py`: 기존 script-style 테스트를 pytest에서 자동 발견되도록 감싼 래퍼
- `tests/test_semantic_robustness.py`: 핵심 7개 유형별 자연어 표현 변형 테스트

`tests/test_semantic_robustness.py`는 7개 핵심 유형 각각 최소 30개 이상의 표현 변형을 포함합니다.

- 경사진 커브: 30개
- 원뿔진자/원뿔진자 후보: 30개
- 미끄럼 동반 회전/구름: 30개
- 수직 원운동: 30개
- 수평면 블록 + 매달린 물체의 마찰 조건: 30개
- 위치벡터/극좌표 분기: 30개
- 탄환-회전강체 충돌: 30개

총 pytest 기준 216개 테스트가 자동 발견되어 통과합니다.

## 테스트 실행 결과

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

pytest -q
223 passed
```

## 커버리지

`coverage run -m pytest -q && coverage report -m` 기준 전체 테스트 커버리지는 95%입니다. 상세 내용은 `COVERAGE_REPORT.txt`에 저장했습니다.

## 여전히 남는 한계

본 앱은 전문가 템플릿 기반 풀이 골격 생성기입니다. 다음은 여전히 완전 자동화 범위 밖입니다.

- 그림에서 기하 관계를 자동으로 읽는 기능
- 복잡한 다물체 시스템의 모든 부호/좌표 자동 결정
- 임의 형상 강체의 관성모멘트 자동 유도
- 비선형 미분방정식의 완전 자동 해석해 생성
- 교재 그림과 텍스트가 함께 필요한 문제의 완전 자동 정답 산출

이런 경우 앱은 가능한 후보 유형, 부족한 조건, 적용하면 안 되는 식을 분리해서 안내하는 것을 목표로 합니다.
