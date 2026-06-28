# DynaTutor · 개인용 모바일 동역학 튜터

DynaTutor는 Python/Streamlit 기반의 개인용 동역학 학습 튜터입니다. 스마트폰 브라우저에서 접속해 문제를 입력하고, 문제 유형, FBD, 적용식, 쓰면 안 되는 식, 단계별 풀이, 오답노트, 복습을 확인할 수 있습니다.

이 앱은 **동역학 문제의 유형을 판별하고 풀이 골격을 안내하는 학습 보조 도구**입니다. 모든 문제의 최종 수치 답을 자동으로 계산하는 완전 자동 문제풀이기는 아닙니다.

이 프로젝트는 다중 사용자 SaaS가 아닙니다. 회원가입, 이메일 로그인, 구글 로그인, 결제, 관리자 페이지는 포함하지 않습니다. 개인 URL + 앱 비밀번호 방식으로 보호합니다.

## 주요 기능

- 동역학 문제 유형 판별
- FBD/좌표축 안내
- 적용 가능한 공식과 쓰면 안 되는 공식 분리
- 학생 풀이 비교
- 오답노트 저장/검색/필터/즐겨찾기/수정/삭제
- 오늘 복습, 즐겨찾기, 최근 오답 복습
- Markdown, CSV, JSON, HTML, 식-only 내보내기
- 선택적 GPT 보조 설명
- API key가 없어도 규칙 기반 분석 가능
- 모바일 세로 화면 기준 카드형 UI
- 단일 앱 비밀번호 보호

## 설치

```bash
pip install -r requirements.txt
cp .env.example .env
```

`.env`에 필요한 값을 설정합니다.

```bash
APP_PASSWORD=your_private_password
OPENAI_API_KEY=
DATABASE_URL=
```

## 실행

```bash
streamlit run app.py
```

스마트폰에서 같은 네트워크의 URL 또는 배포 URL에 접속합니다.

## 앱 비밀번호

`APP_PASSWORD`가 설정되어 있으면 앱 첫 화면에서 비밀번호를 입력해야 합니다. 비밀번호는 코드에 하드코딩하지 않고 환경변수, `.env`, 또는 Streamlit secrets로 관리합니다.

## 화면 구성

앱은 모바일 사용을 기준으로 네 개 탭으로 구성됩니다.

1. **문제 분석**: 문제 입력, 예제 불러오기, 빠른 분석, GPT 설명
2. **오답노트**: 저장된 문제 검색, 필터, 수정, 즐겨찾기, 삭제, 내보내기
3. **복습**: 오늘 복습, 즐겨찾기, 최근 오답, 약점 유형 통계
4. **설정**: 비밀번호/API/저장소 상태, 계산 도우미, 사용 안내, 배포 문서

## 문제 분석 사용법

1. 예제 문제를 선택하거나 직접 문제를 입력합니다.
2. 선택적으로 내 풀이를 입력합니다.
3. **진단 실행**을 누릅니다.
4. 결과 카드에서 문제 유형, 핵심 단서, FBD, 적용식, 비적용식, 단계별 풀이를 확인합니다.
5. 필요한 경우 오답노트에 저장합니다.

## 그림 문제 입력 방법

현재 버전은 이미지/그림을 직접 인식하지 않습니다. 교재 그림에 포함된 치수, 각도, 힘 방향, 접촉 조건, 도르래 연결 구조 등을 텍스트로 입력해야 정확한 진단이 가능합니다.

나쁜 입력:

> 그림과 같은 시스템에서 가속도를 구하라.

좋은 입력:

> 질량 m_A인 블록 A가 마찰 없는 수평면 위에 있고, 질량 m_B인 블록 B가 이상적 도르래에 매달려 있다. 두 물체의 가속도와 장력을 구하라.

입력 전 체크리스트:

- 물체 개수와 각 물체의 질량
- 경사각, 반지름, 끈 길이
- 끈/도르래/레일/트랙/접촉면 구조
- 마찰 있음/없음 및 마찰계수
- 회전축, 피벗, 힌지, 충돌 위치
- 구하려는 값과 운동 방향

## 기호 입력 도우미

모바일에서 θ, ω, μ 같은 특수기호를 직접 입력하기 어렵다면 앱의 **기호 입력 도우미** 버튼을 사용하거나 ASCII 표현을 입력해도 됩니다.

| ASCII 입력 | 의미 |
|---|---|
| theta | θ |
| omega | ω |
| alpha | α |
| mu_s | μ_s |
| mu_k | μ_k |
| sum F | ΣF |
| sum M_G | ΣM_G |
| e_theta | e_θ |
| theta_dot | θ_dot |

앱에는 수평면 블록-도르래, 경사면, 수직 원운동, 원뿔진자, 경사진 커브, 순수 구름, 회전충돌 문제 템플릿 버튼도 포함되어 있습니다.

## 오답노트 사용법

오답노트에는 다음 정보가 저장됩니다.

- 문제 원문
- 학생 풀이
- 문제 유형
- 적용식/비적용식
- 틀린 이유
- 난이도
- 즐겨찾기
- 복습 예정일
- 메모

오답노트 탭에서 검색, 문제 유형 필터, 오답/누락만 보기, 즐겨찾기만 보기, 오늘 복습만 보기를 사용할 수 있습니다.

## 백업과 내보내기

오답노트 탭에서 다음 파일을 다운로드할 수 있습니다.

- CSV 내보내기
- JSON 백업
- Markdown 내보내기

개인용 앱이라도 데이터가 중요하다면 주기적으로 JSON/CSV 백업을 다운로드하세요.

## 저장소 선택

기본은 SQLite입니다.

```bash
DYNAMICS_SQLITE_PATH=data/study_records.sqlite3
```

클라우드 배포에서 데이터가 사라지지 않도록 하려면 Supabase/Postgres 사용을 권장합니다.

```bash
DATABASE_URL=postgresql://...
```

자세한 내용은 `docs/DATABASE_BACKUP_RESTORE.md`를 참고하세요.

## GPT API 사용

GPT 기능은 선택 사항입니다. `OPENAI_API_KEY`가 없으면 규칙 기반 분석만 사용합니다.

```bash
OPENAI_API_KEY=sk-...
DYNAMICS_AI_MODEL=gpt-4o-mini
```

비용 절감을 위해 명확한 문제는 규칙 기반 분석을 우선 사용하고, 필요한 경우에만 GPT 보조 설명을 사용합니다. API key는 화면, 로그, 내보내기 결과에 노출되지 않습니다.

## 모바일 홈 화면 추가

- iPhone: Safari 접속 → 공유 버튼 → 홈 화면에 추가
- Android: Chrome 접속 → 메뉴 → 홈 화면에 추가

자세한 내용은 `docs/MOBILE_HOME_SCREEN.md`를 참고하세요.

## 배포

권장 구성은 Render/Railway + Supabase/Postgres입니다.

자세한 배포 절차는 다음 문서를 참고하세요.

- `docs/DEPLOYMENT.md`
- `docs/REDEPLOYMENT.md`
- `docs/DATABASE_BACKUP_RESTORE.md`
- `docs/OPERATING_COSTS.md`

## 테스트

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
```

## 현재 지원 범위

지원 수준은 앱 내부 **설정 / 지원 범위와 한계**에서도 확인할 수 있습니다.

| 유형 | 지원 수준 | 설명 |
|---|---|---|
| 직교좌표 위치벡터 | A | i/j, <x,y>, (x,y) 성분 위치벡터 미분 |
| 극좌표 운동 | B | r(t), θ(t), e_r/e_θ 단서가 명확한 경우 |
| 수평면 블록-도르래 | A | 마찰 있음/없음, 매달린 블록 연결 문제 |
| 경사면 물체 | B | 기본 FBD와 마찰 조건 안내 중심 |
| 순수 구름 | A | no slip/without slipping/skidding 계열 |
| 미끄럼 동반 회전 | A | contact slip/slipping/skidding 계열 |
| 수직 원운동 | A | 줄 장력과 트랙 수직항력, 최고/최저점 |
| 원뿔진자 | A | 끈+수평 원운동+수직선 각도 또는 cone 표현 |
| 경사진 커브 | A | 마찰 없음/최대속도/최소속도 대표식 |
| loop-the-loop | B | 접촉 유지 조건과 에너지식 안내 |
| 탄환/투사체-회전강체 충돌 | A | 고정축 기준 각운동량 보존 |
| 일반 강체 평면운동 | B | ΣF=ma_G, ΣM_G=I_Gα 골격 중심 |
| 3D 강체 운동/자이로스코프 | 미지원 | 오일러 방정식, 관성텐서, 세차/장동 등 |

A: 유형 판별 + 적용식 + 풀이 순서 안정  
B: 유형 판별 가능, 일부 조건 확인 필요  
C: 후보 제시 가능, 상세 풀이는 제한  
미지원: 현재 범위 밖

## 계산 지원 범위

- 유형 판별: 가능
- 적용식 제시: 가능
- 풀이 골격 제시: 가능
- 자동 수치 답 계산: 제한적
- 단위/유효숫자 포함 최종 답: 제한적

계산 도우미는 등가속도, 포물선 기본식, 높이-속도 에너지, 수직 원운동 최고점 최소속도, 1차원 충돌, 순수 구름 에너지 등 일부 대표 계산을 지원합니다. 복잡한 연립방정식과 모든 수치 정답 계산은 사용자가 직접 검산해야 합니다.

## 현재 한계

- 이미지/그림을 직접 인식하지 않습니다. 그림 속 치수와 조건을 텍스트로 입력해야 합니다.
- 모든 문제의 최종 수치 답을 자동 계산하는 완전 자동 풀이기가 아닙니다.
- 자이로스코프, 오일러 방정식, 3D 관성텐서, 회전좌표계, 3D 코리올리 문제는 미지원입니다.
- 여러 개념이 동시에 섞인 복합 문제는 대표 유형 후보와 풀이 골격 중심으로 안내합니다.
- Streamlit 기반 모바일 웹앱이므로 네이티브 앱/PWA가 아니며, 오프라인 사용·푸시 알림·앱스토어 설치는 지원하지 않습니다.

자세한 내용은 다음 문서를 참고하세요.

- `docs/LIMITATIONS.md`
- `docs/IMAGE_INPUT_LIMITATION.md`
- `docs/NUMERIC_SOLVER_LIMITATION.md`
- `docs/UNSUPPORTED_3D_DYNAMICS.md`
- `docs/SUPPORT_SCOPE_MATRIX.md`
- `docs/INPUT_GUIDE.md`
- `docs/STREAMLIT_MOBILE_LIMITATION.md`
- `docs/MOBILE_QA_CHECKLIST.md`

## 문제 발생 시 확인

1. 입력 문제가 너무 짧지 않은지 확인합니다.
2. 물체, 힘, 마찰 여부, 회전 여부, 지지 조건을 더 구체적으로 적습니다.
3. API key 없이도 규칙 기반 분석이 되는지 확인합니다.
4. 오답노트 저장이 안 되면 저장소 설정과 백업 파일을 확인합니다.
5. 클라우드 배포에서는 `APP_PASSWORD`, `OPENAI_API_KEY`, `DATABASE_URL`이 secrets로 설정되어 있는지 확인합니다.

## 입문자 안전 사용 안내

앱의 기본 화면 모드는 **입문자 모드**입니다. 입문자 모드에서는 문제 유형을 짧게 확인한 뒤 FBD, 핵심 원리, 첫 번째 식, 다음 식, 쓰면 안 되는 식, 직접 계산해볼 부분을 단계별로 열어보도록 구성되어 있습니다.

정보 부족 입력, 예를 들어 “그림과 같은 시스템에서 가속도를 구하라.”처럼 물체·마찰·연결·치수 조건이 빠진 문제는 **정보 부족**으로 표시하고 추측성 풀이를 중단합니다. 이 앱은 **자동 정답 생성기**가 아니라 문제 유형과 풀이 방향을 잡아주는 튜터형 도구입니다.

그림 정보를 텍스트로 바꿀 때는 물체 개수, 질량, 힘, 마찰 여부, 도르래/줄 조건, 운동 방향, 구하려는 값을 함께 적어 주세요. 배포용 ZIP에는 개인 데이터가 들어가지 않도록 `data/*.sqlite3`, `data/gpt_call_log.jsonl`, 캐시와 로그 파일을 제외합니다.


## 입문자 안전 사용 원칙

이 앱은 문제 키워드만 보고 공식을 찍는 도구가 아닙니다. 특히 입문자 모드에서는 다음 경우 구체식을 바로 제시하지 않고 추가 조건을 요구합니다.

- `블록이 경사면 위에 있다. 가속도를 구하라.`처럼 경사각, 마찰, 운동 방향이 빠진 경사면 문제
- `원운동하는 물체의 장력을 구하라.`처럼 수평/수직 원운동, 최고점/최저점, 줄/트랙 모델이 빠진 문제
- `A cylinder is rolling. Find acceleration.`처럼 rolling만 있고 no slip 조건이 없는 구름 문제
- `A car moves on a curve. Find maximum speed.`처럼 평평한 커브/경사진 커브, 마찰, 반지름 조건이 빠진 문제

이 경우 앱은 “정보 부족 · 추가 조건 필요”를 표시하고, 질문형 입력 마법사로 빠진 조건을 묻습니다. 명확한 조건이 들어오면 기존처럼 적용식, 비적용식, FBD, 단계별 풀이를 제공합니다.

자세한 기준은 `docs/BEGINNER_STRICT_CONDITION_GATE.md`를 참고하세요.


## 입문자용 커브 주행 안전 게이트

입문자 모드에서는 `curve`, `flat curve`, `banked curve`, `커브` 같은 키워드만으로 속도 공식을 확정하지 않습니다.

예를 들어 다음 입력은 정보 부족으로 처리됩니다.

```text
A car moves on a banked curve. Find maximum speed.
A car moves on a flat curve. Find maximum speed.
자동차가 경사진 커브를 돈다. 최대속도를 구하라.
```

앱은 대신 커브 반지름 `R`, 평평한/경사진 도로 여부, 마찰계수 `μ_s`, 경사각 `θ`, 최대/최소/설계속도 여부, 미끄러지기 직전 조건을 확인하도록 질문합니다.

다음처럼 조건이 충분하면 적용식을 제시합니다.

```text
A car moves on a flat curve of radius R with coefficient of static friction μ_s. Find the maximum speed before slipping.
A car travels on a frictionless banked curve of radius R and bank angle θ. Find the design speed.
A car travels on a banked curve of radius R and angle θ with coefficient of static friction μ_s. Find the maximum speed before slipping.
```

## Beginner Tutor v1.0 Safety Notes

This version is intentionally conservative for beginners. It is a dynamics learning coach, not an automatic answer generator. It now applies these additional safety rules:

- A block-pulley problem is not allowed to inherit conical-pendulum equations merely because it contains words like string, hanging, and horizontal.
- Conical pendulum equations require explicit conical wording or the physical structure of string + horizontal circular motion + vertical angle.
- If a student solution uses `f = μN` in a frictionless problem, the app flags it as a misconception.
- If pure rolling is not stated, `v_G = ωR` and `a_G = αR` are not treated as generally applicable.
- Wrong-note tags, difficulty level, unit conversion hints, and helper calculators are intended as study aids only; students should still complete the final algebra and unit check.


## v1.1 안전 패치: 오개념 탐지 범위

학생 풀이 오개념 탐지는 이제 단순 키워드보다 최종 문제 유형을 우선합니다. 예를 들어 `줄`, `매달린`, `장력`이라는 단어가 있어도 원뿔진자, 단진자, 단일 줄 평형 문제에서는 도르래 전용 경고를 표시하지 않습니다.

- 원뿔진자: 장력 성분식, 수평 원운동, `r = L sinθ` 관련 오개념만 우선 검사
- 블록-도르래: 두 물체 FBD, 가속도 관계, 매달린 물체 운동방정식 누락 검사
- 애매한 줄 문제: 확정 경고 대신 확인 질문 표시

자세한 결과는 `docs/BEGINNER_TUTOR_V11_QA_RESULT.md`를 참고하세요.

## v1.2 자연어 표현 처리 보강

학생이 교재 문장처럼 정확하게 입력하지 않아도 대표 단서를 더 잘 잡도록 동의어 사전을 분리했습니다.

지원하는 예시는 다음과 같습니다.

- 줄/실/끈/로프/cord/string/rope/cable → 장력 전달 부재 단서
- 정지/가만히 있음/움직이지 않음/평형/at rest/equilibrium → 평형 단서
- 작은 각도/작은 진폭/소진동/살짝 흔들림/small oscillation → 단진자 단서
- 수직선/연직선과 각도, 원을 그리며 돈다/돎, 수평 원운동 → 원뿔진자 단서

단, 이 단어 하나만으로 문제 유형을 확정하지 않습니다. 특히 실, 끈, 로프, 장력, 매달림은 단일 줄 평형, 단진자, 원뿔진자, 수직 원운동, 블록-도르래에서 모두 쓰일 수 있으므로 조합 조건으로 판단합니다.

도르래 전용 오개념 경고는 최종 유형이 블록-도르래 또는 도르래 연결 문제로 확정된 경우에만 표시됩니다. 단진자, 원뿔진자, 단일 줄 평형 문제에서는 표시되지 않습니다.
