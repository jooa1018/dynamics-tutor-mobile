# Mobile Web App QA Result

## Scope

This QA pass verifies the personal mobile web app packaging layer added on top of the existing DynaTutor engine.

## Added checks

- App password helper and `.env` loader
- Mobile tab contract: 문제 분석 / 오답노트 / 복습 / 설정
- Extended wrong-note fields: difficulty, wrong reasons, review due date, needs review
- CSV/JSON/Markdown backup export
- SQLite fallback storage
- Optional Postgres/Supabase `DATABASE_URL` detection
- README and deployment documentation presence

## Commands run

```bash
pytest -q
python regression_tests.py
python expert_regression_tests.py
python fourth_regression_tests.py
python final_quality_tests.py
python expression_variation_tests.py
python tools/ui_smoke_test.py
python live_smoke_test.py
python -m compileall -q .
coverage run -m pytest -q
coverage report -m
```

## Result

- pytest: 366 passed
- regression suites: passed
- UI smoke contract: passed
- live smoke without API key: fallback passed
- compileall: success
- coverage: 96%

## Browser/mobile device note

This package contains the source and deployment instructions. Actual external URL, HTTPS verification, iPhone Safari QA, and Android Chrome QA must be performed after deployment to the selected host because this environment cannot publish a public URL.

## Scope / limitations patch

- 이미지/그림 인식 미지원, 완전 자동 수치 풀이 제한, 3D 강체 운동 미지원, Streamlit 모바일 웹앱 한계를 앱 내부와 README에 고지했습니다.
- 모바일 입력 편의를 위해 기호 입력 도우미와 자주 쓰는 문제 템플릿 버튼을 추가했습니다.
- 3D 강체 운동/자이로스코프/오일러 방정식/관성텐서 입력은 일반 2D 문제로 처리하지 않고 미지원 안내를 표시합니다.
- 추가 테스트: `tests/test_limitations_and_scope.py`, `tests/test_symbol_input_helpers.py`.
