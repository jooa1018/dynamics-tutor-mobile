from __future__ import annotations

from pathlib import Path


def test_gitignore_excludes_private_runtime_data():
    text = Path(".gitignore").read_text(encoding="utf-8")
    for needle in ["data/*.sqlite3", "data/gpt_call_log.jsonl", "__pycache__", ".env"]:
        assert needle in text


def test_readme_mentions_beginner_safety_and_no_auto_answer():
    text = Path("README.md").read_text(encoding="utf-8")
    for needle in ["입문자 모드", "정보 부족", "자동 정답", "그림 정보를 텍스트", "개인 데이터"]:
        assert needle in text
