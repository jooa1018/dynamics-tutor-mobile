# 하이브리드 최종 고도화 변경 내역

## 수정 요약

최신 버전에서는 기존 규칙 기반 전문가 템플릿 엔진 위에 `GPT mini 기반 자동 보조 판별 구조`를 추가했습니다.

핵심 변화:

1. `dynamics_core/ai_assist.py` 추가
2. confidence score 계산 추가
3. GPT 자동 호출 조건 추가
4. JSON Schema 기반 GPT 응답 구조 정의
5. GPT mock 테스트 추가
6. API key 없음/오류/JSON 오류 fallback 처리 추가
7. 캐싱 및 호출 로그 추가
8. forbidden formula guard 강화
9. Streamlit UI에 AI 보조 판별 상태/호출 이유 표시 추가
10. README / TEST_MATRIX / HYBRID_AI_INTEGRATION 문서 업데이트

## 변경된 분류 로직

기존:

```text
문제 입력 → 규칙 기반 템플릿 선택 → 적용식 출력
```

변경 후:

```text
문제 입력
→ 규칙 기반 템플릿 선택
→ confidence score 계산
→ 위험 플래그 검사
→ 필요 시 GPT mini 보조 판별
→ GPT JSON 결과 파싱
→ 규칙 엔진 검증
→ forbidden formula guard 적용
→ 적용식/비적용식/주의사항 분리 출력
```

## GPT 자동 호출 기준

- confidence < 0.70
- 0.70 ≤ confidence < 0.90 이면서 위험 플래그 존재
- 순수 구름/미끄럼 단서 충돌
- 줄/트랙 단서 충돌
- 직교좌표/극좌표 단서 충돌
- 마찰 있음/없음 단서 충돌
- 한국어/영어 혼합 입력 중 위험 단서 존재
- 입력이 짧고 조건 부족
- 회전축 충돌/탄환/고정축 등 복합 단서 존재

## 추가 테스트 목록

새 파일:

- `tests/test_ai_hybrid.py`

검증 내용:

- 확실한 문제에서 GPT 호출하지 않음
- 애매한 도르래 문제에서 GPT 호출 후보가 됨
- API key가 없을 때 fallback
- mock GPT 응답이 sliding_rotation일 때 금지 태그 반영
- 동일 입력 반복 시 캐시 사용
- API 오류 시 fallback + forbidden formula guard 유지
- GPT/규칙 guard가 순수 구름식을 적용식에서 제거
- build_diagnosis 결과에 confidence/AI 상태가 기록됨

## 전체 테스트 실행 결과

```text
python regression_tests.py
OK: all 2nd-rework regression tests passed

python expert_regression_tests.py
OK: expert regression tests passed — 100 representative cases, 50 counterexamples, and equation skeleton checks

python fourth_regression_tests.py
OK: fourth regression tests passed — 20 complex cases, ambiguity handling, and area-aware forbidden-equation checks

python final_quality_tests.py
OK: final quality tests passed — 7 final condition-branch corrections with area-aware checks

python expression_variation_tests.py
OK: expression variation tests passed — robust natural-language variants for final expert templates

pytest -q
223 passed
```

## 비용 절감/캐싱

- cache: `data/ai_assist_cache.json`
- log: `data/gpt_call_log.jsonl`
- API key: `OPENAI_API_KEY`
- model: `DYNAMICS_AI_MODEL`, 기본값 `gpt-4o-mini`

## 안전 원칙

GPT는 최종 수식을 직접 결정하지 않습니다.
GPT는 후보 유형과 태그만 제안하고, 최종 적용식은 기존 규칙 엔진과 forbidden formula guard가 결정합니다.
