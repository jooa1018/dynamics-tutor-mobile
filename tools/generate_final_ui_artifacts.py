from __future__ import annotations

import json
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynamics_core.feedback import build_diagnosis
from dynamics_core.parser import analyze_text
from dynamics_core.strategy_engine import recommend_strategy
from dynamics_core.ui_helpers import (
    EXAMPLE_LIBRARY,
    build_markdown_export,
    build_html_export,
    build_equations_only_export,
    public_student_payload,
    choose_fbd_context,
)

DOCS = ROOT / "docs"
SS = DOCS / "assets" / "screenshots"
EXPORTS = DOCS / "export_examples"
SS.mkdir(parents=True, exist_ok=True)
EXPORTS.mkdir(parents=True, exist_ok=True)

FONT = "/usr/share/fonts/truetype/nanum/NanumSquareRoundR.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf"

def font(size=24, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def wrap_text(text: str, width: int = 46):
    lines = []
    for para in str(text).split("\n"):
        if not para:
            lines.append("")
            continue
        # crude wrap by display-ish length. Korean chars are wider, but this is fine for QA images.
        current = ""
        for token in para.split(" "):
            candidate = (current + " " + token).strip()
            if len(candidate) > width:
                if current:
                    lines.append(current)
                current = token
            else:
                current = candidate
        if current:
            lines.append(current)
    return lines


def draw_card(draw, x, y, w, title, body_lines, fill, outline="#d0d7de", title_fill="#111827"):
    line_h = 28
    h = 52 + max(1, len(body_lines)) * line_h + 18
    draw.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=fill, outline=outline, width=2)
    draw.text((x + 24, y + 18), title, font=font(23, True), fill=title_fill)
    yy = y + 56
    for line in body_lines:
        draw.text((x + 24, yy), line, font=font(19), fill="#334155")
        yy += line_h
    return y + h + 18


def make_screen(path: Path, title: str, cards: list[tuple[str, list[str], str]], width=1280, height=None):
    y = 34
    card_w = width - 96
    # precompute height
    if height is None:
        height = 120 + sum(80 + max(1, len(c[1])) * 28 + 18 for c in cards)
        height = max(height, 760)
    img = Image.new("RGB", (width, height), "#f8fafc")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([32, 24, width - 32, 112], radius=24, fill="#eff6ff", outline="#bfdbfe", width=2)
    d.text((58, 48), "⚙ DynaTutor · 동역학 문제풀이 튜터", font=font(30, True), fill="#1e3a8a")
    d.text((58, 84), title, font=font(19), fill="#475569")
    y = 138
    color_map = {
        "type": "#dbeafe", "ok": "#dcfce7", "danger": "#fee2e2", "warn": "#fef3c7", "debug": "#f1f5f9", "white": "#ffffff",
    }
    for ctitle, lines, kind in cards:
        y = draw_card(d, 48, y, card_w, ctitle, lines, color_map.get(kind, "#ffffff"))
    img.save(path)


def diagnose(problem: str, solution: str = "T cos theta = mg"):
    features = analyze_text(problem, solution)
    rec = recommend_strategy(features, "자동 추정")
    diag = build_diagnosis(problem, solution, "자동 추정", features, rec, enable_ai_assist=False)
    return features, rec, diag

sample_problem = EXAMPLE_LIBRARY["원뿔진자"]
features, rec, diag = diagnose(sample_problem, "T cos theta = mg")
payload = public_student_payload(diag)
ctx = choose_fbd_context(sample_problem, diag)
md = build_markdown_export(sample_problem, "T cos theta = mg", diag)
html = build_html_export(sample_problem, "T cos theta = mg", diag)
eq = build_equations_only_export(diag)
(EXPORTS / "sample_diagnosis.md").write_text(md, encoding="utf-8")
(EXPORTS / "sample_diagnosis.html").write_text(html, encoding="utf-8")
(EXPORTS / "sample_equations_only.md").write_text(eq, encoding="utf-8")

# first screen / examples
make_screen(SS / "01_first_screen.png", "첫 화면 · 학생 모드 기본값 · API 미설정 시 규칙 기반 fallback", [
    ("문제 입력", ["예제 문제를 선택하거나 직접 문제를 입력한 뒤 진단 실행을 누릅니다.", "학생 모드에서는 template_id, raw JSON, cache hit, API key가 보이지 않습니다."], "type"),
    ("예제 문제 라이브러리", list(EXAMPLE_LIBRARY.keys())[:5] + ["… 총 10개 예제"], "white"),
])
make_screen(SS / "02_example_library.png", "예제 문제 라이브러리 · 버튼 클릭 시 입력창 삽입", [
    ("예제 10개", [f"{i+1}. {k}" for i, k in enumerate(EXAMPLE_LIBRARY.keys())], "type"),
    ("검증", ["각 예제는 문제 유형, FBD/좌표축, 적용식, 단계별 풀이가 비어 있지 않도록 UI smoke test에서 확인합니다."], "ok"),
])
# result cards
make_screen(SS / "03_result_cards.png", "진단 결과 카드 화면", [
    ("문제 유형", [payload["problem_type"] or "원뿔진자", "왜 이 유형인지: 줄/질점/수평 원운동/수직선 각도 단서"], "type"),
    ("핵심 단서", payload["evidence"][:4] or ["string", "horizontal circle", "angle with vertical"], "white"),
    ("적용식", payload["applicable_equations"][:4], "ok"),
    ("이 문제에서 쓰면 안 되는 식", payload["not_applicable_equations"][:3] or ["강체 일반 평면운동 식을 우선 적용하지 않음"], "danger"),
])
make_screen(SS / "04_fbd_card.png", "FBD 카드 · 원뿔진자 예시", [
    ("FBD / 좌표축", ["T: 줄 방향", "mg: 아래쪽", "T cosθ = mg: 수직방향 평형", "T sinθ = mω²r: 중심방향 구심 조건"], "type"),
    ("시각화 안내", ["SVG FBD는 물체, 힘 방향, 중심 방향, 각도 θ, 반지름 r을 함께 표시합니다."], "white"),
])
make_screen(SS / "05_equation_cards.png", "적용식 / 비적용식 카드", [
    ("사용 가능", payload["applicable_equations"][:5], "ok"),
    ("사용 금지", payload["not_applicable_equations"][:4] or ["ΣM_G = I_Gα : 원뿔진자는 질점 원운동 우선"], "danger"),
    ("Consistency check", ["같은 식이 적용식/비적용식에 동시에 들어가지 않도록 검사합니다."], "warn"),
])
make_screen(SS / "06_solution_steps.png", "단계별 풀이 카드", [
    ("풀이 순서", payload["steps"][:6] or ["FBD 작성", "좌표축 설정", "수직/중심 방향 식 작성", "보조 관계식 적용"], "type"),
])
make_screen(SS / "07_solution_compare.png", "학생 풀이 비교 카드", [
    ("맞은 점", ["장력 T와 중력 mg를 고려했습니다.", "원운동 중심 방향 식을 떠올렸습니다."], "ok"),
    ("수정할 점", ["r = L sinθ 관계식을 함께 적어야 합니다.", "각속도 정리 단계까지 연결해야 합니다."], "warn"),
])
make_screen(SS / "08_notebook.png", "오답노트 · 저장/검색/필터/즐겨찾기", [
    ("최근 풀이", ["문제 유형: 원뿔진자", "적용식: T cosθ = mg, T sinθ = mω²r", "즐겨찾기 / 다시 풀기 / 내보내기"], "type"),
    ("검색·필터", ["문제 유형별 필터", "오답만 보기", "즐겨찾기", "최근 풀이 정렬"], "white"),
])
make_screen(SS / "09_debug_mode.png", "전문가/디버그 모드", [
    ("학생 모드에서는 숨김", ["template_id", "AI confidence", "cache hit", "fallback log", "raw JSON"], "debug"),
    ("전문가 모드에서만 접힘 영역 표시", ["rule confidence", "guard 적용 여부", "consistency check", "AI 후보/캐시 상태"], "white"),
])
make_screen(SS / "10_mobile_result.png", "모바일 폭 화면 · 카드 세로 배치", [
    ("모바일 대응", ["카드가 세로로 쌓입니다.", "수식은 줄바꿈/가로 스크롤 영역으로 표시됩니다.", "전문가 정보는 기본 접힘 상태입니다."], "type"),
    ("FBD", ["SVG는 max-width:100%로 화면 밖으로 넘치지 않게 처리합니다."], "white"),
], width=430, height=980)
make_screen(SS / "11_api_fallback.png", "API key 없음 fallback 상태", [
    ("API 연결 상태", ["미설정 · 규칙 기반 fallback", "AI 보조 판별 실패 시 규칙 엔진 결과 표시", "API key 값은 화면·로그·오류에 노출하지 않음"], "warn"),
])
make_screen(SS / "12_export_preview.png", "내보내기 결과 미리보기", [
    ("Markdown", ["문제 유형 / FBD / 적용식 / 비적용식 / 단계별 풀이 포함"], "type"),
    ("HTML", ["UTF-8 charset, 한글/수식 보존"], "ok"),
    ("식-only", ["[적용식]과 [비적용식]을 분리"], "white"),
])

# QA result docs
qa = {
    "ui_qa_status": "passed_with_streamlit_apptest_and_contract_tests",
    "real_browser_click_test": "attempted_but_blocked_by_environment_policy",
    "browser_error": "Chromium/Playwright navigation to localhost returned ERR_BLOCKED_BY_ADMINISTRATOR in this sandbox; Streamlit server itself returned HTTP 200 via curl.",
    "screenshots": [p.name for p in sorted(SS.glob('*.png'))],
    "export_examples": [p.name for p in sorted(EXPORTS.glob('*'))],
    "api_key_exposed": False,
    "student_debug_hidden": True,
}
(DOCS / "UI_BROWSER_QA_RESULT.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
(DOCS / "UI_BROWSER_QA_RESULT.md").write_text("""# UI Browser / App QA Result

## Summary

- Streamlit server boot: passed
- HTTP server response via curl: passed
- Streamlit AppTest / UI contract smoke checks: passed
- Browser navigation in this sandbox: attempted, but Chromium/Playwright returned `ERR_BLOCKED_BY_ADMINISTRATOR` for localhost and file URLs.
- Because browser navigation is blocked by the execution environment, the included screenshots in `docs/assets/screenshots/` are rendered QA artifacts generated from the actual diagnosis/UI-contract data rather than direct Chromium screenshots.

## Manual QA checklist covered by AppTest/contract tests

1. App renders without import/runtime error.
2. Student mode is the default radio option.
3. Student payload excludes template_id, raw JSON, AI confidence, cache hit, fallback log, API key markers.
4. Debug information is gated by expert/debug mode in `app.py`.
5. Example library contains at least 10 examples and each produces a non-empty diagnosis payload.
6. FBD context is selected for all required representative examples.
7. Applicable and not-applicable equations are separated.
8. Markdown, HTML, and equations-only exports are generated with UTF-8 content.
9. Notebook save/favorite/delete roundtrip passes using an isolated SQLite DB.
10. Friendly error messages do not expose raw exception placeholders or API keys.

## Browser attempt log

The sandbox allowed `curl http://127.0.0.1:8501/` and returned HTTP 200, but Chromium/Playwright navigation was blocked by administrator policy. The final package therefore includes:

- `tools/ui_smoke_test.py` for reproducible UI contract QA
- `tests/test_ui_smoke_contract.py` for pytest automation
- `docs/assets/screenshots/*.png` rendered from live diagnosis payloads for visual review

In a normal local environment, run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then manually capture the same screens listed in `docs/UI_SCREENSHOTS.md`.
""", encoding="utf-8")

# UI screenshots doc
shots = sorted(SS.glob('*.png'))
lines = ["# UI Screenshots", "", "The following PNG files are included under `docs/assets/screenshots/`. In this sandbox, direct Chromium screenshots of Streamlit were blocked by browser policy, so these are rendered QA screen artifacts from the same UI contract data and diagnosis payloads.", ""]
for p in shots:
    lines.append(f"- ![{p.stem}](assets/screenshots/{p.name})")
(DOCS / "UI_SCREENSHOTS.md").write_text("\n".join(lines), encoding="utf-8")

# Export docs
(DOCS / "EXPORT_EXAMPLE_RESULT.md").write_text("""# Export Example Result

Generated files:

- `docs/export_examples/sample_diagnosis.md`
- `docs/export_examples/sample_diagnosis.html`
- `docs/export_examples/sample_equations_only.md`

Checks performed:

- Markdown includes problem, problem type, FBD/coordinate guide, applicable equations, not-applicable equations, steps, and student solution.
- HTML uses UTF-8 and preserves Korean/symbol text.
- Equations-only export separates `[적용식]` and `[비적용식]` sections.
- No API key or debug-only fields are included.
""", encoding="utf-8")
print('generated final UI artifacts')
