# 3차 개선 반영 노트

## 목표

3차 개선의 목표는 기존의 “문제 방향 추천” 수준을 넘어, 대표 동역학 문제에서 학생이 바로 식을 세울 수 있는 **맞춤 방정식 골격**을 제공하는 것입니다.

## 핵심 변경

1. `dynamics_core/expert_templates.py` 추가
   - 대표 유형별 FBD, 좌표계, 핵심 방정식, 보조식, 적용 조건, 경고를 주입합니다.

2. `modeling.py` 개선
   - 기존 일반 골격 생성 뒤 expert template layer를 적용합니다.

3. `parser.py` 보완
   - 마찰 없음/매끄러운 면 표현 추가
   - 공기저항/drag/속도 비례 저항 표현 추가
   - 극좌표 `theta`, `r(t)`, `theta_dot` 표현 추가
   - 충돌 부정 표현과 회전 부정 표현 보강
   - 한국어 단위/조사 처리 유지

4. `expert_regression_tests.py` 추가
   - 대표 문제 100개
   - 자연어 반례 50개
   - 핵심 방정식 골격 테스트

## 대표 유형별 방정식 골격

- 이상적 도르래: `m1g - T = m1a`, `T - m2g = m2a`
- 질량 있는 도르래: `(T1 - T2)R = Iα`, `a = αR`, `T1 ≠ T2`
- 평평한 커브: `N = mg`, `f_s = mv²/R`, `μ_s ≥ v²/(gR)`
- 수직 원운동: `mg + N = mv²/R`, `N = 0`, `v_min = √(gR)`
- 속도 비례 저항: `m dv_x/dt = -c v_x`, `m dv_y/dt = -mg - c v_y`
- 극좌표: `v = r_dot e_r + r theta_dot e_theta`, `a = (r_ddot - r theta_dot²)e_r + (r theta_ddot + 2r_dot theta_dot)e_theta`
- 순수 구름: `mgh = 1/2mv_G² + 1/2I_Gω²`, `v_G = ωR`, `a_G = αR`
- 순간중심: `v_A = ω r_A/IC`, `v_B = ω r_B/IC`
- 충돌/반발계수: `m1v1i + m2v2i = m1v1f + m2v2f`, `e = (v2f - v1f)/(v1i - v2i)`
- 각운동량: `ΣM_O = dH_O/dt`, `H_O1 = H_O2`, `H_O = r × mv`

## 검증 결과

```bash
python regression_tests.py
# OK: all 2nd-rework regression tests passed

python expert_regression_tests.py
# OK: expert regression tests passed — 100 representative cases, 50 counterexamples, and equation skeleton checks
```

## 남은 한계

- 그림 기반 기하해석은 자동화하지 않았습니다.
- 완전한 심볼릭 솔버는 아닙니다.
- 문제 조건이 모호하면 여러 템플릿이 동시에 출력될 수 있습니다.
- 실제 수치 답은 사용자가 방정식을 정리하거나 계산기로 확인해야 합니다.
