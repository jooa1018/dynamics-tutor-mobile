# Scope / Limitations QA Result

## 추가 검증 범위

- 이미지/그림 직접 인식 미지원 안내가 README, 앱 내부 지원 범위 카드, docs에 표시됨
- 완전 자동 수치 풀이 제한 안내가 README, 결과 화면 계산 지원 수준 카드, docs에 표시됨
- 3D 강체 운동/자이로스코프/오일러 방정식/관성텐서 입력을 현재 미지원 범위로 감지
- 지원 유형별 지원 수준 매트릭스 표시
- Streamlit 모바일 웹앱 한계 고지
- 모바일 기호 입력 도우미와 문제 템플릿 버튼 계약 테스트

## 테스트 명령

```bash
pytest tests/test_limitations_and_scope.py tests/test_symbol_input_helpers.py -q
pytest -q
coverage run -m pytest -q
coverage report -m
```

## 결과

```text
pytest -q: 376 passed
coverage: TOTAL 3949 statements, 96% coverage
```

## 3D 미지원 감지 케이스

- `A rigid body rotates in 3D with angular velocity components omega_x, omega_y, omega_z.`
- `Use Euler's equations to find the precession rate of a gyroscope.`
- `A disk undergoes gyroscopic precession about a vertical axis.`
- `Find the motion using the inertia tensor matrix.`

기대 동작: 2D 공식으로 억지 풀이하지 않고 `현재 미지원 범위: 3차원 강체 운동` 안내를 표시합니다.
