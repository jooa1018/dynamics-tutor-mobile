# 배포용 파일 정리 원칙

배포용 ZIP에는 개인 학습 기록, GPT 호출 로그, API cache, `.env` 파일이 포함되면 안 됩니다.

제외 대상:

- `data/*.sqlite3`
- `data/*.db`
- `data/gpt_call_log.jsonl`
- `data/ai_cache.sqlite3`
- `data/*.jsonl`
- `logs/`
- `exports/`
- `.env`
- `.streamlit/secrets.toml`
- `__pycache__/`
- `.pytest_cache/`
- `.coverage`

앱은 실행 시 필요한 SQLite 파일을 자동 생성합니다. 샘플 문제 파일만 배포물에 포함합니다.
