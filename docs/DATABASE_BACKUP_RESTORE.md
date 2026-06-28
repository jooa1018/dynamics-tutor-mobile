# 오답노트 저장소, 백업, 복구

## 저장 방식

기본값은 SQLite입니다.

```bash
DYNAMICS_SQLITE_PATH=data/study_records.sqlite3
```

클라우드 배포에서 데이터 보존을 중시하면 Supabase/Postgres를 권장합니다.

```bash
DATABASE_URL=postgresql://user:password@host:5432/postgres
```

`DATABASE_URL`이 있고 `psycopg`가 설치되어 있으면 앱은 Postgres를 사용합니다. 없거나 접속할 수 없으면 SQLite fallback으로 동작합니다.

## Supabase 설정

1. Supabase 프로젝트를 만듭니다.
2. Project Settings → Database에서 connection string을 복사합니다.
3. 배포 플랫폼 secrets에 `DATABASE_URL`로 저장합니다.
4. `docs/SUPABASE_SCHEMA.sql`을 SQL editor에서 실행하거나 앱 첫 저장 시 자동 생성되도록 둡니다.

## 백업

앱의 오답노트 탭에서 다음을 다운로드할 수 있습니다.

- CSV 내보내기
- JSON 백업
- Markdown 내보내기

정기적으로 JSON 백업을 다운로드하는 것을 권장합니다.

## 복구

현재 앱은 안전을 위해 UI에서 직접 JSON 복구를 자동 실행하지 않습니다. 복구는 다음 방식 중 하나를 사용합니다.

1. Supabase 대시보드에서 CSV/SQL import
2. SQLite 파일을 백업 파일로 교체
3. 필요 시 `storage.py`의 `save_record` 구조에 맞춰 복구 스크립트 작성

## 데이터가 사라질 수 있는 경우

- 무료/임시 컨테이너의 로컬 파일 시스템
- 앱 재배포 시 ephemeral storage 사용
- `data/study_records.sqlite3`를 저장하지 않고 컨테이너 재생성

이 위험이 있으면 반드시 Postgres/Supabase를 사용하세요.
