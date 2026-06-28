# Curve Driving Strict Gate QA Result

## 목적

입문자 모드에서 `curve`, `flat curve`, `banked curve` 키워드만 보고 공식을 확정하지 않도록 커브 주행 문제 전용 strict gate를 추가로 강화했다.

## 추가된 안전 규칙

커브 주행 문제는 다음 조건이 충분히 확인될 때만 구체식을 적용식으로 제시한다.

- 평평한 커브인지 경사진/banked 커브인지
- 커브 반지름 `R`
- 마찰 있음/없음
- 평평한 커브 최대속도라면 정지마찰계수 `μ_s` 또는 마찰 한계 조건
- 경사진 커브 설계속도라면 마찰 없음과 경사각/속도 관계 조건
- 경사진 커브 최대/최소속도라면 마찰 한계 또는 미끄러짐 방향

단, 기존 고급/검수용 symbolic skeleton 테스트와 충돌하지 않도록 다음은 허용한다.

- “최소 마찰계수” 자체를 구하는 flat curve 문제
- “마찰 있음 + limiting speed”처럼 최대/최소 방향이 불명확한 banked curve는 적용식 확정 대신 속도 한계 정보 보완 카드
- “frictionless/smooth banked curve에서 속도-경사각 관계”처럼 설계속도 관계를 묻는 문제

## 정보 부족으로 처리하는 신규 회귀 입력

- `A car moves on a banked curve. Find maximum speed.`
- `A car moves on a flat curve. Find maximum speed.`
- `자동차가 경사진 커브를 돈다. 최대속도를 구하라.`
- `자동차가 평평한 커브를 돈다. 최대속도를 구하라.`
- `A car turns on a curve. Find speed.`
- `A vehicle travels around a circular road. Find maximum speed.`

위 입력들은 `applicable_equations`를 비우고, 다음을 질문형 마법사로 안내한다.

1. 도로는 평평한가요, 경사져 있나요?
2. 커브 반지름 `R`이 주어졌나요?
3. 마찰이 있나요? 있다면 정지마찰계수 `μ_s`가 주어졌나요?
4. 경사진 커브라면 경사각 `theta`가 주어졌나요?
5. 구하는 값은 최대속도인가요, 최소속도인가요, 설계속도인가요?
6. 미끄러지기 직전 조건인가요?
7. 경사진 커브라면 차량이 위쪽으로 미끄러지려 하나요, 아래쪽으로 미끄러지려 하나요?

## 식 제시가 가능한 입력

- `반지름 R인 평평한 원형 도로에서 정지마찰계수 μ_s일 때, 자동차가 미끄러지기 직전 최대 속도를 구하라.`
- `A car moves on a flat curve of radius R with coefficient of static friction μ_s. Find the maximum speed before slipping.`
- `반지름 R, 경사각 θ인 마찰 없는 경사진 커브에서 설계속도를 구하라.`
- `A car travels on a frictionless banked curve of radius R and bank angle θ. Find the design speed.`
- `반지름 R, 경사각 θ, 정지마찰계수 μ_s가 주어진 경사진 커브에서 최대속도를 구하라.`
- `A car travels on a banked curve of radius R and angle θ with coefficient of static friction μ_s. Find the maximum speed before slipping.`

## 검증 결과

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
