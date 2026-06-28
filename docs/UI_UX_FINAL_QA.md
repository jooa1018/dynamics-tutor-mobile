# UI/UX Final QA

## Passed automated/contract checks

- Student/debug separation
- Example library payload completeness
- FBD context selection by problem type and condition
- Frictionless block-pulley FBD hides friction arrow
- Banked curve max/min friction direction text differs
- Vertical-circle string/track force symbols T/N are separated
- Export generation
- Notebook save/favorite/delete
- Friendly errors

## Browser limitation

The sandbox blocks Chromium/Playwright navigation to localhost and file URLs. Therefore true browser-click screenshots are not claimed. The final package includes Streamlit AppTest results, UI contract tests, rendered UI review PNGs, and local browser QA instructions.

## Remaining local acceptance step

Run `streamlit run app.py` in a normal user environment and capture the screens listed in `docs/UI_SCREENSHOTS.md`.
