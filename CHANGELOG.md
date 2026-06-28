
## v1.1 오개념 탐지 안전 패치

- 원뿔진자/단진자/단일 줄 평형 문제에서 도르래 전용 오개념 경고가 뜨지 않도록 수정했습니다.
- 오개념 탐지는 단순 키워드보다 최종 문제 유형을 우선하도록 제한했습니다.
- 블록-도르래로 확정된 경우에만 가속도 관계 및 매달린 물체 B 운동방정식 누락 경고를 표시합니다.
- 애매한 줄 문제는 경고 대신 확인 필요 질문을 표시합니다.
- `tests/test_beginner_v11_misconception_scoping.py`를 추가했습니다.


## Final natural-language robustness pass

- Fixed `without slip` / `no slip occurs` / `slipping does not occur` so they select pure rolling rather than sliding rotation.
- Expanded positive slip detection for `with slip`, `point of contact slips`, Korean mixed `slip하며 굴러간다`, and `미끄럼을 가지고 구른다`.
- Expanded bullet/projectile rotating-rigid-body collision recognition for hinged/pivoted bars and Korean `투사체 ... 피벗된 막대 ... 붙는다`.
- Strengthened Cartesian position-vector priority for `r vector = ... i + ... j`, `<x,y>`, and `(x,y)` forms.
- Added conical pendulum English natural-language variants.
- Added rail/tension ambiguity handling and ensured bottom-cord tension formulas are never empty.
- Added banked/inclined curve max/min speed variants and loop-the-loop contact-maintenance templates.
- Added `tests/test_final_natural_language_robustness.py` with 29 additional regression cases.
- Corrected live smoke test command references to `python live_smoke_test.py`.

# CHANGELOG

## Hybrid Template Rebuild Pipeline

- Added `dynamics_core/template_rebuild.py`.
- Added explicit GPT candidate → internal template_id mapping.
- Added reconciliation logic that can rebuild the final template from validated GPT candidates.
- Added final forbidden formula guard after template rebuild.
- Added high-risk triggers for projectile/bullet fixed-axis collision, bottom/tension vertical circle, slipping rolling, cartesian/polar conflict, conical pendulum candidates, and friction conflicts.
- Updated Streamlit sidebar so `OPENAI_API_KEY` is read from the environment and placeholder text is not used as a key.
- Added pytest tests for GPT candidate rebuild, reconciliation, fallback, and user failure cases.
- Added `HYBRID_REBUILD_PIPELINE.md` and `live_smoke_test.py`.

## Final Acceptance Bugfix + User-Owned API Smoke Test

- Fixed `without slipping` / `no slip` priority so negated slip phrases are not misclassified as sliding rotation.
- Added positive slip priority for `with slipping`, `contact point slips`, `rolls but skids`, and Korean slip-occurrence variants.
- Updated vertical-circle force-symbol selection so `tension`, `장력`, `rope force`, and `string force` use `T` even in short bottom-point questions.
- Expanded projectile/bullet rotating-body collision recognition: `remains in`, `lodges in`, `hits and remains`, `pivoted rod`, `fixed pivot`, and `angular velocity just after collision`.
- Expanded conical-pendulum English recognition: `bob revolves in a circle`, `string makes angle with vertical`, and related forms.
- Expanded frictionless table recognition: `negligible friction`, `friction may be neglected`, and `polished horizontal table`.
- Added `.env.example` and root-level `live_smoke_test.py` so users can run live OpenAI smoke tests with their own API key.
- Added no-key fallback behavior to `live_smoke_test.py`; it does not fail without `OPENAI_API_KEY`.
- Added `tests/test_final_acceptance_bugfixes.py` covering the final user-reported acceptance blockers.
- Updated coverage config to omit operational live-smoke scripts from library coverage accounting.

## Final residual natural-language robustness patch

- Fixed `without any slipping` / `without any slip` / `no slip occurs` priority so negative slip expressions override the raw `slip` token.
- Added explicit handling for `rolling while slipping`, `rolls and slips`, and related Korean slipping-while-rolling expressions.
- Extended banked-curve recognition for `sloped curve`, `inclined road curve`, `highest speed`, `최고 속도`, and `최저 속도`.
- Added Korean conical-pendulum phrasing such as `원뿔 운동`.
- Added vertical circular rail bottom normal-force handling for `원형 레일의 최하점에서 수직항력`.
- Added final consistency guard to keep applicable equations, non-applicable equations, and cautions from contradicting each other.
- Added `tests/test_final_residual_nl_bugs.py`.
- Updated coverage report: 295 pytest cases, 95% coverage.

---

## Final Ontology-Guided Rework

### Added

- `docs/PHYSICS_ONTOLOGY.md`: 동역학 문제 유형별 template_id, 적용식, 비적용식, 모호성 정책 정리.
- `docs/DYNAMICS_GLOSSARY_KO_EN.md`: 한영/혼합 표현군 사전과 우선순위 정리.
- `docs/DECISION_TREE.md`: 좌표계, 구름/미끄럼, 원운동, 충돌, 마찰 조건 우선순위 정리.
- `docs/FORBIDDEN_FORMULA_TABLE.md`: template별 적용식 영역 금지식 표.
- `docs/AMBIGUITY_POLICY.md`: 정보 부족/단서 충돌 시 출력 정책.
- `docs/FINAL_CONSISTENCY_CHECK.md`: 최종 guard 검사 항목 문서화.
- `dynamics_core/consistency_guard.py`: GPT/template rebuild 이후 최종 적용식/비적용식 일관성 검사.
- `tests/test_domain_ontology_regression.py`: 표현군 단위 도메인 회귀 테스트 16개 추가.

### Changed

- `semantic_normalizer.py`
  - `without skidding`, `not slipping as it rolls`, `rolling but not slipping`를 순수 구름으로 정규화.
  - `slips while rolling`, `there is slip at the contact point`, `skidding while rolling`을 미끄럼 동반 회전으로 정규화.
  - `slanted curve`, `canted curve`, `fastest/greatest speed`, `가장 큰/작은 속력`, `뱅크 도로` 표현 보강.
  - `moves like a cone`, 한국어 수평 원운동 + 수직선 각도 조합을 원뿔진자로 정규화.
  - `r vector equals ... i-hat plus ... j-hat`, `particle has position (x,y)`를 직교좌표 위치벡터로 정규화.
- `fourth_templates.py`와 `template_rebuild.py`에서 최종 consistency guard를 호출하도록 연결.

### Verified

```text
python regression_tests.py → OK
python expert_regression_tests.py → OK
python fourth_regression_tests.py → OK
python final_quality_tests.py → OK
python expression_variation_tests.py → OK
pytest -q → 311 passed
coverage → TOTAL 3184 statements, 95%
python live_smoke_test.py without API key → fallback_test passed
```

### Known limits

- 그림 기반 기하 해석, 복잡한 다물체 기구 해석, 완전 자동 수치 연립 계산은 제한적입니다.
- GPT 보조 판별은 API key가 있을 때만 활성화되며, 최종 물리식은 규칙 엔진과 consistency guard가 검증합니다.

## Ontology Final Code-Alignment Patch

- `without any skidding`, `does not skid`, `skid 없이` 부정 skid 표현을 순수 구름으로 우선 처리하도록 정규화 우선순위를 수정했습니다.
- `conical path`, `traces a cone`, `sweeps out a cone` 표현을 원뿔진자 후보/템플릿으로 연결했습니다.
- `inclined roadway curve`, `sloped turn`, `maximum permissible velocity`, `upper speed limit` 표현을 경사진 커브 최대속도 계열로 확장했습니다.
- `lower most point`, `lowermost point`, `제일 아래`, `법선반력`을 수직 원운동 트랙 최저점 수직항력으로 처리하도록 보강했습니다.
- `particle position equals (x(t), y(t))` 괄호형 위치벡터를 직교좌표 위치벡터 미분으로 처리했습니다.
- 순수 구름 결과에서 현재 문제가 미끄럼 상황인 것처럼 보이는 모순적 주의문을 제거하고, 긍정형 순수 구름 주의문으로 대체했습니다.
- `tests/test_docs_code_alignment_final.py`를 추가해 문서에 적힌 glossary/ontology 표현과 실제 런타임 출력의 일치성을 검증합니다.

## UI/UX SaaS Rework

- Reworked the Streamlit app from an internal diagnostic dashboard into a student-facing tutoring flow.
- Added Student Mode and Expert/Debug Mode. Student Mode hides template IDs, AI confidence, cache status, raw JSON, and guard logs by default.
- Added card-based result sections: problem type, evidence, FBD/coordinate visualization, applicable equations, not-applicable equations, cautions, steps, student-solution comparison, and export/save.
- Added simple SVG FBD visualizations for representative dynamics templates: block-pulley, incline, pure rolling, sliding rotation, vertical circle with string, vertical circle with track, conical pendulum, banked curve, bullet-rotating-body collision, and Cartesian position-vector motion.
- Added example problem library with one-click insertion for 10 representative problem types.
- Improved AI/API UX: key values are never displayed; Student Mode shows only connection status and fallback availability.
- Replaced raw AI exception display with user-friendly fallback messages.
- Improved study records into an error-note flow with search, type filtering, mistake-only filtering, favorites, retry, JSON export, and Markdown export.
- Added Markdown/HTML/equation export for the current diagnosis.
- Added responsive card styling, consistent colors, formula blocks, badges, and mobile-friendly layout rules.

## UI/UX final QA patch

- Added `dynamics_core/ui_helpers.py` for UI-contract logic that can be tested without a Streamlit browser session.
- Added `tests/test_ui_smoke_contract.py` covering student/debug separation, example library behavior, FBD contexts, exports, records, and friendly errors.
- Added `tools/ui_smoke_test.py` to produce `docs/UI_SMOKE_TEST_RESULT.md` and `docs/EXAMPLE_LIBRARY_TEST_RESULT.md`.
- Added documentation: `docs/RESPONSIVE_CHECK.md`, `docs/UI_SCREENSHOTS.md`, `docs/UI_UX_FINAL_QA.md`, and SVG wireframe assets.
- Improved FBD context selection:
  - Frictionless block-pulley diagrams hide friction force.
  - Banked curve maximum/minimum speed cases show different friction-direction guidance.
  - String vertical-circle cases use `T`; track/rail cases use `N`; rail+tension conflicts show ambiguity.
- Improved export generation so Markdown/HTML/equation-only outputs are based on student-safe payloads.
- Added record-level favorite toggle and delete helpers.
- Added friendlier empty/short/error messages for student mode.

## SaaS UI Final QA Patch

- Added residual natural-language regression tests for contact-point slip, Korean skidding, conical trajectory, describes-a-cone, spaced Korean banked-road expressions, and coordinate vector variants.
- Strengthened semantic normalizer for `contact point has slip`, `스키딩하며`, `conical trajectory`, `describes a cone`, `position is equal to (...)`, and `coordinates are <...>`.
- Added generated export examples under `docs/export_examples/`.
- Added UI browser/AppTest QA documentation under `docs/UI_BROWSER_QA_RESULT.md` and rendered UI review images under `docs/assets/screenshots/`.
- Rewrote README as final user-facing documentation and moved development history to CHANGELOG.

## Final acceptance micro patch — natural-language edge cases

- Added `tests/test_final_micro_patch_nl.py` with 16 final acceptance edge cases.
- Strengthened contact-point slip/no-slip priority rules:
  - positive slip: `there is slipping at the point of contact`, `rolling disk has slip at the contact point`, `contact patch has slipping`, `point-of-contact slip exists while rolling`.
  - negated slip: `no slip exists at the contact point`, `there is no slip at the point of contact`, `no point-of-contact slip`, `contact patch has no slip`.
- Extended conical-pendulum ontology coverage:
  - `cone-shaped trajectory/path`, `moves in a cone shaped path`, Korean tilted-string + horizontal-circle expressions.
- Extended banked-curve speed-limit coverage:
  - `minimum permissible speed/velocity`, `minimum allowed velocity`, `lower permissible velocity`, Korean sentence-form “커브가 경사져 있고 마찰이 있을 때 최대/최소 허용 속도”.
- Extended Cartesian-position-vector coverage:
  - `particle coords are <x(t), y(t)>`, `coordinates of the particle are (x(t), y(t)>`, `particle coordinates are (...)`.
- Added `smooth horizontal plane` to the frictionless horizontal plane/table + hanging block + pulley detector.
- Verified no regression in UI smoke, AppTest smoke, export examples, fallback live smoke, and the official regression suites.

Validation:

```text
pytest -q                         -> 357 passed
coverage run -m pytest -q          -> 357 passed
coverage report -m                 -> TOTAL 3598 statements, 95% coverage
python regression_tests.py          -> OK
python expert_regression_tests.py   -> OK
python fourth_regression_tests.py   -> OK
python final_quality_tests.py       -> OK
python expression_variation_tests.py -> OK
python tools/ui_smoke_test.py       -> passed
python tools/ui_app_test_smoke.py   -> passed
python live_smoke_test.py           -> skipped_no_api_key fallback passed
python -m compileall -q .           -> success
```

## Mobile Personal Web App Package

- Added environment/secrets-based `APP_PASSWORD` gate for personal URL protection.
- Reorganized the Streamlit app into mobile-first tabs: 문제 분석, 오답노트, 복습, 설정.
- Added extended wrong-note fields: wrong reasons, difficulty, review due date, review flag.
- Added CSV backup export alongside JSON and Markdown.
- Added optional Supabase/Postgres storage path via `DATABASE_URL`, with SQLite as local fallback.
- Added mobile deployment, redeployment, database backup/restore, home-screen, and operating cost documents.
- Added `tests/test_mobile_webapp_packaging.py` and updated coverage report.

## Personal mobile webapp scope/limitations patch

- 앱 내부 `지원 범위와 한계` 카드 추가.
- 이미지/그림 직접 인식 불가, 완전 자동 수치 풀이 제한, 3D 강체 운동 미지원, Streamlit 모바일 웹앱 한계를 README와 docs에 명시.
- 3D 강체 운동, 자이로스코프, 오일러 방정식, 관성텐서, 회전좌표계, 코리올리 가속도 표현을 미지원 범위로 감지하여 2D 공식으로 오분류하지 않도록 보강.
- 모바일 문제 입력창에 기호 입력 도우미와 자주 쓰는 문제 템플릿 버튼 추가.
- `docs/LIMITATIONS.md`, `docs/IMAGE_INPUT_LIMITATION.md`, `docs/NUMERIC_SOLVER_LIMITATION.md`, `docs/UNSUPPORTED_3D_DYNAMICS.md`, `docs/SUPPORT_SCOPE_MATRIX.md`, `docs/INPUT_GUIDE.md`, `docs/STREAMLIT_MOBILE_LIMITATION.md`, `docs/MOBILE_QA_CHECKLIST.md` 추가.
- `tests/test_limitations_and_scope.py`, `tests/test_symbol_input_helpers.py` 추가.

## Final beginner tutor safety patch

- 입문자 모드 추가: 핵심 유형 → FBD → 핵심 원리 → 첫 식 → 다음 식 → 비적용식 → 실수 → 직접 계산 순서.
- 정보 부족 입력에서 추측성 풀이 추천을 중단하는 `assess_information_sufficiency` 추가.
- 문제 유형별 그림 정보 체크리스트와 추가 질문 제공.
- 적용식/비적용식마다 초보자용 설명을 붙이는 UI helper 추가.
- 오답노트/복습에서 자주 틀리는 실수 유형 Top 5 표시 강화.
- 배포용 ZIP에서 개인 DB, GPT 로그, 캐시, 임시 파일을 제외하도록 `.gitignore` 및 패키징 규칙 정리.
- 테스트 추가: `tests/test_beginner_tutor_safety.py`, `tests/test_distribution_hygiene.py`.

## Beginner strict condition gate patch

- 키워드만 있는 경사면/원운동/구름/커브 문제에서 추측성 적용식 출력을 중단했습니다.
- `assess_information_sufficiency()`에 유형별 필수 조건 검사를 추가했습니다.
- `question_wizard_for_text()`로 경사면, 도르래, 원운동, 구름, 충돌, 원뿔진자별 질문형 입력 마법사를 제공합니다.
- `A cylinder is rolling`처럼 rolling만 있는 입력은 순수 구름으로 확정하지 않습니다.
- `A disk slips as it rolls`를 미끄럼 동반 회전으로 보강했습니다.
- 비적용식 중복 제거를 강화했습니다.
- 적용식 설명에 `N_A = m_Ag`, `T = m_Aa`, `f = μN`, `ΣM_G = I_Gα` 설명 패턴을 추가했습니다.
- 오답노트 저장 시 wrong_reasons가 비어 있으면 자동 약점 태그를 추정합니다.
- `tests/test_beginner_strict_condition_gates.py`를 추가했습니다.


## Beginner curve strict gate patch

- Strengthened beginner-mode curve driving gates so bare `banked curve`, `flat curve`, or generic `curve` prompts do not show formula-like applicable equations.
- Added `tests/test_curve_strict_gate_final.py` with 12 curve-driving cases: 6 insufficient prompts and 6 sufficiently specified prompts.
- Added curve-specific question wizard items for road shape, radius R, friction/μ_s, bank angle θ, max/min/design speed, impending slip, and slip direction.
- Preserved symbolic-skeleton support for clearly framed expert cases such as minimum friction coefficient, frictionless banked-curve design relationship, and friction-limited banked curve with limiting-speed ambiguity.
- Updated final residual test expectations for `inclined road curve maximum allowable velocity` to follow the new beginner strict gate: additional conditions are required before formula output.

Validation:

```text
pytest -q                         -> 415 passed
coverage run -m pytest -q          -> 415 passed
coverage report -m                 -> TOTAL 4410 statements, 95% coverage
python regression_tests.py          -> OK
python expert_regression_tests.py   -> OK
python fourth_regression_tests.py   -> OK
python final_quality_tests.py       -> OK
python expression_variation_tests.py -> OK
python tools/ui_smoke_test.py       -> passed
python live_smoke_test.py           -> skipped_no_api_key fallback passed
python -m compileall -q .           -> success
```

## Beginner Tutor v1.0 Safety Patch

- Fixed the highest-priority contamination bug where horizontal block-pulley problems could inherit conical pendulum formulas through broad `string/hanging/horizontal` cues.
- Added block-pulley dominance rules: if block + horizontal surface + pulley + hanging mass are detected, conical pendulum formulas are removed from applicable equations and excluded as a candidate.
- Tightened conical pendulum confirmation: conical formulas require explicit cone/conical wording or the physical structure of string + horizontal circular motion + vertical angle.
- Added stronger student-solution misconception detection for frictionless problems, unverified pure rolling constraints, banked-curve `N=mg`, vertical-circle sign errors, pulley acceleration constraints, inelastic collision energy misuse, and nonconservative energy misuse.
- Added beginner numeric helper functions for frictionless block-pulley, simple incline, centripetal acceleration, vertical-circle force, and common unit conversions.
- Added review scheduling and difficulty classification helpers for wrong-note review.
- Added `tests/test_beginner_tutor_v10_requirements.py`; total pytest suite now passes with 427 tests.

## Beginner Tutor v1.2 — Natural-language synonym robustness

- Added `dynamics_core/lexicon.py` as a shared synonym/normalization layer.
- Treated 줄/실/끈/로프/cord/string/rope/cable as rope-like support cues without making them pulley cues by themselves.
- Added rest/equilibrium variants such as 가만히 있음, 움직이지 않는다, 평형, at rest, equilibrium.
- Added simple pendulum variants such as 작은 진폭, 소진동, 살짝 흔들림, small oscillation.
- Added conical pendulum variants such as 연직선과 각도 θ, 원을 그리며 돎, 수평 원운동.
- Preserved v1.1 safety: simple pendulum, conical pendulum, and single-string equilibrium never trigger pulley-specific misconception warnings.
- Added TEST-011 through TEST-020 in `tests/test_beginner_v12_synonym_robustness.py`.
