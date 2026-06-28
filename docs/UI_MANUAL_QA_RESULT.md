# UI Manual QA Result

## Result

- Streamlit import and AppTest execution: passed
- UI contract smoke test: passed
- Example library diagnostics: passed
- Export generation: passed
- Notebook save/favorite/delete roundtrip: passed
- API key absent fallback: passed
- Direct Chromium/Playwright click test: attempted, but blocked by sandbox browser policy (`ERR_BLOCKED_BY_ADMINISTRATOR`).

## Manual checklist for local environment

Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then verify:

1. Student mode is the default.
2. Expert/debug mode is available from the sidebar.
3. Built-in example buttons fill the input field.
4. Diagnosis renders problem type, evidence, FBD, applicable equations, not-applicable equations, steps, and solution comparison.
5. Student mode does not show `template_id`, raw JSON, AI confidence, cache hit, fallback log, model name, token log, or API key.
6. Expert/debug mode shows internal information only inside expanders.
7. Notebook can save, search, favorite, re-open, export, and delete records.
8. Markdown/HTML/equations-only exports preserve Korean and equations.
9. Mobile width stacks cards vertically and keeps FBD/SVG within viewport.
10. API key missing state uses rule-based fallback without exposing a raw exception.
