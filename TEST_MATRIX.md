# 테스트 매트릭스 · 4차 재작업판

## 실행 명령

```bash
python regression_tests.py
python expert_regression_tests.py
python fourth_regression_tests.py
```

## 테스트 구성

| 파일 | 목적 | 개수/범위 |
|---|---|---|
| `regression_tests.py` | 기존 오진 방지, 계산기 검증, 2차 구조화 검증 | 핵심 회귀 테스트 |
| `expert_regression_tests.py` | 3차 전문가 템플릿 검증 | 대표 문제 100개, 반례 50개, 핵심 방정식 테스트 |
| `fourth_regression_tests.py` | 4차 복합 템플릿 및 배제 로직 검증 | 대표 복합 문제 20개 + 모호성 처리 1개 |

## 4차 테스트 방식

4차 테스트는 단순 전체 문자열 검사가 아니라 출력 영역별로 확인합니다.

- `applicable_equations`: 반드시 사용할 식이 들어가야 함
- `not_applicable_equations`: 현재 문제에서 쓰면 안 되는 식 또는 적용 보류 식이 들어가야 함
- `cautions`: 조건/주의사항이 들어가야 함
- `suppressed_templates`: 배제된 일반 템플릿이 기록되어야 함
- `ambiguity_notes`: 정보 부족 시 추가 조건 안내가 들어가야 함

핵심 기준:

- 금지식이 `applicable_equations`에 들어가면 실패
- 금지식이 `not_applicable_equations`나 `cautions`에 “적용 불가” 설명으로 들어가는 것은 허용
- 모호한 문제는 억지로 일반 템플릿을 적용하면 실패

## 대표 복합 문제 20개

1. 수평면 블록 + 매달린 물체 + 마찰
2. 경사면 블록 + 매달린 물체
3. 질량 있는 도르래
4. 움직도르래
5. 평평한 커브
6. 경사진 커브
7. 원뿔진자
8. 수직 원운동
9. 미끄럼 없는 순수 구름
10. 미끄럼을 동반한 구름
11. 위치 함수 x(t), y(t) 운동학
12. 위치 의존 힘 F(x)
13. 시간 의존 힘 F(t)와 충격량
14. 막대 벽-바닥 순간중심
15. 슬롯/핀 상대속도
16. 탄환-막대 충돌
17. 각운동량 보존
18. 충돌 + 반발계수
19. 강체 고정축 회전
20. 강체 일반 평면운동

## 예시 검수 기준

### 수평면 블록 + 매달린 물체

입력:

```text
질량 10 kg인 블록 A가 수평면 위에 있고, 질량 5 kg인 물체 B가 도르래에 매달려 있다. 수평면의 마찰계수는 0.2이다. 가속도와 장력을 구하라.
```

`applicable_equations`에 포함되어야 함:

- `T - f = m_Aa`
- `N_A = m_Ag`
- `f = μN_A`
- `m_Bg - T = m_Ba`

`applicable_equations`에 들어가면 안 됨:

- `m_Ag - T = m_Aa`

### 경사진 커브

`applicable_equations`에 포함되어야 함:

- `N cosθ = mg`
- `N sinθ = mv²/R`
- `tanθ = v²/(gR)`

`applicable_equations`에 들어가면 안 됨:

- `N = mg`
- `μ_s ≥ v²/(gR)`

### 미끄럼 구름

`applicable_equations`에 포함되어야 함:

- `ΣF = ma_G`
- `ΣM_G = I_Gα`
- `f_k = μ_kN`

`applicable_equations`에 들어가면 안 됨:

- `v_G = ωR`
- `a_G = αR`

### 위치 함수 운동학

`applicable_equations`에 포함되어야 함:

- `v(t) = dr/dt`
- `a(t) = d²r/dt²`
- `dx/dt`
- `d²x/dt²`

`applicable_equations`에 들어가면 안 됨:

- `v = v0 + at`
- `s = v0t + 1/2at²`

## 기존 테스트 유지

기존 100개 대표 유형 테스트와 50개 반례 테스트도 유지됩니다. 4차 개선은 기존 기능을 삭제하는 것이 아니라, 복합 문제에서 잘못된 일반 템플릿이 섞이지 않도록 상위 구조를 추가한 것입니다.

---

## 최종 품질 보정 테스트 추가

파일: `final_quality_tests.py`

추가 검수 항목:

| 항목 | 입력 유형 | 적용식 검증 | 비적용식/주의사항 검증 |
|---|---|---|---|
| 마찰 없는 수평면 블록 + 매달린 물체 | 마찰 없는 수평면, 매달린 물체, 도르래 | `f = 0`, `T = m_Aa`, `m_Bg - T = m_Ba` | `f = μN_A`, `T - f = m_Aa`는 적용식 금지 |
| 매끈한 경사면 블록 + 매달린 물체 | 매끈한 경사면, 도르래 연결 | `f = 0`, `N = mg cosθ`, `T - mg sinθ = ma` | `f = μN = μmg cosθ` 적용식 금지 |
| 마찰계수 언급 + 마찰 무시 | μ 언급 후 마찰 무시 | `f = 0` 우선 | μ 기반 마찰식 적용식 금지 |
| 경사진 커브 최대속도 | 마찰 있는 banked curve 최대속도 | `N cosθ - f sinθ = mg`, `N sinθ + f cosθ = mv²/R` | 평평한 커브 식, 마찰 없는 설계식 단독 적용 금지 |
| 경사진 커브 최소속도 | 마찰 있는 banked curve 최소속도 | `N cosθ + f sinθ = mg`, `N sinθ - f cosθ = mv²/R` | 평평한 커브 식, 마찰 없는 설계식 단독 적용 금지 |
| 원뿔진자 표현 변형 | 줄, 매단 질점, 수평 원운동, 연직선 각도 | `T cosθ = mg`, `T sinθ = mω²r`, `r = L sinθ` | 강체 회전식 적용식 금지 |
| 미끄럼 동반 회전 | 미끄러져 내려가면서 회전 | `ΣF = ma_G`, `ΣM_G = I_Gα`, `f_k = μ_kN` | `v_G = ωR`, `a_G = αR` 적용식 금지 |
| 위치벡터 r(t) | `r(t)=...i+...j` | `v(t)=dr/dt`, `a(t)=d²r/dt²` | 극좌표 `e_r`, `e_θ` 식 적용식 금지 |
| 탄환-원판 충돌 | 탄환이 원판 가장자리에 박힘 | `H_O(before)=H_O(after)`, `m_bvr=I_totalω` | 선운동량 보존 우선 적용 금지 |
| 수직 원운동 최저점 | 줄에 매단 물체 최저점 장력 | `T - mg = mv²/R`, `T = mg + mv²/R` | 최고점 최소속도 조건 우선 적용 금지 |
| 수직 원운동 최고점 | 최고점 최소속도 | `mg + T = mv²/R`, `T = 0`, `v_min = √(gR)` | 최저점 장력식 적용식 금지 |
| 수직 원운동 임의각도 | 임의 각도 장력 | `T - mg cosθ = mv²/R`, `ΣF_t = ma_t` | 최고점 전용 최소속도 조건 우선 적용 금지 |

검증 기준:

- `applicable_equations`에는 금지식이 들어가면 실패
- `not_applicable_equations`에는 금지식이 “적용 불가/적용 보류” 설명과 함께 들어갈 수 있음
- `cautions`, `suppressed_templates`, `ambiguity_notes`는 별도 영역으로 검증

## 표현 변형 견고성 테스트

추가 파일: `expression_variation_tests.py`

이 테스트는 기존 예시 문장과 조금 다른 실제 학생식 표현을 검증합니다.

| 영역 | 예시 표현 | 기대 동작 |
|---|---|---|
| 경사진 커브 | 최대 속력, 허용 가능한 최대 속력, 뱅크 커브 | 마찰 있는 banked curve 최대속도 템플릿 |
| 경사진 커브 | 최소 속력, 아래로 미끄러지지 않는 최소 속력 | 마찰 있는 banked curve 최소속도 템플릿 |
| 원뿔진자 | 수평면에서 원을 그리며 회전, 줄이 수직과 θ | 원뿔진자 템플릿 |
| 원뿔진자 후보 | 줄에 매단 물체가 원을 그리나 각도 기준 부족 | ambiguity_notes에 추가 조건 안내 |
| 미끄럼 회전 | 미끄러지며 내려가고 회전도 한다, rolling with slip | 미끄럼 동반 회전 템플릿, 순수 구름 조건 비적용 |
| 수직 원운동 | 가장 낮은 위치, bottom, rope/string | 최저점 장력식 T - mg = mv²/R |
| 마찰 없음 | smooth horizontal table | f = 0, T = m_Aa |
| 위치벡터 | r(t)=3t i + 2t² j | 직교좌표 위치벡터 미분 |
| 탄환 충돌 | 총알이 회전판 가장자리에 박힘 | 각운동량 보존 우선 |

영역별 검증 기준은 기존과 같습니다.

- `applicable_equations`: 실제 적용식만 포함
- `not_applicable_equations`: 현재 조건에서 쓰면 안 되는 식
- `cautions`: 주의사항
- `suppressed_templates`: 배제된 일반 템플릿
- `ambiguity_notes`: 정보 부족 안내

---

## 6차 검토 후 자연어 견고성 테스트 매트릭스

새 테스트 파일: `tests/test_semantic_robustness.py`

| 핵심 유형 | 테스트 수 | 주요 검증 내용 |
|---|---:|---|
| 경사진 커브 | 30 | 최대속도/최대속력, 최소속도/최소속력, banked curve, friction 있음/없음 분기 |
| 원뿔진자 | 30 | 원뿔진자 직접 표현, 구조 기반 감지, 조건 부족 시 후보/모호성 안내 |
| 미끄럼 동반 회전/구름 | 30 | slip/slipping/미끄럼 발생/not pure rolling이 있으면 순수 구름식 배제 |
| 수직 원운동 | 30 | 줄/끈/로프 문제의 T와 트랙/레일 문제의 N 분리, 최고점/최저점 분기 |
| 수평면 블록 + 매달린 물체 | 30 | smooth/frictionless/ignore friction, 마찰 있음, 마찰 조건 불명 분기 |
| 위치벡터/극좌표 | 30 | i,j/\hat{i},\hat{j} 위치벡터와 r,θ/e_r,e_θ 극좌표 분기 |
| 탄환-회전강체 충돌 | 30 | 총알/탄환 + 원판/회전판/막대/바퀴 + 고정축/박힘 표현 확장 |

검증 방식:

- `applicable_equations`에 반드시 들어가야 할 식 검사
- `applicable_equations`에 들어가면 안 되는 식 검사
- `not_applicable_equations`에 비적용식이 분리되어 있는지 검사
- `cautions`, `ambiguity_notes`, `suppressed_templates` 영역별 검사

전체 pytest 결과:

```text
223 passed in 1.69s
```

커버리지 요약:

```text
TOTAL 2438 statements, 95% coverage
```

---

## 하이브리드 GPT mini 보조 판별 테스트 매트릭스

새 테스트 파일: `tests/test_ai_hybrid.py`

| 테스트 | 목적 | 기대 결과 |
|---|---|---|
| clear_rule_case | 명확한 규칙 기반 문제에서 GPT 호출 방지 | `should_call=False`, confidence ≥ 0.90 |
| ambiguous_short_pulley | 짧고 배치 정보가 부족한 도르래 문제 | GPT 호출 후보, confidence < 0.70 |
| no_api_key_fallback | API key 없음 | 앱 중단 없이 규칙 기반 결과 사용 |
| mock_gpt_result | mock GPT JSON 응답 처리 | 후보/금지 태그 반영, 호출 로그 저장 |
| cache_hit | 동일 입력 반복 | API 재호출 없이 cache 사용 |
| gpt_error_fallback | API 오류 | 규칙 기반 fallback + forbidden guard 유지 |
| forbidden_guard | GPT보다 규칙 guard 우선 | 순수 구름식이 적용식에서 제거 |
| build_diagnosis_ai_status | 진단 결과에 confidence/AI 상태 기록 | blueprint에 디버그 필드 기록 |

검증되는 안전 규칙:

- 미끄럼 단서가 있으면 `v_G = ωR`, `a_G = αR` 적용식 금지
- 마찰 없음 단서가 있으면 `f = 0` 우선
- 회전축 충돌에서는 각운동량 보존 우선
- 위치벡터 `i,j`는 직교좌표 미분 우선
- GPT 응답은 최종 식이 아니라 후보/태그로만 반영
- API 실패 시 기존 규칙 엔진으로 fallback

현재 pytest 결과:

```text
223 passed
```

---

## Hybrid Template Rebuild 추가 테스트

추가 테스트 파일:

- `tests/test_template_rebuild_pipeline.py`
- `tests/test_template_rebuild_extra.py`
- `tests/test_final_user_failure_cases.py`

검증 항목:

1. GPT 후보가 실제 `final_template_id` 재선택에 반영되는지
2. `conical_pendulum`, `sliding_rotation`, `vertical_circle_string_bottom`, `cartesian_position_vector`, `bullet_rotating_body_collision` 재생성 검증
3. GPT confidence가 낮을 때 무리하게 재선택하지 않는지
4. 자동 호출 고위험 단서: projectile/bullet fixed-axis collision, bottom/tension, rolling+slip, cartesian vector, conical candidate
5. forbidden formula guard가 재생성 이후 최종 적용식에서 금지식을 제거하는지
6. 사용자 검토 실패 사례:
   - `뱅크 커브에서 limiting speed... friction이 있다`
   - `마찰 있는 banked road에서 upper limit of speed...`
   - `실 끝의 질점이 테이블과 평행한 원궤도...`
   - `cylinder rotates but the contact point slips`
   - `wheel rolls but skids`
   - `줄에 매단 공이 수직 원운동... 하단에서 장력`
   - `Block A is on a table with negligible friction...`
   - `r⃗(t)=3t i + 2t^2 j...`
   - `projectile embeds in a wheel... fixed axle`

현재 pytest 결과: `245 passed`.
커버리지 결과: `TOTAL 2816 statements, 95% coverage`.

---

## 최종 수락 전 버그 수정 테스트 매트릭스

새 테스트 파일: `tests/test_final_acceptance_bugfixes.py`

| 항목 | 입력 예시 | 기대 결과 |
|---|---|---|
| 순수 구름 부정 처리 | `cylinder rolls without slipping down incline.` | `pure_rolling`, `v_G = ωR`, `a_G = αR`; 미끄럼 템플릿 금지 |
| 순수 구름 영어 | `wheel rolls without slipping.` | 순수 구름 적용식 출력 |
| 미끄럼 동반 회전 | `wheel rolls but skids.` | 미끄럼 동반 회전, 순수 구름식 비적용식 이동 |
| 최저점 장력 짧은 표현 | `바닥점의 장력은?` | `T - mg = mv²/R`, `T = mg + mv²/R`; N 단독식 금지 |
| lowest/tension 혼합 | `lowest에서 tension?` | 장력 T 우선 |
| 수직 원운동 lowest | `줄에 매단 공이 수직 원운동을 한다. lowest에서 tension...` | 최저점 장력 템플릿 |
| 투사체-피벗 막대 충돌 | `projectile hits and remains in a rod pivoted at one end...` | 고정축 기준 각운동량 보존 |
| 원뿔진자 영어 | `string makes 30 degrees with vertical while bob revolves...` | 원뿔진자 템플릿 |
| negligible friction | `block on table, friction is negligible, tied to hanging mass.` | `f = 0`, 마찰 없는 수평면-매달린 블록 후보 |
| polished table | `polished horizontal table connected over a pulley...` | 마찰 없음 후보/적용, 마찰 있음 확정 금지 |

현재 pytest 결과: `255 passed`.
커버리지 결과: `TOTAL 2911 statements, 95% coverage`.

Live smoke test 파일:

- 실행 파일: `live_smoke_test.py`
- 내부 구현: `tools/live_smoke_runner.py`
- API key 없음: fallback check를 통과하고 `LIVE_SMOKE_TEST_RESULT.json` 생성
- API key 있음: GPT 호출, JSON 응답, template rebuild, guard, cache/log를 점검


## 최종 자연어 견고성 추가 테스트

파일: `tests/test_final_natural_language_robustness.py`

범위:

1. `without slip`, `no slip occurs`, `slipping does not occur` → 순수 구름
2. `with slip`, `contact point slips`, `미끄럼을 가지고 구른다`, `slip하며 굴러간다` → 미끄럼 동반 회전
3. hinged/pivoted bar + projectile sticks/remains → 탄환/투사체-회전강체 충돌
4. `r vector`, `<x,y>`, `(x,y)` → 직교좌표 위치벡터
5. string/cord/bob + circle + vertical angle → 원뿔진자
6. vertical loop + cord/tension/bottom → 최저점 장력식
7. rail + tension → 힘 기호 충돌 모호성 안내
8. inclined/banked curve + max/min speed variants → 경사진 커브 한계속도
9. friction-free/negligible/neglected friction + table/hanging mass → f=0 우선
10. loop-the-loop/contact 유지 → 최고점 접촉 유지 조건

검증 항목:

- 적용식이 비어 있지 않은지
- 잘못된 식이 applicable_equations에 들어가지 않는지
- 비적용식/주의사항에 금지식이 분리되는지
- T/N 힘 기호 충돌을 모호성으로 처리하는지
- 평평한 커브식과 경사진 커브식이 섞이지 않는지

## Final residual NL robustness tests

Added `tests/test_final_residual_nl_bugs.py` with 11 acceptance cases:

1. `Cylinder rolls without any slipping down the ramp.` → pure rolling, includes `v_G = ωR`, `a_G = αR`.
2. `The cylinder is rolling while slipping on the plane.` → sliding rotation, pure rolling constraints excluded from applicable equations.
3. `The cylinder rolls and slips down an incline.` → sliding rotation.
4. `원통이 미끄러지지 않고 회전하며 내려간다.` → pure rolling.
5. `원통이 접촉점에서 미끄러지지 않는다.` → pure rolling.
6. `car on a sloped curve with friction, find highest speed before sliding up the bank` → banked curve with friction, max speed.
7. `마찰계수가 있는 경사 도로 커브에서 최고 속도` → banked curve with friction, max speed.
8. `마찰계수가 있는 경사 도로 커브에서 최저 속도` → banked curve with friction, min speed.
9. `inclined road curve maximum allowable velocity` → banked curve max-speed candidate/skeleton.
10. `끈에 달린 물체가 원뿔 운동을 한다.` → conical pendulum.
11. `원형 레일의 최하점에서 수직항력` → vertical circular track bottom normal-force skeleton.

Each case checks non-empty applicable equations, required equations, forbidden applicable equations, and final-output type evidence.

---

## 도메인 사양 기반 최종 자연어 회귀 테스트

추가 파일: `tests/test_domain_ontology_regression.py`

이 테스트는 `docs/PHYSICS_ONTOLOGY.md`, `docs/DYNAMICS_GLOSSARY_KO_EN.md`, `docs/DECISION_TREE.md`, `docs/FORBIDDEN_FORMULA_TABLE.md`의 기준을 코드가 따르는지 확인합니다.

검증 항목:

- expected problem type / template family
- applicable_equations 비어 있지 않음
- forbidden formula가 적용식 영역에 없음
- `forbidden_formula_guard_applied = True`
- `consistency_check_passed = True`
- 순수 구름/미끄럼 동반 회전 표현군 분리
- banked/slanted curve 최대/최소속도 표현군 분리
- 원뿔진자 구조 표현군 분리
- 직교좌표 위치벡터 i-hat/j-hat, `(x,y)` 표현 분리
- 회전충돌 표현군 유지

대표 추가 케이스:

```text
A disk rolls without skidding down the incline.
The wheel is not slipping as it rolls.
The cylinder slips while rolling down the plane.
The cylinder rolls, but there is slip at the contact point.
The wheel is rolling but not slipping.
vehicle on a slanted curve with static friction, fastest speed before sliding outward
마찰 있는 뱅크 도로에서 최고 속력
마찰 있는 뱅크 도로에서 최저 속력
경사진 커브에서 가장 큰 속력은? μ_s가 주어짐
경사진 도로 커브에서 가장 작은 속력은? 마찰계수 있음
자동차가 경사진 커브에서 바깥쪽으로 미끄러지기 직전의 속력
자동차가 경사진 커브에서 안쪽으로 미끄러지기 직전의 속력
bob tied to a cord moves like a cone
끈과 수직선이 각도를 이루며 물체가 수평 원운동한다
r vector equals 3t i-hat plus 2t^2 j-hat, compute acceleration
particle has position (3t, 2t^2), find velocity
```

전체 결과:

```text
pytest -q: 311 passed
coverage: TOTAL 3184 statements, 95%
```

## 최종 문서-코드 일치 회귀 테스트

파일: `tests/test_docs_code_alignment_final.py`

추가 검증 항목:

1. `A wheel rolls without any skidding down a ramp.` → 순수 구름, `v_G = ωR`, `a_G = αR`
2. `The disk rolls and does not skid.` → 순수 구름
3. `The disk does not skid while rolling.` → 순수 구름
4. `원반이 skid 없이 굴러간다.` → 순수 구름
5. `mass on a string traces a conical path` → 원뿔진자
6. `a bob attached to a string sweeps out a cone` → 원뿔진자
7. `car on an inclined roadway curve, upper speed limit with static friction` → 경사진 커브 최대속도
8. `sloped turn maximum permissible velocity with mu_s` → 경사진 커브 최대속도
9. `bead on circular track at lower most point find normal force` → 수직 원운동 트랙 최저점
10. `원형 트랙 제일 아래에서 법선반력` → 수직 원운동 트랙 최저점
11. `particle position equals (3t, 2t^2); compute acceleration` → 직교좌표 위치벡터 미분
12. 순수 구름 출력에서 모순적 미끄럼 주의문 제거 검증

각 케이스는 적용식 비어 있지 않음, forbidden guard 적용, consistency check 통과, expected problem type, 금지식 미포함을 함께 검증한다.


## UI/UX SaaS Rework

- 학생 모드와 전문가/디버그 모드를 분리했습니다.
- 학생 모드에서는 `template_id`, AI confidence, cache hit, raw JSON, guard 내부 로그 등 검수용 정보가 기본 숨김 처리됩니다.
- 결과 화면을 문제 유형, 핵심 단서, FBD/좌표축, 적용식, 비적용식, 주의사항, 풀이 순서, 학생 풀이 비교, 저장/내보내기 카드로 재구성했습니다.
- 대표 동역학 유형 10종에 대해 간단한 SVG 기반 FBD 시각화를 추가했습니다.
- 예제 문제 라이브러리를 추가하여 버튼 클릭으로 대표 문제를 입력할 수 있습니다.
- Markdown/HTML/식-only 내보내기와 오답노트 저장을 추가했습니다.
- 오답노트는 검색, 문제 유형 필터, 오답만 보기, 즐겨찾기, 다시 풀기, JSON/Markdown 내보내기를 지원합니다.
- API key 값은 화면과 로그에 노출하지 않고, 학생 모드에서는 API 연결 상태와 fallback 가능 여부만 간단히 표시합니다.

실행:

```bash
pip install -r requirements.txt
streamlit run app.py
```

live smoke test:

```bash
python live_smoke_test.py
```

## UI/UX smoke and SaaS QA tests

| Test file / document | Scope | Result |
|---|---|---|
| `tests/test_ui_smoke_contract.py` | Student/debug mode separation, example library, FBD context, exports, records, friendly errors | Pass |
| `tools/ui_smoke_test.py` | Scripted UI contract smoke runner; writes reports under `docs/` | Pass |
| `docs/UI_SMOKE_TEST_RESULT.md` | UI smoke summary without browser session | Included |
| `docs/EXAMPLE_LIBRARY_TEST_RESULT.md` | 10 built-in examples produce problem type, FBD kind, applicable equations, no student debug leak | Included |
| `docs/RESPONSIVE_CHECK.md` | Desktop/tablet/mobile responsive checklist | Included |
| `docs/UI_SCREENSHOTS.md` | Browser screenshot capture guide and included wireframe assets | Included |
| `docs/UI_UX_FINAL_QA.md` | FBD condition rules, export QA, record QA, error-state policy | Included |

### UI acceptance checks covered by scripted tests

- Student mode public payload does not include `template_id`, raw JSON, AI confidence, cache hit, fallback log, model name, token estimate, traceback, or API key.
- Expert/debug panel exists and is gated by `view_mode == "전문가/디버그 모드"`.
- All 10 example problems generate non-empty applicable equations and FBD/coordinate data.
- FBD context hides friction for frictionless table/block-pulley problems.
- Banked curve max/min speed cases have different friction-direction guidance.
- Vertical-circle string/track cases prefer `T`/`N` respectively, while rail+tension conflict becomes ambiguous.
- Markdown, HTML, and equation-only exports are structured and redacted.
- Study records support save, favorite toggle, and delete in a temporary database.

## Final SaaS UI QA Patch Matrix

### Residual NL engine cases

| Case | Expected |
|---|---|
| `The contact point has slip while the disk rolls.` | sliding rotation; pure rolling equations blocked |
| `원통이 스키딩하며 굴러간다.` | sliding rotation; pure rolling equations blocked |
| `a bob on a string moves along a conical trajectory` | conical pendulum candidate/template |
| `a particle tied to a string describes a cone` | conical pendulum candidate/template |
| `경사진 곡선 도로에서 최대 허용 속력, μ_s` | banked curve with friction, max-speed template |
| `경사진 곡선 도로에서 최소 허용 속력, μ_s` | banked curve with friction, min-speed template |
| `particle position is equal to (3t, 2t^2), find velocity` | Cartesian position-vector differentiation |
| `the particle’s coordinates are <3t, 2t^2>; compute v` | Cartesian position-vector differentiation |

### UI QA artifacts

| Artifact | Purpose |
|---|---|
| `tests/test_ui_smoke_contract.py` | UI contract checks without browser dependency |
| `tools/ui_smoke_test.py` | Scripted smoke test and report generation |
| `docs/UI_BROWSER_QA_RESULT.md` | Browser/AppTest QA notes and environment limitation |
| `docs/assets/screenshots/*.png` | Rendered UI review images for first screen/result cards/FBD/notebook/mobile/export |
| `docs/export_examples/*` | Markdown/HTML/equations-only export examples |

## Final acceptance micro patch regression suite

File: `tests/test_final_micro_patch_nl.py`

This suite adds 16 final edge cases from the acceptance review. Each case checks semantic flags, expected problem/template family, applicable equations, forbidden equations, final guard state, and consistency-check state.

| Area | Added coverage |
|---|---|
| Contact slip positive | `There is slipping at the point of contact...`, `rolling disk has slip at the contact point` |
| Contact no-slip negation | `no slip exists at the contact point`, `there is no slip...`, `no point-of-contact slip` |
| Conical pendulum | `cone-shaped trajectory`, `cone shaped path`, Korean tilted string + horizontal circle |
| Banked curve minimum speed | `minimum permissible speed`, `minimum allowed velocity`, `lower permissible velocity` |
| Korean banked-curve sentence forms | “커브가 경사져 있고 마찰이 있을 때 최대/최소 허용 속도” |
| Cartesian vector shorthand | `particle coords are <...>`, `coordinates of the particle are (...)` |
| Smooth horizontal plane pulley | `smooth horizontal plane` + hanging block + pulley -> `f=0`, `T=m_Aa`, `m_Bg-T=m_Ba` |

Current full result:

```text
pytest -q -> 357 passed
coverage -> 95%
```

## 개인용 모바일 웹앱 패키징 테스트

| 영역 | 검증 내용 | 상태 |
|---|---|---|
| 비밀번호 보호 | APP_PASSWORD 기반 인증 helper, .env loader | 통과 |
| 모바일 탭 | 문제 분석 / 오답노트 / 복습 / 설정 탭 계약 | 통과 |
| 오답노트 | 난이도, 틀린 이유, 복습일, 즐겨찾기, 수정/삭제 | 통과 |
| 백업 | CSV / JSON / Markdown export | 통과 |
| 저장소 | SQLite 기본, DATABASE_URL 기반 Postgres/Supabase 선택 | 통과 |
| 문서 | DEPLOYMENT / REDEPLOYMENT / DB backup / home screen / costs | 통과 |
| 기존 엔진 | 기존 regression, expert, fourth, final, expression 테스트 유지 | 통과 |

## 개인용 모바일 웹앱 한계/범위 고지 테스트

- `tests/test_limitations_and_scope.py`
  - 이미지/그림 인식 미지원 안내 문서 존재
  - 완전 자동 수치 풀이 제한 고지
  - 3D 강체 운동/자이로스코프/오일러 방정식/관성텐서 입력 시 미지원 안내
  - 지원 범위 매트릭스와 앱 내부 한계 카드 노출 계약
  - 기호 입력 도우미/문제 템플릿 UI 계약 확인

- `tests/test_symbol_input_helpers.py`
  - θ, ω, α, μ, ΣF, ΣM_G 등 모바일 기호 버튼 정의
  - theta, omega, mu_s 등 ASCII 대체 표현 안내
  - 수평면 블록-도르래, 경사면, 수직 원운동, 원뿔진자, 경사진 커브, 순수 구름, 회전충돌 템플릿 제공

기대 결과: 사용자가 앱을 완전 자동 그림 풀이기나 3D 강체 해석기로 오해하지 않도록 앱 내부와 README/문서에 동일한 한계가 표시된다.

## 입문자 안전 모드 / 배포 위생 테스트

| 테스트 파일 | 검증 내용 |
|---|---|
| `tests/test_beginner_tutor_safety.py` | 정보 부족 입력에서 풀이 추천 중단, 문제 유형별 체크리스트, 적용식 설명, 입문자 단계 UI |
| `tests/test_distribution_hygiene.py` | 개인 DB/log/cache 제외 규칙, README의 입문자/정보 부족/개인 데이터 고지 |

대표 케이스:

- `그림과 같은 시스템에서 가속도를 구하라.` → 정보 부족, 추측성 풀이 중단
- `m_B g - T = m_B a` → 힘 방향과 좌표축 기반 설명 제공
- 배포물 → 개인 SQLite DB와 GPT call log 제외

## 입문자 안전 게이트 회귀 테스트

| 테스트 파일 | 목적 | 대표 검증 |
|---|---|---|
| `tests/test_beginner_strict_condition_gates.py` | 키워드 기반 추측 풀이 방지 | 경사면/원운동/rolling/curve 정보 부족 입력에서 적용식 비움 |
| `tests/test_beginner_strict_condition_gates.py` | 명확한 조건은 유지 | 순수 구름, 미끄럼 구름, 수직 원운동 최저/최고점, 평평한 커브 공식 출력 |
| `tests/test_beginner_strict_condition_gates.py` | 입문자 설명 강화 | `N_A = m_Ag`, `T = m_Aa`, `f = μN`, `ΣM_G = I_Gα` 설명 패턴 |
| `tests/test_beginner_strict_condition_gates.py` | 오답노트 약점 분석 | wrong_reasons 자동 태그 생성 |

현재 전체 pytest 결과: `402 passed`, coverage 총합 `95%`.


## Beginner Curve Strict Gate Regression

| Test file | Focus | Verified behavior |
|---|---|---|
| `tests/test_curve_strict_gate_final.py` | Bare curve prompts | `banked curve`, `flat curve`, generic curve, and circular-road speed prompts are treated as information-insufficient when radius/friction/bank-angle/limit conditions are missing. |
| `tests/test_curve_strict_gate_final.py` | Fully specified curve prompts | Flat curve with `R` and `μ_s`, frictionless banked curve design speed, and friction-limited banked curve max speed still show the proper equations. |
| `tests/test_curve_strict_gate_final.py` | Curve question wizard | Shows road-shape, radius, friction/μ_s, bank angle, max/min/design-speed, impending-slip, and slip-direction questions. |

## Beginner Tutor v1.0 Safety Requirements

| Area | Added tests | What is checked |
|---|---:|---|
| Block-pulley vs conical pendulum | 1 | `T cosθ = mg`, `T sinθ = mω²r`, `r = L sinθ` never appear in block-pulley output. |
| Conical pendulum confirmation | 1 | String + vertical angle + horizontal circular motion still produces conical pendulum equations. |
| Student misconception detection | 1 | Frictionless problem + `f = μN` in student solution raises a clear misconception warning. |
| Forbidden formula guard | 3 | Frictionless, sliding rolling, banked curve guards continue to block wrong formulas. |
| Numeric helper calculators | 2 | Block-pulley, incline, centripetal acceleration, vertical-circle force, collision/rolling checks, and common unit conversion helpers. |
| Wrong-note learning support | 2 | Auto wrong-reason tags, spaced review schedule, and difficulty classification helpers. |


## v1.1 오개념 탐지 스코핑 테스트

- `tests/test_beginner_v11_misconception_scoping.py`
  - TEST-006 원뿔진자에서 도르래 경고 금지
  - TEST-007 블록-도르래에서 도르래 전용 경고 유지
  - TEST-008 단일 줄 평형에서 도르래 경고 금지
  - TEST-009 단진자에서 도르래 경고 금지
  - TEST-010 애매한 줄 문제에서 경고 대신 확인 필요 출력

검증 결과: `pytest -q` 기준 432 passed, coverage 95%.

## v1.2 synonym robustness tests

| Area | Test file | Result |
|---|---|---|
| 줄/실/끈/로프 동의어 | `tests/test_beginner_v12_synonym_robustness.py` | passed |
| 단일 줄 평형 구어체 | `tests/test_beginner_v12_synonym_robustness.py` | passed |
| 단진자 작은 진폭/소진동/살짝 흔들림 | `tests/test_beginner_v12_synonym_robustness.py` | passed |
| 원뿔진자 연직선/각도/원을 그리며 돎 | `tests/test_beginner_v12_synonym_robustness.py` | passed |
| 도르래 오개념 경고 재발 방지 | `tests/test_beginner_v12_synonym_robustness.py` | passed |

Latest full run: `443 passed`, total coverage `95%`.
