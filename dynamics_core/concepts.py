from __future__ import annotations

METHODS = [
    "운동학",
    "뉴턴 제2법칙 F=ma",
    "일-에너지 원리",
    "충격량-운동량",
    "원운동 조건",
    "강체 평면운동",
    "상대속도/순간중심",
    "복합 풀이",
]

GOALS = [
    "자동 추정",
    "속도",
    "가속도",
    "시간",
    "위치/변위",
    "힘",
    "장력/마찰력",
    "에너지/일",
    "충돌 후 속도",
    "각속도/각가속도",
    "토크",
    "접촉 유지 조건",
]

CUE_LABELS = {
    "time": "시간 정보",
    "distance": "거리/변위 정보",
    "constant_accel": "등가속도 가능성",
    "projectile": "포물선/투사 운동",
    "incline": "경사면/빗면",
    "force": "힘/하중/수직항력",
    "mass": "질량",
    "tension": "줄/장력/도르래",
    "pulley_connected": "연결된 물체/도르래 계",
    "friction": "마찰 있음",
    "no_friction": "마찰 없음/무시",
    "height": "높이 변화",
    "spring": "스프링/용수철",
    "collision": "충돌/반발계수",
    "no_collision": "충돌 아님/충돌 전만 언급",
    "impulse": "충격량/짧은 시간 큰 힘",
    "momentum": "운동량",
    "angular_momentum": "각운동량",
    "circular": "원운동/곡률반지름",
    "normal_tangent": "법선-접선 좌표계",
    "polar": "극좌표계",
    "rotation": "회전/각속도/각가속도",
    "no_rotation": "회전 없음",
    "translation_only": "순수 병진운동",
    "rolling": "순수 구름/굴림",
    "sliding": "미끄럼/활주",
    "torque": "토크/모멘트",
    "fixed_axis": "고정축 회전",
    "rigid_body": "강체 물체",
    "relative_motion": "상대운동/상대속도",
    "instant_center": "순간중심",
    "variable_force": "위치에 따라 변하는 힘/그래프",
    "air_resistance": "공기저항/drag 고려",
    "no_air_resistance": "공기저항 무시",
    "nonconservative_work": "비보존력/손실 일",
}

ALL_CUES = list(CUE_LABELS.keys())

SUPPORTED_PROBLEM_TYPES = [
    "직선 운동학", "포물선 운동", "곡선 운동학", "법선-접선 좌표계", "극좌표계 운동", "상대운동",
    "질점의 F=ma", "경사면", "연결된 물체와 도르래", "마찰", "일-에너지 원리",
    "보존력과 비보존력", "충격량-운동량", "충돌", "각운동량", "원운동",
    "강체 고정축 회전", "강체 일반 평면운동", "순수 구름", "미끄럼 구름", "순간중심", "상대속도와 상대가속도",
    "수평면 블록-매달린 물체", "경사면 블록-매달린 물체", "질량 있는 도르래", "움직도르래",
    "평평한 커브", "경사진 커브", "원뿔진자", "위치 함수 운동학", "위치 의존 힘", "탄환-막대 충돌",
]
