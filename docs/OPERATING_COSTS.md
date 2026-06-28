# 예상 운영 비용

실제 비용은 배포 플랫폼, DB 사용량, OpenAI API 호출량에 따라 달라집니다.

## 저비용 구성

- Streamlit Community Cloud 또는 무료 호스팅
- Supabase Free
- OpenAI API는 필요할 때만 수동 호출

월 비용: 0원~소액 API 사용료

## 안정형 개인용 구성

- Render/Railway 등 유료 Web Service
- Supabase Free 또는 Pro
- OpenAI API 선택 호출

월 비용: 앱 서버 비용 + DB 비용 + OpenAI 사용량

## 비용 절감 원칙

- 기본 분석은 규칙 기반으로 실행
- GPT는 `GPT로 자세히 설명받기` 또는 애매한 문제에서만 사용
- 동일 입력은 캐시 가능
- 오답노트는 Supabase/Postgres에 저장하고 CSV/JSON 백업 병행
