# GPT mini 기반 자동 보조 판별 구조

이 문서는 최종 수락 전 요청된 **규칙 기반 엔진 + 선택적 GPT mini 보조 판별** 구조를 설명합니다.

## 1. 설계 목표

이 앱은 GPT가 물리식을 마음대로 생성하는 챗봇이 아닙니다.

기본 흐름은 다음과 같습니다.

```text
학생 문제 입력
→ semantic_normalizer / parser 규칙 분석
→ 전문가 템플릿 엔진 적용
→ confidence score 계산
→ 확실하면 GPT 호출 없음
→ 애매하거나 금지식 위험이 있으면 GPT mini 자동 호출
→ GPT는 JSON으로 후보 유형/단서/금지 태그만 반환
→ 규칙 엔진이 GPT 결과를 검증
→ forbidden formula guard 적용
→ 적용식 / 비적용식 / 주의사항 출력
```

## 2. GPT 호출 조건

`dynamics_core/ai_assist.py`의 `decide_ai_assist()`가 자동 호출 여부를 판단합니다.

대표 조건:

- 규칙 엔진 confidence가 낮음
- 정보 부족 또는 모호성 템플릿 선택
- 순수 구름과 미끄럼 단서가 함께 있음
- 줄/끈/로프 문제와 트랙/레일 문제가 충돌
- 직교좌표 위치벡터와 극좌표 단서가 충돌
- 마찰 있음과 마찰 없음 단서가 충돌
- 한국어/영어 혼합 입력
- 입력이 너무 짧아 조건이 부족함
- 회전축 충돌/탄환/고정축처럼 여러 유형에 걸칠 위험이 있음
- 금지식이 적용식으로 섞일 위험이 있음

호출하지 않는 경우:

- 전용 템플릿이 높은 confidence로 확정됨
- 적용식/비적용식 충돌이 없음
- 위치벡터 미분처럼 구조가 명확함
- 기존 규칙과 테스트로 충분히 검증된 대표 구조

## 3. confidence score 기준

`estimate_rule_confidence()`는 0~1 범위 점수를 계산합니다.

| 점수 | 처리 |
|---:|---|
| 0.90 이상 | 규칙 기반 판별로 충분히 확실, GPT 호출 없음 |
| 0.70 이상 0.90 미만 | 위험 플래그가 있으면 GPT 호출 가능 |
| 0.70 미만 | GPT mini 보조 판별 권장 |
| 0.50 미만 | 하나의 유형으로 확정하지 않고 후보/확인 조건 출력 |

일부 강제 위험 조건은 점수가 높아도 GPT 호출 후보가 됩니다.
예: `구름 + 미끄럼`, `줄 + 트랙`, `직교좌표 + 극좌표 충돌`.

## 4. JSON Schema 구조

GPT 응답은 자유문장이 아니라 다음 구조를 따릅니다.

```json
{
  "primary_candidate": "sliding_rotation",
  "secondary_candidates": ["general_planar_rigid_body"],
  "confidence": 0.86,
  "detected_features": {
    "has_rolling": true,
    "has_slipping": true,
    "has_string": false,
    "has_track": false,
    "has_fixed_axis": false,
    "has_collision": false,
    "has_cartesian_vector": false,
    "has_polar_vector": false,
    "friction_mode": "kinetic_or_slipping"
  },
  "evidence_phrases": ["굴러 내려가지만", "미끄럼이 발생한다"],
  "missing_information": ["운동마찰계수 μ_k", "경사각 θ"],
  "must_use_tags": ["sum_forces", "sum_moments_about_center", "kinetic_friction"],
  "must_not_use_tags": ["pure_rolling_constraint"],
  "warnings": ["미끄럼이 있으므로 순수 구름 조건을 적용하면 안 됩니다."]
}
```

실제 schema는 `dynamics_core/ai_assist.py`의 `GPT_ASSIST_JSON_SCHEMA`에 있습니다.

## 5. GPT가 해도 되는 일과 하면 안 되는 일

GPT가 하는 일:

- 자연어 표현 해석 보조
- 후보 유형 태그 제안
- 단서와 근거 표현 추출
- 부족한 조건 제시
- 금지식 태그 제안
- 경고 문장 제안

GPT가 하지 않는 일:

- 최종 물리식을 단독 생성
- 미검증 식을 적용식에 직접 추가
- 문제에 없는 조건을 가정
- 수치 답을 임의 계산
- forbidden formula guard 우회

## 6. forbidden formula guard

`apply_forbidden_formula_guard()`는 GPT 결과보다 우선합니다.

대표 방어 규칙:

- 미끄럼 단서가 있으면 `v_G = ωR`, `a_G = αR`을 적용식에서 제거
- frictionless/smooth/ignore friction이면 `f = 0` 우선, `f = μN` 적용식 제거
- 줄/끈/로프 수직 원운동에서는 `T` 사용, `N` 우선식 제거
- i, j 위치벡터에서는 극좌표 가속도식 적용 금지
- 탄환-회전강체 충돌에서는 단순 선운동량 보존 우선식 차단
- 경사진 커브에서는 평평한 커브 식 `N = mg`, `μ_s ≥ v²/(gR)` 적용 금지

## 7. 비용 절감 구조

- 확실한 문제는 GPT 호출 없음
- 기본 모델은 `gpt-4o-mini` 또는 환경변수 `DYNAMICS_AI_MODEL`
- prompt에는 문제 문장과 규칙 엔진 1차 분석 결과만 포함
- JSON 출력과 `max_output_tokens`로 출력 길이 제한
- temperature는 낮게 설정
- 동일 정규화 입력은 `data/ai_assist_cache.json` 캐시 사용
- 호출 기록은 `data/gpt_call_log.jsonl`에 저장
- API key는 코드에 저장하지 않고 `OPENAI_API_KEY` 환경변수 사용
- API key 없음, 네트워크 오류, JSON 오류 시 규칙 기반 결과로 fallback

## 8. 환경변수 설정

```bash
export OPENAI_API_KEY="your_api_key_here"
export DYNAMICS_AI_MODEL="gpt-4o-mini"
```

API key가 없어도 앱은 규칙 기반 엔진으로 정상 작동합니다.

## 9. 테스트

기존 테스트:

```bash
python regression_tests.py
python expert_regression_tests.py
python fourth_regression_tests.py
python final_quality_tests.py
python expression_variation_tests.py
```

pytest 자동 발견 테스트:

```bash
pytest -q
```

GPT mock / fallback / cache 테스트:

```bash
pytest -q tests/test_ai_hybrid.py
```

테스트는 실제 API를 호출하지 않습니다. mock client를 주입해 비용 없이 검사합니다.

## 10. 현재 한계

- GPT 보조 판별은 자연어 해석 보조일 뿐, 완전 자동 풀이기가 아닙니다.
- 그림 기반 기하 해석은 여전히 제한적입니다.
- 복잡한 다물체/3차원 강체 문제는 후보와 확인 조건을 제시하는 수준일 수 있습니다.
- 최종 수치 연립 계산은 모든 유형에서 자동화되어 있지 않습니다.
