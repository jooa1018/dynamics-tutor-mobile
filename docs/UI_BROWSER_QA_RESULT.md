# UI Browser / App QA Result

## Summary

- Streamlit server boot: **passed**
- HTTP response check with `curl http://127.0.0.1:8501/`: **passed**
- Streamlit AppTest interaction smoke: **passed**
- UI contract smoke test: **passed**
- Real Chromium/Playwright browser navigation: **attempted but blocked by this sandbox policy**

## Why direct screenshots are marked separately

The execution sandbox allowed the Streamlit server to start and respond to `curl`, but both Playwright and Chromium navigation to `http://127.0.0.1:8501/` returned:

```text
ERR_BLOCKED_BY_ADMINISTRATOR
```

The same browser policy also blocked `file://` navigation. Because of that, true browser-click screenshots could not be captured in this environment. To keep the final package verifiable, this release includes three layers of UI QA:

1. `tools/ui_app_test_smoke.py` using Streamlit AppTest for app-level interaction checks.
2. `tools/ui_smoke_test.py` and `tests/test_ui_smoke_contract.py` for UI contract tests without a browser dependency.
3. `docs/assets/screenshots/*.png`, rendered from actual diagnosis/UI-contract data, for visual review of the intended SaaS screens.

## Streamlit AppTest result

```json
{
  "streamlit_apptest": "passed",
  "student_mode_default": true,
  "example_button_click": true,
  "diagnosis_button_click": true,
  "debug_mode_available": true,
  "raw_exception_visible": false
}
```

## Manual QA checklist covered

1. App renders without import/runtime error.
2. Student mode is the default option.
3. Example problem button inserts text into the problem field.
4. Diagnosis button runs without visible error.
5. Student payload excludes `template_id`, raw JSON, AI confidence, cache hit, fallback log, token logs, and API key markers.
6. Debug information is gated by expert/debug mode in `app.py`.
7. Built-in examples produce non-empty problem type, FBD/coordinate data, applicable equations, and steps.
8. Markdown, HTML, and equations-only exports preserve UTF-8 content.
9. Notebook save/favorite/delete roundtrip passes using isolated SQLite storage.
10. Friendly error messages do not expose raw tracebacks or API keys.

## Local browser QA command

In a normal local environment, run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then verify the screenshots listed in `docs/UI_SCREENSHOTS.md` against the actual browser UI.
