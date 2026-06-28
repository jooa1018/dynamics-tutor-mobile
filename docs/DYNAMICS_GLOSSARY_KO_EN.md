# Dynamics Glossary KO/EN

이 용어 사전은 `semantic_normalizer.py`가 따라야 하는 개념별 표현군입니다. 단어 하나가 아니라 **긍정/부정/반례/우선순위**를 함께 정의합니다.

## 1. 순수 구름 표현

긍정 표현:

- rolling without slipping, rolls without slipping
- without slipping, without slip, without any slipping, without any slip
- without skidding, without any skidding
- no slip, no slipping, no slip occurs, no slipping occurs
- slipping does not occur, slip does not occur, does not slip, does not skid
- not slipping as it rolls, rolling but not slipping
- no slip at the contact point, no slipping at the point of contact
- 접촉점에서 미끄러지지 않음, 접촉점에서 미끄럼 없음
- 미끄러지지 않고 구름, 미끄러지지 않고 회전하며 이동
- 미끄럼 없이 회전, 미끄럼 없이 구름

핵심 의미: 접촉점 상대운동 없음. `v_G = ωR`, `a_G = αR` 적용.

반례 표현:

- rolling while slipping, rolling with slip, rolls and slips
- there is slip at the contact point, skidding while rolling
- 구르면서 미끄러짐, 접촉점에서 미끄러짐

우선순위: `without/no/not ... slip/skid` 표현은 `slip/skid` 토큰보다 우선한다.

## 2. 미끄럼 동반 회전 표현

긍정 표현:

- rolling with slip, rolling with slipping, rolling while slipping
- rolls and slips, slips while rolling, rotating while slipping
- there is slip at the contact point, contact point slips
- slips at the point of contact, point of contact slips
- skidding while rolling, rolls but skids
- 구르면서 미끄러짐, 미끄러지며 회전, 미끄럼을 동반한 구름
- 접촉점에서 미끄러짐, slip하며 굴러감

핵심 의미: 접촉점 미끄럼 있음. `v_G = ωR`, `a_G = αR` 일반 적용 금지. `ΣF = ma_G`, `ΣM_G = I_Gα`, `f_k = μ_kN` 후보.

반례/부정: without slipping, no slip, not slipping as it rolls.

## 3. slip 문맥 구분

rolling contact slip 단서:

- wheel, disk, cylinder, rolling, rotating, contact point, point of contact, skidding while rolling

banked curve slip 단서:

- car, vehicle, curve, bank, road, outward, inward, up the bank, down the bank, sliding outward/inward

규칙: banked curve 문맥의 slipping outward/downward는 구름 접촉 미끄럼이 아니다. 경사진 커브 출력에는 `v_G = ωR 적용 불가` 같은 rolling guard를 섞지 않는다.

## 4. 힘 기호 사전

T 계열: tension, tensile force, string force, rope force, cord force, 장력, 줄의 힘, 끈의 힘, 로프의 힘.

N 계열: normal force, normal reaction, track force, rail force, 수직항력, 법선반력, 레일이 미는 힘, 트랙이 미는 힘.

f 계열: friction, static friction, kinetic friction, 마찰력, 정지마찰력, 운동마찰력.

우선순위:

- 줄/끈/로프/string/cord/rope/tension이면 T 우선.
- 트랙/레일/normal force/수직항력이면 N 우선.
- rail과 tension처럼 서로 충돌하면 모호성 경고를 출력하고 T/N 후보식을 모두 제시.

## 5. 경사진 커브 용어

경사진 커브 표현:

- banked curve, banked road, banked roadway, curve with bank angle
- inclined curve, sloped curve, slanted curve, canted curve
- inclined road curve, sloped road curve
- 경사진 커브, 경사진 도로 커브, 경사 도로 커브
- 경사진 곡선도로, 뱅크 커브, 뱅크 도로, 경사각이 있는 커브

최대속도 표현:

- maximum speed, maximum velocity, maximum safe speed
- maximum allowable speed, maximum allowable velocity
- highest speed, fastest speed, greatest speed, upper speed limit
- highest speed before sliding outward/up the bank
- 최고 속도, 최고 속력, 최대 속도, 최대 속력
- 허용 최대 속도, 허용 최대 속력, 가장 큰 속도, 가장 큰 속력
- 바깥쪽/위쪽으로 미끄러지기 직전

최소속도 표현:

- minimum speed, minimum velocity, lowest speed, slowest speed
- lower speed limit, minimum speed before sliding down the bank
- 최저 속도, 최저 속력, 최소 속도, 최소 속력
- 가장 작은 속도, 가장 작은 속력
- 안쪽/아래쪽으로 미끄러지기 직전

## 6. 원뿔진자 용어

원뿔진자 표현:

- conical pendulum, conical motion, conical movement
- moves like a cone, bob tied to a cord moves like a cone
- string makes angle with vertical, cord inclined from vertical
- mass/bob moves in a horizontal circle
- 원뿔진자, 원뿔 운동, 원뿔형 운동, 원뿔 모양 운동, 원뿔꼴 운동
- 원뿔 형태로 회전, 끈에 달린 물체가 원뿔 운동
- 줄/끈과 수직선이 각도를 이루며 수평 원운동

핵심 구조: string/cord/rope/줄/끈 + vertical/수직선 각도 + horizontal circle/수평 원운동.

## 7. 위치벡터 / 좌표계 용어

직교좌표 위치벡터:

- `r = x(t)i + y(t)j`, r vector, vector r, position vector
- position is `<x(t), y(t)>`, particle has position `(x(t), y(t))`
- i, j, i-hat, j-hat, unit vector i/j, <x,y>, (x,y)
- 위치벡터, 직교좌표, i성분, j성분

극좌표:

- polar coordinates, r(t), θ(t), radial/transverse
- e_r, e_θ, r-dot, theta-dot, 극좌표, 반지름 방향, 횡방향

우선순위: i/j, i-hat/j-hat, <x,y>, (x,y)가 명확하면 직교좌표 우선. r 하나나 theta 단순 언급만으로 극좌표 확정 금지.

## 8. 탄환/투사체-회전강체 충돌 용어

표현:

- bullet, projectile, strikes, hits, embeds, sticks, remains in, lodges in, becomes embedded
- disk, wheel, rod, bar, fixed axle, fixed pivot, hinge, hinged bar, pivoted rod, pinned at one end
- angular velocity just after collision, angular speed after impact
- 탄환, 투사체, 박힌다, 붙는다, 충돌 후 함께 회전
- 고정축, 피벗, 힌지, 한쪽 끝이 고정된 막대, 충돌 후 각속도

적용 원리: 고정점 O 기준 각운동량 보존. `H_O(before) = H_O(after)`, `m_b v r = I_totalω`.

금지: projectile 단어만 보고 포물선 운동으로 보내지 않는다. 고정축 반력이 있으면 단순 1D 선운동량 보존을 단독 우선 적용하지 않는다.

## 최종 문서-코드 일치 보강 표현군

### 순수 구름 skid 부정 표현
다음 표현은 `pure_rolling`으로 정규화한다. `skid/skidding` 토큰보다 부정 표현을 먼저 판정한다.

- `without skidding`, `without any skidding`, `does not skid`, `does not skid while rolling`
- `rolling and does not skid`, `not skidding as it rolls`, `no skidding`, `no skidding occurs`
- `skid 없이`, `skidding 없이`, `스키딩 없이`, `미끄럼 없이`, `접촉점에서 미끄러지지 않음`

우선순위: `without/no/does not` 계열은 양성 `skid/slip` 토큰보다 항상 우선한다.

### 원뿔진자 conical-path 표현
다음 표현은 `conical_pendulum` 또는 최소한 원뿔진자 후보로 정규화한다.

- `conical path`, `traces a conical path`, `traces a cone`, `sweeps out a cone`
- `moves in a conical path`, `forms a cone`, `string forms a cone`
- `bob sweeps out a cone`, `mass sweeps out a cone`
- `원뿔 경로`, `원뿔 궤적`, `원뿔 형태의 경로`, `원뿔 모양 궤적`

### 경사진 커브 roadway/turn 표현
다음 표현은 `banked_curve` 계열로 정규화한다.

- `inclined roadway curve`, `sloped roadway curve`, `slanted roadway curve`, `banked roadway`, `canted roadway`
- `road curve with bank angle`, `curve on an inclined roadway`, `roadway curve with static friction`
- `sloped turn`, `banked turn`, `inclined turn`, `canted turn`
- `maximum permissible velocity`, `maximum permissible speed`, `upper velocity limit`, `maximum allowed speed/velocity`

### 수직 원운동 최저점 표현
다음 표현은 bottom/최저점으로 정규화한다.

- `lowermost point`, `lower most point`, `lowest position`, `bottommost point`, `bottom point`
- `at the bottom of the circular track`, `at the lower end of the vertical circle`
- `제일 아래`, `제일 낮은 점`, `최하점`, `최저점`, `바닥점`, `하단`

### 직교좌표 위치벡터 괄호 표현
다음 표현은 직교좌표 위치벡터 미분 문제로 정규화한다.

- `particle position equals (x(t), y(t))`, `particle position is (x(t), y(t))`
- `position equals (x(t), y(t))`, `position is (x(t), y(t))`
- `coordinates are (x(t), y(t))`, `위치가 (x(t), y(t))`, `좌표가 (x(t), y(t))`

## Final acceptance micro-patch additions

### Contact slip / no-slip priority

Positive contact-slip expressions now treated as sliding rotation:

- there is slipping at the point of contact
- slipping exists at the point of contact
- slip exists at the point of contact
- the rolling disk has slip at the contact point
- the wheel has slipping at the contact patch
- point-of-contact slip exists while rolling

Negated contact-slip expressions now override positive slip tokens and are treated as pure rolling:

- no slip exists at the contact point
- there is no slip at the point of contact
- no point-of-contact slip
- no slipping at the contact point
- contact point has no slip
- contact patch has no slip

### Conical pendulum additions

- cone-shaped trajectory
- cone shaped trajectory
- cone-shaped path
- cone shaped path
- follows a cone-shaped trajectory
- moves in a cone-shaped path
- 끈이 기울어진 채 물체가 수평 원을 그린다
- 끈이 기울어진 채 수평 원운동

### Banked curve speed-limit additions

- minimum permissible speed / velocity
- minimum allowed speed / velocity
- lower permissible speed / velocity
- lower allowed velocity
- canted turn lower permissible velocity
- 커브가 경사져 있고 마찰이 있을 때 최대 허용 속도
- 커브가 경사져 있고 마찰이 있을 때 최소 허용 속도

### Cartesian vector shorthand additions

- particle coords are `<x(t), y(t)>`
- coords are `<x(t), y(t)>`
- coordinates of the particle are `(x(t), y(t))`
- particle coordinates are `(x(t), y(t))`

### Block-pulley frictionless surface additions

- smooth horizontal plane
- smooth horizontal table
- block on a smooth horizontal plane connected to a hanging block over a pulley
