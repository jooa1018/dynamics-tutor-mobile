# Physics Ontology for Dynamics Solver Trainer

이 문서는 앱의 자연어 분류, 템플릿 선택, GPT 후보 검증, forbidden formula guard, 회귀 테스트가 따라야 하는 기준 문서입니다. 문장별 패치를 피하고, **물리 상황 중심**으로 문제를 분류하는 것을 목표로 합니다.

## 공통 출력 구조

모든 전문 템플릿은 다음 영역을 구분해야 합니다.

- `problem_type`: 판별된 문제 유형
- `evidence`: 판별 근거 표현
- `applicable_equations`: 현재 문제에서 실제로 사용할 식
- `not_applicable_equations`: 현재 문제에서 쓰면 안 되는 식 또는 조건부 보류식
- `cautions`: 풀이상 주의사항
- `ambiguity_notes`: 정보 부족/충돌 시 확인할 조건
- `suppressed_templates`: 배제한 일반 템플릿

## 1. `pure_rolling`

- 문제 유형명: 순수 구름 운동
- 물리 상황: 접촉점에서 상대운동이 없는 강체 구름 운동.
- 핵심 판별 단서: rolling/rolls/구름/구른다 + no slip/without slipping/without skidding/미끄러지지 않음/접촉점 미끄럼 없음.
- 보조 판별 단서: wheel, disk, cylinder, 원통, 원반, 바퀴, rough incline.
- 혼동 단서: slipping이라는 단어가 있어도 `without slipping`, `no slip occurs`, `not slipping as it rolls`는 순수 구름이다.
- 적용식:
  - `v_G = ωR`
  - `a_G = αR`
  - 에너지 문제이면 `mgh = 1/2mv_G² + 1/2I_Gω²`
- 비적용식:
  - `v_G = ωR 적용 불가` 경고를 핵심 경고로 출력 금지
  - `a_G = αR 적용 불가` 경고를 핵심 경고로 출력 금지
  - 미끄럼 동반 회전으로 확정 금지
- 필요한 추가 조건: 반지름 R, 관성모멘트 I_G, 경사각 또는 높이 조건.
- 힘 기호 규칙: 접촉면이 있으면 N, 마찰은 보통 정지마찰 f_s 후보.
- 좌표계 규칙: 경사면 평행/수직 축, 회전 양의 방향.
- 마찰 조건 규칙: 미끄럼 없음이므로 운동마찰 f_k를 무조건 적용하지 않는다.
- 대표 예시: `rolling without slipping`, `without slip`, `without skidding`, `no slip at the contact point`, `미끄러지지 않고 구른다`.
- 반례: `rolling while slipping`, `rolls and slips`, `there is slip at the contact point`, `구르면서 미끄러짐`.
- 모호할 때 출력: 접촉점 미끄럼 여부 확인 필요. 순수 구름 조건은 확인 후 적용.

## 2. `sliding_rotation`

- 문제 유형명: 미끄럼 동반 회전/구름 운동
- 물리 상황: 강체가 회전하면서 접촉점에서 미끄러지는 경우.
- 핵심 판별 단서: rolling/rotating + slip/skid/미끄럼 발생/접촉점 미끄러짐.
- 적용식:
  - `ΣF = ma_G`
  - `ΣM_G = I_Gα`
  - `f_k = μ_kN` 또는 마찰 조건 확인
- 비적용식:
  - `v_G = ωR` 적용식 금지
  - `a_G = αR` 적용식 금지
  - 순수 구름으로 확정 금지
- 필요한 추가 조건: μ_k, 경사각, I_G, R.
- 반례: `without slipping`, `no slip occurs`, `not slipping as it rolls`.
- 모호할 때 출력: 미끄럼 여부가 명확하지 않으면 순수 구름식을 확정하지 않고 확인 조건 출력.

## 3. `cartesian_position_vector`

- 문제 유형명: 직교좌표 위치벡터 미분
- 물리 상황: 질점 위치가 i, j 또는 <x,y>, (x,y) 성분으로 주어진 운동학 문제.
- 핵심 판별 단서: `r = x(t)i + y(t)j`, `r vector`, `i-hat`, `j-hat`, `<x,y>`, `(x,y)`, position vector.
- 적용식:
  - `r(t) = x(t)i + y(t)j`
  - `v(t) = dr/dt`
  - `a(t) = d²r/dt²`
- 비적용식:
  - 극좌표 가속도식 단독 출력 금지
  - `e_r`, `e_θ` 기반 식 우선 출력 금지
- 좌표계 규칙: i, j 성분이면 theta 단어가 다른 문장에 있어도 직교좌표 우선.
- 모호할 때 출력: 극좌표가 명시되었는지, e_r/e_θ 단서가 있는지 확인.

## 4. `polar_motion`

- 문제 유형명: 극좌표 운동학
- 핵심 판별 단서: polar, 극좌표, e_r, e_θ, radial/transverse, r(t)와 θ(t)가 함께 주어짐.
- 적용식:
  - `v = r_dot e_r + r theta_dot e_theta`
  - `a = (r_ddot - r theta_dot²)e_r + (r theta_ddot + 2r_dot theta_dot)e_theta`
- 비적용식: i/j 성분이 명확한 문제를 극좌표로 확정 금지.

## 5. `conical_pendulum`

- 문제 유형명: 원뿔진자
- 물리 상황: 줄/끈/로프에 매단 질점이 수평 원운동하고 줄이 수직선과 각도를 이룸.
- 핵심 단서: conical pendulum, conical motion, 원뿔 운동, string/cord + angle with vertical + horizontal circle.
- 적용식:
  - `T cosθ = mg`
  - `T sinθ = mω²r`
  - `T sinθ = mv²/r`
  - `r = L sinθ`
- 비적용식: `ΣM_G = I_Gα`를 핵심 적용식으로 출력 금지.
- 필요한 추가 조건: L, θ 기준, 수평 원운동 여부.
- 모호할 때 출력: 원뿔진자 가능성, 수평 원운동 여부와 각도 기준 확인 필요. 기본 원뿔진자 식은 후보식으로 제시.

## 6. `vertical_circle_string_bottom/top/angle`

- 문제 유형명: 수직 원운동 — 줄/끈 장력 문제
- 핵심 단서: string/rope/cord/줄/끈/실/로프 + vertical circle/수직 원운동 + tension/장력.
- 최저점 적용식:
  - `T - mg = mv²/R`
  - `T = mg + mv²/R`
- 최고점 적용식:
  - `T + mg = mv²/R`
  - 최소 팽팽 조건: `T = 0`, `v_min = √(gR)`
- 비적용식: N 식만 단독 출력 금지.
- 모호할 때 출력: 지지 방식이 줄인지 트랙인지 확인.

## 7. `vertical_circle_track_bottom/top/angle`

- 문제 유형명: 수직 원운동 — 트랙/레일 수직항력 문제
- 핵심 단서: rail/track/원형 레일/원형 트랙 + normal force/수직항력.
- 최저점 적용식:
  - `N - mg = mv²/R`
  - `N = mg + mv²/R`
- 최고점 접촉 유지:
  - `N + mg = mv²/R`
  - 최소 접촉 조건: `N = 0`, `mg = mv²/R`, `v_min = √(gR)`
- 비적용식: T 식만 단독 출력 금지.
- 모호할 때 출력: rail + tension처럼 힘 단서가 충돌하면 후보식 둘 다 제시하고 지지 방식 확인.

## 8. `loop_the_loop_contact`

- 문제 유형명: loop-the-loop 접촉 유지/최소 높이
- 핵심 단서: loop-the-loop, maintain contact, minimum height, 접촉 유지, 원형 트랙 꼭대기.
- 적용식:
  - 최고점 접촉 한계: `N = 0`
  - `mg = mv²/R`
  - `v_min = √(gR)`
  - 마찰 없으면 에너지 보존으로 높이 h 연결
- 비적용식: 임의각도 장력 문제로만 처리 금지.

## 9. `frictionless_pulley_block`

- 문제 유형명: 마찰 없는 수평면 블록-매달린 물체
- 핵심 단서: table/surface/수평면 + hanging mass/block + pulley/tied + frictionless/friction-free/negligible friction/마찰 없음.
- 적용식:
  - `f = 0`
  - `N_A = m_Ag`
  - `T = m_Aa`
  - `m_Bg - T = m_Ba`
- 비적용식:
  - `f = μN_A`
  - `T - f = m_Aa`를 최종 적용식으로 유지 금지
- 마찰 조건 규칙: rough/μ가 있어도 friction neglected가 명시되면 f=0 우선.

## 10. `frictional_pulley_block`

- 문제 유형명: 마찰 있는 수평면 블록-매달린 물체
- 적용식:
  - `N_A = m_Ag`
  - `f = μN_A = μm_Ag`
  - `T - f = m_Aa`
  - `m_Bg - T = m_Ba`
- 비적용식: 블록 A에 `m_Ag - T = m_Aa` 적용 금지.

## 11. `banked_curve_frictionless`

- 문제 유형명: 마찰 없는 경사진 커브
- 핵심 단서: banked curve + frictionless/no friction.
- 적용식:
  - `N cosθ = mg`
  - `N sinθ = mv²/R`
  - `tanθ = v²/(gR)`
- 비적용식: `N = mg`, 평평한 커브 마찰계수 식.

## 12. `banked_curve_with_friction_max_speed`

- 문제 유형명: 마찰 있는 경사진 커브 최대속도
- 핵심 단서: banked/sloped/slanted/inclined curve + friction/μ_s + maximum/highest/fastest/greatest/최고/최대/가장 큰/바깥쪽/위쪽.
- 적용식:
  - `N cosθ - f sinθ = mg`
  - `N sinθ + f cosθ = mv²/R`
  - `f = μ_sN`
- 비적용식: `N = mg`, `μ_s ≥ v²/(gR)`, `tanθ = v²/(gR)` 단독.

## 13. `banked_curve_with_friction_min_speed`

- 문제 유형명: 마찰 있는 경사진 커브 최소속도
- 핵심 단서: banked/sloped/slanted/inclined curve + friction/μ_s + minimum/lowest/slowest/최저/최소/가장 작은/안쪽/아래쪽.
- 적용식:
  - `N cosθ + f sinθ = mg`
  - `N sinθ - f cosθ = mv²/R`
  - `f = μ_sN`
- 비적용식: 마찰 없는 설계속도식 단독.

## 14. `flat_curve_friction`

- 문제 유형명: 평평한 커브 마찰 문제
- 적용식:
  - `N = mg`
  - `f_s = mv²/R`
  - `f_s ≤ μ_sN`
  - `μ_s ≥ v²/(gR)`
- 반례: banked/sloped/inclined/slanted curve.

## 15. `bullet_rotating_body_collision`

- 문제 유형명: 탄환/투사체-회전강체 충돌
- 핵심 단서: bullet/projectile/탄환/투사체 + hits/strikes/sticks/embeds/remains/lodges/붙는다/박힌다 + rod/bar/disk/wheel/pivot/hinge/fixed axle + angular velocity after collision.
- 적용식:
  - `H_O(before) = H_O(after)`
  - `m_b v r = I_totalω`
- 비적용식:
  - 포물선 운동 우선 출력 금지
  - 단순 1D 선운동량 보존식만 단독 출력 금지
- 모호할 때 출력: 고정축/핀 기준인지, 충돌 후 붙는지, 충돌점 거리 r 확인.

## 16. `general_impulse_momentum`

- 문제 유형명: 일반 충격량-운동량/충돌
- 핵심 단서: collision/impact/impulse/restitution, 고정축 회전강체 단서 없음.
- 적용식:
  - `∫Fdt = Δp`
  - 선운동량 보존은 외부 충격량이 무시될 때만
  - 반발계수 있으면 `e = (v2f - v1f)/(v1i - v2i)`
- 비적용식: 고정축 회전 충돌에서는 단순 선운동량 보존 단독 금지.

## 17. `general_planar_rigid_body`

- 문제 유형명: 일반 강체 평면운동
- 적용식:
  - `ΣF = ma_G`
  - `ΣM_G = I_Gα`
  - `v_B = v_A + ω × r_B/A`
- 비적용식: 더 구체적인 순수 구름, 미끄럼 회전, 회전충돌, 순간중심 단서가 있으면 일반 템플릿이 후순위.

## 문서-코드 일치 보강: 최종 수락 전 잔여 표현군

이번 보강부터 ontology의 대표 표현은 `tests/test_docs_code_alignment_final.py`에서 실제 런타임 출력과 대조한다. 특히 다음 규칙은 코드의 `semantic_normalizer.py`, `fourth_templates.py`, `consistency_guard.py`에 반영되어야 한다.

1. `without any skidding`, `does not skid`, `skid 없이`는 `pure_rolling`으로 분류하고 `v_G = ωR`, `a_G = αR`을 적용식에 둔다.
2. `conical path`, `sweeps out a cone`은 원뿔진자 후보 이상으로 분류하고 `T cosθ = mg`, `T sinθ = mω²r`, `r = L sinθ`을 제시한다.
3. `inclined roadway curve`, `sloped turn`, `upper speed limit`, `maximum permissible velocity`는 경사진 커브 최대속도 후보로 분류한다.
4. `lower most point`, `제일 아래`가 원형 트랙/레일 문맥과 함께 있으면 수직 원운동 최저점 수직항력 문제로 분류한다.
5. `particle position equals (x(t), y(t))`는 직교좌표 위치벡터 미분 문제로 분류한다.
6. 순수 구름 출력에는 현재 문제가 미끄럼 상황인 것처럼 보이는 모순적 주의문을 남기지 않는다.

## Final acceptance micro-patch ontology alignment

The runtime ontology now explicitly distinguishes:

- **positive contact slip** (`has slip`, `there is slipping`, `slip exists`) -> `sliding_rotation`.
- **negated contact slip** (`no slip exists`, `there is no slip`, `has no point-of-contact slip`) -> `pure_rolling`.
- **cone-shaped path / trajectory with string or bob** -> `conical_pendulum` candidate/template.
- **minimum permissible / lower permissible banked-curve speed** -> `banked_curve_with_friction_min_speed`.
- **smooth horizontal plane + hanging block + pulley** -> frictionless horizontal block-pulley system.
