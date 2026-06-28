# 개인용 모바일 웹앱 배포 가이드

이 앱은 다중 사용자 SaaS가 아니라 개인용 Streamlit 모바일 웹앱입니다. 회원가입, 결제, 관리자 페이지 없이 URL + 앱 비밀번호 방식으로 보호합니다.

## 추천 구성

- 앱 호스팅: Render 또는 Railway
- 저장소: Supabase/Postgres 권장, 로컬 테스트는 SQLite 가능
- 보안: `APP_PASSWORD`, `OPENAI_API_KEY`, `DATABASE_URL`을 환경변수/secrets로 설정
- 접속: HTTPS URL을 스마트폰 Chrome/Safari에서 사용

## Render 배포 예시

1. GitHub 저장소에 이 프로젝트를 업로드합니다.
2. Render에서 New Web Service를 생성합니다.
3. Build Command:

```bash
pip install -r requirements.txt
```

4. Start Command:

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

5. Environment Variables에 다음을 설정합니다.

```bash
APP_PASSWORD=원하는_앱_비밀번호
OPENAI_API_KEY=선택사항
DATABASE_URL=postgresql://...  # Supabase/Postgres 사용 시
```

6. 배포 후 제공되는 HTTPS URL로 스마트폰에서 접속합니다.

## Streamlit Community Cloud 배포 예시

1. GitHub 저장소 연결
2. Main file path: `app.py`
3. Secrets에 다음 형태로 입력

```toml
APP_PASSWORD="원하는_앱_비밀번호"
OPENAI_API_KEY=""
DATABASE_URL=""
```

로컬 SQLite만 쓰는 배포는 플랫폼 재시작/재배포 시 데이터 유지가 보장되지 않을 수 있습니다. 오답노트 보존이 중요하면 Supabase/Postgres 사용을 권장합니다.

## 로컬 실행

```bash
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## 배포 체크리스트

- [ ] 앱 URL이 HTTPS인지 확인
- [ ] 앱 접속 시 비밀번호 화면이 표시되는지 확인
- [ ] API key 값이 화면/로그에 노출되지 않는지 확인
- [ ] 문제 분석이 API key 없이도 작동하는지 확인
- [ ] 오답노트 저장/검색/내보내기가 작동하는지 확인
- [ ] 모바일 Safari/Chrome에서 카드가 세로로 잘 배치되는지 확인
