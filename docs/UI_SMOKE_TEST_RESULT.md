# UI Smoke Test Result

- Status: **passed**
- Browser click test: **attempted_but_blocked_by_sandbox_browser_policy**
- Streamlit AppTest: **see docs/UI_APPTEST_RESULT.json**
- Note: This scripted smoke test validates the UI contract without requiring a browser session. In this sandbox Chromium navigation to localhost was blocked; run `streamlit run app.py` for local visual QA.

## Source/contract checks
- student_mode_default: passed
- expert_debug_gated: passed
- friendly_empty_message: passed
- api_key_not_logged: passed
- markdown_export_button: passed
- html_export_button: passed
- equation_export_button: passed
- friendly_errors: passed

## Example library checks
- 순수 구름: 순수 구름 운동 / FBD=pure_rolling / equations=3
- 미끄럼 동반 회전: 미끄럼을 동반한 구름 운동 / FBD=sliding_rotation / equations=3
- 원뿔진자: 원뿔진자 원운동 문제 / FBD=conical_pendulum / equations=4
- 수직 원운동 장력: 수직 원운동 최저점 장력/수직항력 문제 / FBD=vertical_circle_string / equations=2
- 수직 원운동 수직항력: 수직 원운동 최저점 장력/수직항력 문제 / FBD=vertical_circle_track / equations=2
- 경사진 커브 최대속도: 마찰 있는 경사진 커브 최대속도 문제 / FBD=banked_curve / equations=3
- 경사진 커브 최소속도: 마찰 있는 경사진 커브 최소속도 문제 / FBD=banked_curve / equations=5
- 수평면 블록-도르래: 수평면 블록 + 매달린 물체 연결 문제 / FBD=block_pulley / equations=4
- 위치벡터 미분: 위치 함수 기반 입자 운동학 / FBD=cartesian_vector / equations=5
- 탄환-회전강체 충돌: 탄환-막대 충돌/각운동량 보존 문제 / FBD=bullet_rotating_body_collision / equations=5

## Export checks
- markdown: passed (804 bytes)
- html: passed (999 bytes)
- equations_only: passed (194 bytes)

## Records checks
- save: passed
- favorite: passed
- delete: passed