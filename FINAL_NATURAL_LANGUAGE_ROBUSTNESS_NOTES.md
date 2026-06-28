# 최종 자연어 견고성 보강 노트

## 반영 목적

추가 검토에서 확인된 공식 테스트 밖의 실제 학생식 표현을 회귀 테스트에 포함하고, 단순 문장 하드코딩이 아니라 공통 의미 정규화와 템플릿 우선순위를 보강했다.

## 주요 수정

1. **순수 구름 / 미끄럼 동반 회전 부정 표현 분리**
   - `without slip`, `no slip occurs`, `slipping does not occur`, `does not skid`는 순수 구름으로 우선 처리한다.
   - `with slip`, `slips at the point of contact`, `contact point slips`, `미끄럼을 가지고 구른다`, `slip하며 굴러간다`는 미끄럼 동반 회전으로 처리한다.
   - 순수 구름에는 `v_G = ωR`, `a_G = αR`을 적용식으로 둔다.
   - 미끄럼 동반 회전에는 위 두 식을 비적용식으로만 둔다.

2. **탄환/투사체-회전강체 충돌 표현군 확장**
   - `projectile strikes a hinged bar and sticks`, `투사체가 피벗된 막대에 충돌하여 붙는다`를 고정축 기준 각운동량 보존 문제로 처리한다.
   - `H_O(before) = H_O(after)`, `m_b v r = I_totalω`가 적용식으로 출력된다.

3. **직교좌표 위치벡터 / 극좌표 분기 강화**
   - `r vector = ... i + ... j`, `position is <3t,2t^2>`, `r=(3t,2t^2)`는 직교좌표 위치벡터 미분으로 처리한다.
   - 단순히 `theta`가 다른 문장에 언급되어도 i, j 성분이 있으면 극좌표로 보내지 않는다.

4. **원뿔진자 영어 자연문 표현 강화**
   - `stone tied to a string moves in a horizontal circle making angle theta with vertical` 및 `cord inclined from vertical` 계열 표현을 원뿔진자로 처리한다.
   - 후보 수준이라도 기본식이 비지 않도록 `T cosθ = mg`, `T sinθ = mω²r`, `r = L sinθ`를 제공한다.

5. **수직 원운동 최저점 / 힘 기호 충돌 처리**
   - `cord + vertical loop + tension at bottom`은 장력식 `T - mg = mv²/R`, `T = mg + mv²/R`을 출력한다.
   - `rail + tension`처럼 물리 모델과 힘 이름이 충돌하면 N/T 단일 확정 대신 확인 필요 안내를 출력한다.

6. **경사진 커브 표현군 보강**
   - `inclined curve`, `maximum safe speed`, `maximum velocity before slipping outward`, `경사진 곡선도로`, `최소 speed` 계열을 banked curve로 처리한다.
   - 경사진 커브에서 평평한 커브식 `N = mg`, `μ_s ≥ v²/(gR)`가 적용식으로 나오지 않도록 유지한다.

7. **마찰 없음 / 수평면 블록-도르래 표현 보강**
   - `friction-free`, `friction is neglected`, `마찰은 없다`는 f=0을 우선한다.
   - `rough table but friction is neglected`처럼 상충 표현이 있어도 무시 조건이 우선이다.

8. **loop-the-loop / 접촉 유지 후보 보강**
   - `minimum height to maintain contact`, `원형 트랙 꼭대기 접촉 유지`, `loop-the-loop minimum height frictionless`는 최고점 접촉 유지 조건으로 안내한다.
   - `N = 0`, `mg = mv²/R`, `v_min = √(gR)`가 적용식으로 출력된다.

## 추가 테스트

`tests/test_final_natural_language_robustness.py` 추가.

- 29개 추가 회귀 테스트
- `expected_template_id` 성격의 문제 유형/제목 검증
- 적용식 비어 있음 방지
- must_include / must_not_include 방식 검증
- 순수 구름식, 미끄럼 금지식, 직교/극좌표 분리, T/N 힘 기호 충돌, 마찰 없음 우선순위 검증

## 실행 결과

```bash
python regression_tests.py
python expert_regression_tests.py
python fourth_regression_tests.py
python final_quality_tests.py
python expression_variation_tests.py
pytest -q
```

결과:

```text
OK: all 2nd-rework regression tests passed
OK: expert regression tests passed — 100 representative cases, 50 counterexamples, and equation skeleton checks
OK: fourth regression tests passed — 20 complex cases, ambiguity handling, and area-aware forbidden-equation checks
OK: final quality tests passed — 7 final condition-branch corrections with area-aware checks
OK: expression variation tests passed — robust natural-language variants for final expert templates
284 passed in 2.19s
TOTAL 2949 statements, 95% coverage
```

## 남은 한계

- 그림 기반 기하 해석은 자동으로 수행하지 않는다.
- 복잡한 다물체 계의 수치 연립 계산은 풀이 골격 중심으로 제공한다.
- GPT live smoke test는 사용자가 `OPENAI_API_KEY`를 직접 설정한 환경에서 실행해야 한다.

## Final residual natural-language robustness pass

This pass adds 11 final acceptance regression cases requested after the `final_nl_robust` review.

### Fixed meaning groups

- Pure rolling: `without any slipping`, `without any slip`, `no slip occurs`, `slipping does not occur`, Korean `미끄러지지 않고 회전하며`, and `접촉점에서 미끄러지지 않는다` now normalize before positive slip detection.
- Sliding rotation: `rolling while slipping`, `rolls and slips`, `rolling and slipping`, `rotating while slipping`, Korean `구르면서 미끄러짐` / `미끄러지며 회전` now force sliding-rotation treatment.
- Banked curve: `sloped curve`, `inclined road curve`, `highest speed`, Korean `최고 속도`, `최저 속도` map to banked-curve max/min templates.
- Conical pendulum: Korean `원뿔 운동`, `원뿔형 운동`, and related phrasing now routes to conical-pendulum candidate/template instead of generic dynamics.
- Vertical circular track: `원형 레일의 최하점에서 수직항력` now routes to the vertical-circle track bottom normal-force skeleton.

### Final consistency check

`apply_fourth_rework_templates()` now applies a final consistency guard after template selection. It removes contradictions such as pure-rolling constraints inside sliding-rotation applicable equations, frictional formulas under frictionless conditions, and polar formulas under Cartesian vector conditions. It also fills a basic formula set if a selected template would otherwise have empty applicable equations.
