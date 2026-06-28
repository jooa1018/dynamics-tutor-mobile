# 표현 변형 견고성 최종 보정 노트

## 목적

5차 최종 개선안 이후 남아 있던 문제는 정해진 예시 문장에는 강하지만, 실제 학생이 자연스럽게 바꿔 쓰는 표현에서는 일부 템플릿 분기가 흔들릴 수 있다는 점이었습니다.

이번 보정은 새 대형 기능 추가가 아니라, 기존 4차/최종 구조의 `applicable_equations`, `not_applicable_equations`, `cautions`, `suppressed_templates`, `ambiguity_notes` 분리 구조를 유지하면서 자연어 표현 변형을 더 안정적으로 처리하는 마지막 품질 보정입니다.

## 보정 항목

### 1. 경사진 커브 속도/속력 표현

다음 표현을 같은 계열로 인식합니다.

- 최대속도 / 최대 속도 / 최대속력 / 최대 속력
- 허용 가능한 최대 속력 / 허용 최대 속력
- 최소속도 / 최소 속도 / 최소속력 / 최소 속력
- 아래로 미끄러지지 않는 최소 속력
- 경사진 커브 / 경사 커브 / 뱅크 커브 / banked curve

마찰 없음이 명시되지 않았고 최대/최소 속력 한계를 묻는 banked curve 문제는 정지마찰 한계 문제로 우선 분기합니다.

### 2. 원뿔진자 구조 기반 감지 강화

`원뿔진자`라는 단어가 없어도 다음 조합이면 원뿔진자 템플릿을 우선 적용합니다.

- 줄/끈/실/로프/string/cord/rope
- 매단 질점 또는 매단 물체
- 수평 원운동 또는 수평면에서 원을 그림
- 줄이 수직/연직선과 θ를 이룸

조건이 일부 부족하면 `원뿔진자 가능성 있음 — 수평 원운동 여부와 각도 기준 확인 필요`를 `ambiguity_notes`에 표시합니다.

### 3. 미끄럼 동반 회전/구름 표현 확장

다음 표현을 순수 구름이 아니라 미끄럼 동반 회전으로 처리합니다.

- 미끄러지며 내려가고 회전도 한다
- 미끄러지면서 돈다
- 미끄러지며 회전한다
- 구르면서 미끄러진다
- rolling with slip
- sliding while rotating
- slips as it rotates

이 경우 `v_G = ωR`, `a_G = αR`은 적용식이 아니라 `not_applicable_equations`에만 표시됩니다.

### 4. 수직 원운동 최저점/줄 표현 확장

다음 표현을 최저점으로 인식합니다.

- 최저점
- 가장 아래점
- 가장 낮은 점
- 가장 낮은 위치
- 아래 위치
- bottom
- lowest point

다음 표현은 장력 문제로 처리합니다.

- 줄
- 끈
- 실
- 로프
- string
- rope
- cord

줄/끈/실/로프 문제에서는 `T - mg = mv²/R`, `T = mg + mv²/R`을 사용하고, 트랙/레일 문제에서는 수직항력 `N`을 사용합니다.

### 5. 마찰 없음 영어 표현 강화

다음 표현은 마찰 없음으로 처리합니다.

- smooth
- smooth horizontal table
- frictionless
- no friction
- neglect friction
- ignore friction
- 매끄러운 / 매끈한 / 마찰 없음 / 마찰 없는 / 마찰을 무시

마찰계수 μ가 언급되어도 `마찰 무시`가 명시되면 `f = 0`이 우선됩니다.

### 6. 위치벡터 r(t)와 극좌표 분리

`r(t)=...i+...j`, `r(t)=...î+...ĵ`, `position vector`, `위치벡터`는 직교좌표 위치벡터 미분으로 처리합니다.

극좌표 템플릿은 다음 단서가 함께 있을 때 우선 적용합니다.

- θ 또는 theta
- e_r, e_θ
- polar
- 극좌표
- radial/transverse
- r(t), θ(t)가 함께 주어짐

### 7. 탄환-회전강체 충돌 표현 확장

다음 표현을 탄환-회전강체 충돌로 인식합니다.

- 탄환 / 총알 / bullet
- 박힌다 / 박혀서 함께 돈다 / 가장자리에 박힘
- 회전판 / 원판 / 원반 / 바퀴 / 막대 / 진자막대
- 고정축 / fixed axis
- 충돌 직후 각속도

이 경우 `H_O(before) = H_O(after)`를 우선 적용하고, 단순 1차원 선운동량 보존식은 적용식 영역에서 배제합니다.

## 추가 테스트

새 테스트 파일:

```bash
python expression_variation_tests.py
```

검증 범위:

- 경사진 커브 최대속력/최소속력 표현 변형
- 원뿔진자 표현 변형 및 모호성 안내
- 미끄럼 동반 회전 표현 변형
- 수직 원운동 최저점과 string/rope 표현
- smooth horizontal table 마찰 없음
- r(t)=...i+...j 위치벡터
- 총알-회전판 충돌

## 전체 테스트 명령

```bash
python regression_tests.py
python expert_regression_tests.py
python fourth_regression_tests.py
python final_quality_tests.py
python expression_variation_tests.py
```

이번 보정 후 모든 테스트가 통과해야 합니다.
