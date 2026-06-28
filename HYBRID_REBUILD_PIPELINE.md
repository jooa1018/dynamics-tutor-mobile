# Hybrid Template Rebuild Pipeline

## 목적

기존 규칙 기반 엔진은 빠르고 비용이 들지 않지만, 자연어 표현이 애매하거나 여러 물리 상황의 단서가 섞이면 고위험 오분류가 발생할 수 있다. 이 버전은 GPT mini 계열 모델을 **항상 호출하지 않고**, 필요한 경우에만 보조 판별로 사용한다.

## 처리 흐름

```text
문제 입력
→ semantic_normalizer 정규화
→ 규칙 기반 템플릿 1차 선택
→ confidence / risk trigger 계산
→ 필요 시 GPT mini JSON 판별 호출
→ GPT primary_candidate 검증
→ GPT candidate → internal template_id 매핑
→ Reconciliation Logic으로 최종 template_id 결정
→ Template Rebuild Pipeline으로 적용식/비적용식/주의사항 재생성
→ forbidden formula guard 최종 적용
→ 출력
```

## GPT candidate → internal template_id 매핑

| GPT candidate | internal template_id | 설명 |
|---|---|---|
| conical_pendulum | conical_pendulum | 원뿔진자 |
| sliding_rotation | sliding_rotation | 미끄럼 동반 회전/구름 |
| pure_rolling | pure_rolling | 순수 구름 |
| vertical_circle_string_bottom | vertical_circle_string_bottom | 줄/끈 수직 원운동 최저점 장력 |
| vertical_circle_string_top | vertical_circle_string_top | 줄/끈 수직 원운동 최고점 |
| vertical_circle_track_bottom | vertical_circle_track_bottom | 트랙 수직 원운동 최저점 수직항력 |
| frictionless_pulley_block | frictionless_pulley_block | 마찰 없는 수평면 블록 + 매달린 물체 |
| banked_curve_with_friction_max_speed | banked_curve_with_friction_max_speed | 마찰 있는 경사진 커브 최대속도 |
| banked_curve_with_friction_min_speed | banked_curve_with_friction_min_speed | 마찰 있는 경사진 커브 최소속도 |
| cartesian_position_vector | cartesian_position_vector | 직교좌표 위치벡터 미분 |
| polar_motion | polar_motion | 극좌표 운동학 |
| bullet_rotating_body_collision | bullet_rotating_body_collision | 탄환/투사체-회전강체 충돌 |
| general_planar_rigid_body | general_planar_rigid_body | 강체 일반 평면운동 |

## Reconciliation Logic

GPT 후보는 무조건 적용하지 않는다. 다음 조건을 만족할 때 실제 템플릿 재선택에 반영한다.

1. GPT confidence가 충분히 높다.
2. GPT 후보가 내부 템플릿 매핑표에 존재한다.
3. 후보 템플릿의 필수 물리 단서가 문제 문장 또는 GPT detected_features와 맞는다.
4. 기존 규칙 결과가 일반 템플릿이거나, 고위험 오분류 단서가 있다.
5. forbidden formula guard와 충돌하지 않는다.

반대로 GPT confidence가 낮거나 필수 조건이 부족하면 하나의 템플릿으로 확정하지 않고 `ambiguity_notes`에 후보와 확인 필요 조건을 표시한다.

## 고위험 자동 호출 트리거

confidence가 높아 보이더라도 다음 조합은 GPT 보조 판별 후보가 된다.

- projectile/bullet + embedded/sticks + wheel/disk/rod + fixed axis/rotate together
- string/rope/cord + bottom/lowest + tension
- frictionless/smooth/negligible friction + friction/mu 단서 충돌
- rolling + slipping/skids/contact point slips
- cartesian i/j vector + polar-like r(t) 표현 충돌
- conical candidate: string + hanging object + horizontal circle/vertical angle
- mixed Korean/English input

## JSON Schema 역할

GPT는 최종 식을 생성하지 않는다. 다음 구조만 반환한다.

```json
{
  "primary_candidate": "sliding_rotation",
  "secondary_candidates": ["general_planar_rigid_body"],
  "confidence": 0.86,
  "detected_features": {
    "has_rolling": true,
    "has_slipping": true,
    "friction_mode": "kinetic_or_slipping"
  },
  "evidence_phrases": ["rolls but skids"],
  "missing_information": ["mu_k", "theta", "I_G"],
  "must_use_tags": ["sum_forces", "sum_moments_about_center"],
  "must_not_use_tags": ["pure_rolling_constraint"],
  "warnings": ["Do not apply pure rolling constraints."]
}
```

최종 적용식은 내부 템플릿과 guard가 만든다.

## forbidden formula guard

최종 출력 직전에 한 번 더 적용한다.

- 미끄럼 단서 있음 → `v_G = ωR`, `a_G = αR` 적용식 제거
- 마찰 없음 → `f = μN` 적용식 제거, `f = 0` 추가
- 줄/끈 수직 원운동 → `N` 계열 식 제거, `T` 사용
- 트랙/레일 수직 원운동 → `T` 계열 식 제거, `N` 사용
- 직교좌표 위치벡터 → 극좌표 가속도식 제거
- 탄환-회전강체 충돌 → 단순 1D 선운동량 보존 우선식 제거
- 마찰 있는 경사진 커브 → 평평한 커브식과 마찰 없는 설계속도 단독 적용 제거

## API key와 모델

- `OPENAI_API_KEY` 환경변수에서만 읽는다.
- 앱 UI의 모델명은 하이브리드 판별 로직에 전달된다.
- API key가 없거나 오류가 발생하면 규칙 기반 엔진으로 fallback한다.

## 캐싱과 로그

- 동일 정규화 입력은 `DYNAMICS_AI_CACHE` 경로에 캐시된다.
- 호출 로그는 `DYNAMICS_AI_LOG` 경로에 JSONL로 저장된다.
- 로그에는 input_hash, rule_candidate, rule_confidence, trigger_reason, ai_candidate, ai_confidence, final_template, cache_hit, fallback_used, estimated chars가 포함된다.

## Live smoke test

`live_smoke_test.py`를 실행하면 실제 API key 환경에서 다음을 확인한다.

```bash
OPENAI_API_KEY=... python live_smoke_test.py
```

API key가 없는 환경에서는 실행하지 않고 mock 테스트만 수행한다.
