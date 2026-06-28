# UI/UX SaaS Rework Notes

This rework focuses on making the Streamlit app feel like a student-facing dynamics tutoring product rather than an internal validation dashboard.

## Implemented user-facing changes

1. **Student Mode / Expert Debug Mode**
   - Student Mode hides `template_id`, AI confidence, cache status, raw cue maps, fallback internals, and guard logs.
   - Expert Mode exposes those details inside a collapsed debug panel.

2. **Card-based diagnosis view**
   - Problem type card
   - Evidence card
   - FBD / coordinate-system card
   - Applicable equations card
   - Not-applicable equations card
   - Cautions / common mistakes card
   - Step-by-step solution card
   - Student-solution comparison card
   - Export/save card

3. **FBD visualizations**
   Added lightweight inline SVG diagrams for:
   - horizontal block-pulley
   - incline body
   - pure rolling cylinder/disk
   - sliding rotation
   - vertical circle with string tension
   - vertical circle with track normal force
   - conical pendulum
   - banked curve
   - bullet/projectile embedded in rotating rigid body
   - Cartesian position-vector kinematics

4. **Example library**
   Ten representative examples can be inserted into the problem input with one click.

5. **Study record / error-note UX**
   - Saves problem, detected type, applicable equations, not-applicable equations, missing items, misconception tags, memo, and favorite flag.
   - Adds search, type filter, mistake-only filter, favorite-only filter, retry button, JSON export, and Markdown export.

6. **Export**
   - Current diagnosis can be exported as Markdown, HTML, or equations-only text.
   - Full study history can be exported as JSON or Markdown.

7. **AI/API UX**
   - Student Mode shows simple status only: AI assist on/off, API configured/missing, fallback available.
   - API key value is never displayed.
   - AI feedback failures show a friendly fallback message rather than raw exception text.

8. **Responsive design**
   - Card widths and formulas use wrapping/overflow handling.
   - Expert/debug blocks are collapsed by default, especially useful for mobile.

## Remaining limitations

- FBD diagrams are schematic SVGs, not geometry-accurate drawings extracted from textbook figures.
- Streamlit remains a rapid-app framework; a production SaaS deployment would still benefit from a custom front end, authentication, billing, telemetry, and robust persistence.
- PDF export is not implemented directly; Markdown and HTML export are provided first because they are robust and easy to review.

## 최종 UI/UX QA 보강

이번 패치에서는 SaaS UI를 실제 학생 사용 흐름 기준으로 한 번 더 보강했습니다.

- `dynamics_core/ui_helpers.py`를 추가하여 예제 라이브러리, 학생 공개 payload, FBD 문맥 선택, 내보내기 생성, 오류 메시지를 Streamlit 없이도 테스트할 수 있게 했습니다.
- `tests/test_ui_smoke_contract.py`를 추가하여 학생 모드 디버그 정보 비노출, 예제 10개 진단, FBD 문맥, 내보내기, 오답노트 저장/즐겨찾기/삭제를 검증합니다.
- `tools/ui_smoke_test.py`를 추가하여 브라우저 없이 UI 계약 smoke test를 실행하고 `docs/UI_SMOKE_TEST_RESULT.md`, `docs/EXAMPLE_LIBRARY_TEST_RESULT.md`를 생성합니다.
- FBD 문맥 선택을 개선하여 frictionless block-pulley에서는 마찰력 화살표를 숨기고, banked curve 최대/최소속도에서는 마찰 방향 안내가 다르게 표시됩니다.
- rail/track과 tension이 충돌하는 경우 무리하게 T/N 중 하나로 확정하지 않고 모호성 안내를 표시합니다.
- Markdown/HTML/equation-only 내보내기는 학생 공개 payload에서 생성되며 API key나 내부 로그를 포함하지 않습니다.
- 오답노트에 기록 삭제와 즐겨찾기 토글을 추가했습니다.

브라우저 클릭 테스트는 이 실행 환경에서 수행하지 못했으므로, 배포 환경에서 `streamlit run app.py` 후 `docs/UI_SCREENSHOTS.md`의 체크리스트에 따라 실제 화면 캡처를 진행해야 합니다.
