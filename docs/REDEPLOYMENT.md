# 재배포 방법

## 코드 수정 후 재배포

1. 코드 수정 및 테스트 실행

```bash
pytest -q
python tools/ui_smoke_test.py
python live_smoke_test.py
```

2. GitHub에 push합니다.
3. Render/Railway/Streamlit Cloud가 자동 배포되도록 설정했으면 빌드 로그를 확인합니다.
4. 수동 배포 방식이면 플랫폼 대시보드에서 redeploy를 누릅니다.

## 환경변수 변경 후 재배포

- `APP_PASSWORD` 변경: 환경변수 수정 후 서비스 재시작
- `OPENAI_API_KEY` 변경: 환경변수 수정 후 서비스 재시작
- `DATABASE_URL` 변경: 기존 오답노트 데이터를 백업한 뒤 변경

## 비밀번호 변경

1. 배포 플랫폼의 Environment Variables 또는 Secrets에서 `APP_PASSWORD` 값을 변경합니다.
2. 앱을 재시작/재배포합니다.
3. 기존 브라우저 세션은 새로고침 후 새 비밀번호를 입력해야 합니다.
