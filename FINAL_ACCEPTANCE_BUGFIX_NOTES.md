# Final Acceptance Bugfix Notes

## 수정 요약

이번 보정은 기존 하이브리드 재빌드 구조를 유지하면서 최종 수락 전 필수 버그를 수정한 버전입니다.

핵심 수정:

1. `without slipping`, `rolling without slipping`, `no slip`이 `slipping` 토큰 때문에 미끄럼 동반 회전으로 오판되는 문제 수정.
2. `장력`, `tension`, `rope force`, `string force`가 있으면 수직 원운동 최저점에서 `T`를 우선 사용하도록 수정.
3. `projectile hits and remains in a rod pivoted at one end` 계열을 탄환/투사체-회전강체 충돌로 인식하도록 보강.
4. `string makes ... with vertical while bob revolves in a circle` 계열을 원뿔진자로 인식하도록 보강.
5. `negligible friction`, `polished horizontal table` 계열을 마찰 없음 또는 마찰 없음 후보로 처리.
6. API key를 개발자에게 전달하지 않고, 사용자가 `.env` 또는 환경변수로 직접 넣어 live smoke test를 실행할 수 있도록 구성.

## 변경된 분류 로직

- `semantic_normalizer.py`에서 부정 slip 신호와 긍정 slip 신호를 분리했습니다.
- 순수 구름 신호가 있고 강한 positive slip 신호가 없으면 `slip_present=False`, `explicit_pure_rolling=True`가 됩니다.
- `not pure rolling`, `rolls but skids`, `contact point slips`는 positive slip으로 우선 처리합니다.
- 수직 원운동에서는 `tension/장력`이 있으면 줄/끈 문제로 보고 `T`를 우선 사용합니다.
- 탄환/투사체 충돌에서는 `projectile + remains/lodges/sticks + pivoted/fixed axis + rod/disk/wheel` 조합을 회전강체 충돌로 우선 처리합니다.

## 추가 테스트 목록

새 파일: `tests/test_final_acceptance_bugfixes.py`

- `cylinder rolls without slipping down incline.`
- `wheel rolls without slipping.`
- `wheel rolls but skids.`
- `바닥점의 장력은?`
- `lowest에서 tension?`
- `줄에 매단 공이 수직 원운동을 한다. lowest에서 tension을 구하라.`
- `a projectile hits and remains in a rod pivoted at one end; find angular velocity just after collision.`
- `string makes 30 degrees with vertical while bob revolves in a circle.`
- `block on table, friction is negligible, tied to hanging mass.`
- `a block sits on a polished horizontal table connected over a pulley to a hanging mass.`

## 테스트 결과

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
255 passed

coverage
TOTAL 2911 statements, 95% coverage
```

## API key 직접 검증 구조

- `.env.example` 포함.
- root `live_smoke_test.py` 포함.
- 내부 구현은 `tools/live_smoke_runner.py`.
- API key가 없으면 fallback 결과를 출력하고 정상 종료합니다.
- API key가 있으면 실제 GPT 호출, JSON Schema 응답, template rebuild, forbidden formula guard, cache/log 생성을 점검합니다.

## 현재 한계

- 실제 API 호출 성공 여부는 사용자가 `OPENAI_API_KEY`를 설정한 환경에서 실행해야 합니다.
- 그림 기반 기하 해석과 복잡한 수치 연립은 제한적입니다.
- GPT는 후보 판별 보조이며 최종 적용식은 내부 템플릿과 guard가 결정합니다.
