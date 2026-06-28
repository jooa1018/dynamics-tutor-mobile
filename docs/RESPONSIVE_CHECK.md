# Responsive Check

## Result

- Desktop layout: card layout expected to fit within 1180px container.
- Tablet layout: cards remain single-column friendly when width narrows.
- Mobile layout: CSS stacks cards vertically and constrains FBD SVG with `max-width: 100%; height: auto`.
- Expert/debug information is designed to remain in collapsed expanders.

## Evidence included

- `docs/assets/screenshots/10_mobile_result.png` contains a mobile-width rendered UI artifact based on the result card contract.
- Direct browser mobile screenshot could not be captured in this sandbox because Chromium navigation was blocked by administrator policy. Local verification command:

```bash
streamlit run app.py
```

Then open browser dev tools or mobile device preview and verify:

1. Problem input is not clipped.
2. Result cards stack vertically.
3. FBD SVG stays within viewport.
4. Formula blocks scroll or wrap safely.
5. Expert/debug sections remain collapsed.
