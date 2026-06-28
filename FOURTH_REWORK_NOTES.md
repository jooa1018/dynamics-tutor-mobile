# 4차 개선 노트

## 반영한 핵심 요청

4차 개선에서는 “맞는 공식을 포함하는 것”보다 “문제 상황에 맞지 않는 공식을 적용식처럼 보여주지 않는 것”을 핵심 목표로 삼았습니다.

## 주요 변경

1. `SolutionBlueprint`에 구조화 필드 추가
   - `applicable_equations`
   - `not_applicable_equations`
   - `cautions`
   - `suppressed_templates`
   - `ambiguity_notes`
   - `support_level`

2. `dynamics_core/fourth_templates.py` 추가
   - 20개 대표 복합 문제 전용 템플릿
   - 템플릿 우선순위 적용
   - 잘못된 일반 템플릿 배제
   - 모호한 도르래 문제 정보 부족 안내

3. 앱 화면 수정
   - “이 문제에서 사용할 식”과 “이 문제에서 쓰면 안 되는 식”을 별도 영역으로 표시
   - 배제된 템플릿과 모호성 안내 표시

4. `fourth_regression_tests.py` 추가
   - 20개 대표 복합 문제 검증
   - `applicable_equations`에 금지식이 없는지 확인
   - `not_applicable_equations`와 `cautions`는 금지식 설명을 허용
   - 모호한 문제에서 억지 템플릿 적용 방지

## 통과한 테스트

```bash
python regression_tests.py
python expert_regression_tests.py
python fourth_regression_tests.py
```

결과:

```text
OK: all 2nd-rework regression tests passed
OK: expert regression tests passed — 100 representative cases, 50 counterexamples, and equation skeleton checks
OK: fourth regression tests passed — 20 complex cases, ambiguity handling, and area-aware forbidden-equation checks
```

## 남은 한계

- 그림 기반 기하 구조를 완전히 자동 해석하지는 못합니다.
- 조건이 생략된 문제는 추가 정보 안내 수준으로 처리합니다.
- 복잡한 연립방정식의 수치 자동 계산은 제한적입니다.
- 3차원 강체 운동과 비표준 링크/캠/벨트 문제는 완전 지원하지 않습니다.
