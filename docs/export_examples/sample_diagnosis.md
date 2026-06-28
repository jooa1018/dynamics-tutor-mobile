# DynaTutor 풀이 진단 요약

## 문제
A stone tied to a string moves in a horizontal circle making angle theta with vertical. Find angular speed.

## 문제 유형
원뿔진자 원운동 문제

## FBD / 좌표축
- 중력 mg
- 장력 T

## 적용식
- T cosθ = mg
- T sinθ = mv²/r
- T sinθ = mω²r
- r = L sinθ
- ω² = g/(L cosθ)
- ω² = g / (L cosθ)

## 이 문제에서 쓰면 안 되는 식
- ΣM_G = I_Gα : 원뿔진자는 질점 원운동으로 우선 처리
- 강체 일반 평면운동 템플릿

## 단계별 풀이
1. 질량 m만 떼어 FBD를 그린다.
2. 장력 T를 수직/수평 성분으로 나눈다.
3. 수직 방향은 평형, 수평 방향은 구심가속도를 적용한다.
4. r = L sinθ를 연결한다.

## 학생 풀이
T cos theta = mg