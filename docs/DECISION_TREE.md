# Dynamics Decision Tree

이 decision tree는 템플릿 우선순위의 기준입니다. 표면 키워드보다 물리 상황과 금지식 위험을 먼저 본다.

## 1. 좌표/운동학 단서 우선

1. `i`, `j`, `i-hat`, `j-hat`, `<x,y>`, `(x,y)`, position vector가 있으면 `cartesian_position_vector`.
2. `e_r`, `e_θ`, `polar`, `radial/transverse`, r(t)와 θ(t)가 함께 있으면 `polar_motion`.
3. i/j 성분이 있으면 theta 단순 언급보다 직교좌표가 우선.

## 2. 구름/접촉 운동

1. rolling + no/without/not slip/skid 계열이면 `pure_rolling`.
2. rolling/rotating + slip/skid 발생 계열이면 `sliding_rotation`.
3. banked curve 문맥의 sliding outward/downward는 rolling slip으로 해석하지 않는다.

## 3. 원운동 계열

1. string/rope/cord + vertical circle + bottom/top/tension이면 수직 원운동 장력 템플릿.
2. track/rail + vertical circle + normal force면 수직 원운동 수직항력 템플릿.
3. string/cord + horizontal circle + angle with vertical이면 `conical_pendulum`.
4. car/vehicle + banked/sloped/slanted/inclined curve면 banked curve 계열.
5. flat/level curve + friction이면 평평한 커브.

## 4. 충돌 계열

1. projectile/bullet + sticks/embeds/remains + rod/disk/wheel + hinge/pivot/fixed axle/angular velocity after impact면 `bullet_rotating_body_collision`.
2. 위 단서가 없으면 일반 충격량-운동량/반발계수 후보.

## 5. 마찰 조건

1. frictionless/friction-free/negligible/ignore/neglect/마찰 없음/마찰 무시이면 f=0.
2. μ, rough, friction present만 있고 무시 조건이 없으면 마찰 있음.
3. rough와 friction neglected가 충돌하면 명시적 무시 조건 우선 + 경고.

## 6. 요청량/위치 단서

- tension/장력 → T 우선.
- normal force/수직항력 → N 우선.
- maximum/highest/fastest/greatest/최고/가장 큰 → 최대속도.
- minimum/lowest/slowest/최저/가장 작은 → 최소속도.
- bottom/최저점/최하점 → 최저점.
- top/꼭대기/최고점 → 최고점.

## 7. 정보 부족 정책

단서가 충돌하거나 부족하면 단일 템플릿으로 억지 확정하지 않는다. 후보 유형, 필요한 추가 조건, 쓰면 안 되는 식을 함께 출력한다.
