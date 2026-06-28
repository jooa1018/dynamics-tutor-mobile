# 최종 품질 보정 노트

이번 보정은 4차 개선본의 구조를 유지하면서, 최종 검수에서 지적된 7개 조건 분기 문제를 보완한 버전입니다.
핵심 목표는 공식을 더 많이 보여주는 것이 아니라, `applicable_equations`에는 실제 적용 가능한 식만 두고, 문제 상황에 맞지 않는 식은 `not_applicable_equations` 또는 `cautions`로 분리하는 것입니다.

## 반영 사항

### 1. 복합 템플릿의 마찰 없음 조건 반영

수평면 블록 + 매달린 물체, 경사면 블록 + 매달린 물체 템플릿 내부에서 마찰 상태를 세 가지로 분기합니다.

- 마찰 있음: `f = μN`
- 마찰 없음: `f = 0`
- 마찰 조건 불명: 추가 조건 확인 안내

예를 들어 마찰 없는 수평면 블록-매달린 물체 문제에서는 적용식에 다음이 표시됩니다.

- `f = 0`
- `T = m_Aa`
- `m_Bg - T = m_Ba`

반대로 `f = μN_A = μm_Ag`, `T - f = m_Aa`는 적용식 영역에서 제외되고 비적용식 영역에 표시됩니다.

### 2. 경사진 커브 세분화

경사진 커브를 세 유형으로 분리했습니다.

- `banked_curve_frictionless`
- `banked_curve_with_friction_max_speed`
- `banked_curve_with_friction_min_speed`

마찰 있는 최대속도 문제에서는 다음 식을 적용식으로 둡니다.

- `N cosθ - f sinθ = mg`
- `N sinθ + f cosθ = mv²/R`
- `f = μ_sN`

마찰 있는 최소속도 문제에서는 다음 식을 적용식으로 둡니다.

- `N cosθ + f sinθ = mg`
- `N sinθ - f cosθ = mv²/R`
- `f = μ_sN`

`N = mg`, `μ_s ≥ v²/(gR)`, `tanθ = v²/(gR)` 단독 적용은 적용식에서 배제됩니다.

### 3. 원뿔진자 구조 감지 강화

`원뿔진자`라는 단어가 없어도 다음 조합을 감지하면 원뿔진자로 처리합니다.

- 줄/로프
- 매단 질점 또는 매단 물체
- 수평 원운동
- 연직선과 각도 θ

적용식:

- `T cosθ = mg`
- `T sinθ = mv²/r`
- `T sinθ = mω²r`
- 보조식: `r = L sinθ`

강체 회전식 `ΣM_G = I_Gα`는 적용식으로 나오지 않습니다.

### 4. 미끄럼 동반 회전/구름 표현 확장

다음 표현을 순수 구름이 아닌 미끄럼 동반 회전으로 인식합니다.

- 미끄러져 내려가면서 동시에 회전
- 미끄러지면서 회전
- 굴러가지만 미끄러진다
- 미끄럼을 동반한 회전
- sliding and rotating
- rolling with slip

적용식:

- `ΣF = ma_G`
- `ΣM_G = I_Gα`
- `f_k = μ_kN`

`v_G = ωR`, `a_G = αR`은 적용식이 아니라 비적용식/주의사항 영역에만 표시됩니다.

### 5. 위치벡터 r(t)와 극좌표 r, θ 구분

`r(t)=...i + ...j` 또는 `위치벡터` 표현은 직교좌표 위치벡터 미분 문제로 처리합니다.

적용식:

- `r(t) = x(t)i + y(t)j`
- `v(t) = dr/dt`
- `a(t) = d²r/dt²`

극좌표 템플릿은 θ/theta/e_r/e_θ/polar 같은 단서가 함께 있을 때 우선 적용됩니다.

### 6. 탄환-회전강체 충돌 확장

기존 탄환-막대 충돌 템플릿을 탄환-회전강체 충돌로 확장했습니다.
대상은 막대뿐 아니라 원판, 원반, 바퀴, 회전판, 고정축 강체 등을 포함합니다.

적용식:

- `H_O(before) = H_O(after)`
- `m_bvr = I_totalω`
- `m_b v r = I_total ω`

단순 1차원 선운동량 보존식은 적용식으로 나오지 않고, 축 반력 때문에 선운동량 보존이 성립하지 않을 수 있다는 주의사항이 표시됩니다.

### 7. 수직 원운동 위치별 분기

수직 원운동을 세 유형으로 분리했습니다.

- 최고점 접촉 유지/최소속도
- 최저점 장력/수직항력
- 임의 각도에서의 장력/수직항력

최저점 줄 문제 적용식:

- `T - mg = mv²/R`
- `T = mg + mv²/R`

최고점 줄 문제 적용식:

- `최고점: mg + T = mv²/R`
- `mg + T = mv²/R`
- `최소 조건: T = 0`
- `v_min = √(gR)`

임의 각도 줄 문제 적용식:

- `T - mg cosθ = mv²/R`
- `ΣF_t = ma_t`

## 추가 테스트

새 파일 `final_quality_tests.py`를 추가했습니다.

검증 항목:

- 마찰 없는 수평면 블록 + 매달린 물체
- 매끈한 경사면 블록 + 매달린 물체
- 마찰계수 언급 + 마찰 무시 우선순위
- 마찰 있는 경사진 커브 최대속도
- 마찰 있는 경사진 커브 최소속도
- 원뿔진자 표현 변형
- 미끄럼 동반 회전
- 위치벡터 r(t)
- 탄환-원판 충돌
- 수직 원운동 최저점 장력
- 수직 원운동 최고점 최소속도
- 수직 원운동 임의 각도

## 실행 결과

다음 테스트를 통과했습니다.

```bash
python regression_tests.py
python expert_regression_tests.py
python fourth_regression_tests.py
python final_quality_tests.py
```

결과:

```text
OK: all 2nd-rework regression tests passed
OK: expert regression tests passed — 100 representative cases, 50 counterexamples, and equation skeleton checks
OK: fourth regression tests passed — 20 complex cases, ambiguity handling, and area-aware forbidden-equation checks
OK: final quality tests passed — 7 final condition-branch corrections with area-aware checks
```

## 여전히 남는 한계

본 앱은 대표 유형의 풀이 골격을 생성하는 튜터형 도구입니다. 복잡한 그림 기반 기하 해석, 다물체 3차원 운동, 실제 교재 그림 치수 자동 판독, 긴 연립방정식의 완전 자동 수치해석은 제한적입니다. 조건이 부족한 문제는 억지로 템플릿을 확정하지 않고 추가 조건 확인을 안내하는 방향으로 설계했습니다.
