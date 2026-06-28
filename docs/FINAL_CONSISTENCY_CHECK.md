# Final Consistency Check

코드 위치: `dynamics_core/consistency_guard.py`

최종 consistency check는 다음 순서 뒤에 실행된다.

1. 규칙 기반 템플릿 선택
2. GPT 후보 reconciliation/template rebuild
3. forbidden formula guard
4. **final consistency check**

## 검사 항목

- pure rolling인데 `v_G = ωR 적용 불가`가 핵심 경고로 남아 있지 않은가?
- sliding rotation인데 `v_G = ωR`, `a_G = αR`이 적용식에 있지 않은가?
- frictionless인데 `f = μN`이 적용식에 있지 않은가?
- 직교좌표인데 극좌표식이 적용식에 있지 않은가?
- 극좌표인데 필요한 e_r/e_θ 식이 빠져 있지 않은가?
- tension 문제인데 N 식만 단독 출력되지 않는가?
- normal force 문제인데 T 식만 단독 출력되지 않는가?
- banked curve인데 flat curve 식만 단독 출력되지 않는가?
- bullet rotating collision인데 포물선/1D 선운동량식만 우선 출력되지 않는가?
- 특정 전문 template이 선택됐는데 applicable_equations가 비어 있지 않은가?

## 코드 플래그

최종 guard가 실행되면 blueprint에 다음 속성을 설정한다.

- `forbidden_formula_guard_applied = True`
- `consistency_check_passed = True`

테스트는 이 두 플래그와 적용식/비적용식 영역을 함께 검사한다.

## 최종 문서-코드 일치 보강 항목

최종 출력 직전 `apply_final_consistency_guard`는 다음을 추가로 보장한다.

- `pure_rolling`이고 `slip_present=False`이면 `v_G = ωR`, `a_G = αR`은 적용식에 남고, “적용 불가” 계열 문구는 비적용식/주의사항에서 제거한다.
- `without/no/does not skid/slip` 표현은 양성 skid/slip 토큰보다 우선한다.
- `track/rail + bottom + normal force/법선반력`은 `N - mg = mv²/R`, `N = mg + mv²/R`을 적용식에 둔다.
- `cartesian_position_vector=True`이면 극좌표 적용식은 제거하고 `r(t)=x(t)i+y(t)j`, `v(t)=dr/dt`, `a(t)=d²r/dt²`을 적용식에 둔다.
- `banked_curve=True`이면 평평한 커브식 `N=mg`, `μ_s ≥ v²/(gR)`은 적용식에 둘 수 없다.
