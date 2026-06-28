# Forbidden Formula Table

최종 출력 직전 guard가 검사해야 할 식/템플릿 충돌 표입니다.

| template_id / 상황 | 적용식 영역에서 금지 | 허용 위치 | 이유 |
|---|---|---|---|
| pure_rolling | `v_G = ωR 적용 불가`, `a_G = αR 적용 불가`, sliding_rotation 확정 | 주의사항에서도 핵심 경고로 반복 금지 | 접촉점 미끄럼이 없음 |
| sliding_rotation | `v_G = ωR`, `a_G = αR`, 순수 구름 확정 | not_applicable에 “적용 불가”로 표시 | 접촉점 미끄럼 있음 |
| cartesian_position_vector | e_r/e_θ 극좌표식 단독 | not_applicable 경고 | i/j 또는 <x,y> 성분 미분 문제 |
| polar_motion | 단순 i/j 성분 미분식만 출력 | 보조 설명 | 기저벡터 변화항 필요 |
| conical_pendulum | `ΣM_G = I_Gα` 우선 적용, `T cosθ`, `T sinθ` 누락 | not_applicable | 질점 원운동 |
| vertical_circle_string | N 식만 단독 | not_applicable | 줄/끈 문제는 장력 T |
| vertical_circle_track | T 식만 단독 | not_applicable | 트랙/레일 문제는 수직항력 N |
| frictionless | `f = μN`, `f = μN_A`, `T - f = m_Aa` 최종식 | 일반식 설명 후 f=0 대입 설명 | 마찰 없음/무시 조건 우선 |
| banked_curve | `N = mg`, `μ_s ≥ v²/(gR)`, `tanθ = v²/(gR)` 단독 | not_applicable 또는 비교 설명 | 경사진 커브 성분 분해 필요 |
| bullet_rotating_collision | 포물선 운동식, 1D 선운동량 보존 단독 | not_applicable | 고정축 기준 각운동량 보존 |
| selected specialist template | 적용식이 빈 상태 | 불가 | 기본식 또는 확인 필요식을 채워야 함 |

Guard는 GPT 결과, template rebuild, forbidden formula filtering 이후 최종 출력 직전에 다시 적용한다.

## 최종 보강 금지 규칙

- 순수 구름: `v_G = ωR 적용 불가`, `a_G = αR 적용 불가`를 현재 문제의 핵심 비적용식처럼 출력하지 않는다.
- 원뿔진자 후보: `ΣM_G = I_Gα`를 핵심 적용식으로 출력하지 않는다.
- 경사진 커브: `N = mg`, `μ_s ≥ v²/(gR)`를 적용식으로 단독 출력하지 않는다.
- 수직 원운동 트랙 최저점: `T - mg = mv²/R`만 단독 출력하지 않는다.
- 직교좌표 위치벡터: `e_r`, `e_θ`, `theta_dot` 기반 극좌표식을 우선 출력하지 않는다.
