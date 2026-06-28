from __future__ import annotations

import csv
import hashlib
import hmac
import io
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping

MISTAKE_REASON_OPTIONS = [
    "FBD 오류",
    "좌표축/부호 오류",
    "마찰 방향/마찰 조건 오류",
    "조건 누락",
    "금지식 사용",
    "단위 오류",
    "문제 유형 오판",
    "계산 실수",
    "개념 혼동",
    "힘 그림을 잘못 그림",
    "좌표축을 잘못 잡음",
    "마찰 방향을 잘못 판단함",
    "원운동에서 구심력 방향을 헷갈림",
    "에너지 보존 조건을 잘못 판단함",
    "운동량 보존 조건을 잘못 판단함",
    "각운동량 보존 조건을 잘못 판단함",
    "관성모멘트를 잘못 사용함",
    "공식은 맞았지만 계산 실수함",
    "문제 조건을 잘못 읽음",
    "기타",
]

REVIEW_INTERVAL_OPTIONS = {
    "오늘": 0,
    "1일 후": 1,
    "3일 후": 3,
    "7일 후": 7,
    "직접 표시 안 함": -1,
}

MOBILE_TABS = ["문제 분석", "오답노트", "복습", "설정"]


def load_env_file(path: str | Path = ".env") -> None:
    """Load a small .env file without requiring python-dotenv.

    Existing environment variables win. This keeps local/mobile deployment simple and
    avoids printing secrets anywhere.
    """
    p = Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_secret(name: str, default: str = "") -> str:
    """Read a secret from environment first, then Streamlit secrets when available."""
    value = os.getenv(name, "")
    if value:
        return value
    try:
        import streamlit as st  # imported lazily so tests can run without Streamlit context

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return default


def get_app_password() -> str:
    return get_secret("APP_PASSWORD", "")


def password_configured() -> bool:
    return bool(get_app_password().strip())


def check_password(candidate: str) -> bool:
    expected = get_app_password().strip()
    if not expected:
        return True
    return hmac.compare_digest(candidate or "", expected)


def secret_status_label(name: str) -> str:
    return "설정됨" if bool(get_secret(name, "").strip()) else "미설정"


def review_due_date(label: str) -> str:
    days = REVIEW_INTERVAL_OPTIONS.get(label, -1)
    if days < 0:
        return ""
    return (date.today() + timedelta(days=days)).isoformat()


def today_iso() -> str:
    return date.today().isoformat()


def is_due(record: Mapping[str, Any], today: str | None = None) -> bool:
    due = str(record.get("review_due_at") or "").strip()
    if not due:
        return False
    return due <= (today or today_iso())


def stable_input_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def records_to_csv(records: Iterable[Mapping[str, Any]]) -> str:
    buf = io.StringIO()
    fieldnames = [
        "id",
        "created_at",
        "updated_at",
        "problem_type",
        "problem",
        "solution",
        "memo",
        "difficulty",
        "wrong_reasons",
        "favorite",
        "needs_review",
        "review_due_at",
    ]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in records:
        writer.writerow(
            {
                "id": r.get("id", ""),
                "created_at": r.get("created_at", ""),
                "updated_at": r.get("updated_at", ""),
                "problem_type": r.get("problem_type") or r.get("recommended", ""),
                "problem": r.get("problem", ""),
                "solution": r.get("solution", ""),
                "memo": r.get("memo", ""),
                "difficulty": r.get("difficulty", ""),
                "wrong_reasons": "; ".join(r.get("wrong_reasons", []) or []),
                "favorite": bool(r.get("favorite")),
                "needs_review": bool(r.get("needs_review")),
                "review_due_at": r.get("review_due_at", ""),
            }
        )
    return buf.getvalue()


def public_settings_status() -> dict[str, str]:
    storage = "PostgreSQL/Supabase" if os.getenv("DATABASE_URL", "").strip() else "SQLite 로컬 저장소"
    return {
        "앱 비밀번호": "사용 중" if password_configured() else "미설정",
        "OpenAI API": secret_status_label("OPENAI_API_KEY"),
        "저장소": storage,
        "규칙 기반 분석": "사용 가능",
        "GPT 사용량 보호": "켜짐",
    }


def redact_secrets(text: str) -> str:
    for name in ["OPENAI_API_KEY", "APP_PASSWORD", "SUPABASE_SERVICE_KEY", "DATABASE_URL"]:
        value = get_secret(name, "")
        if value:
            text = text.replace(value, "[REDACTED]")
    return text

# ---------------------------------------------------------------------------
# Beginner review scheduling and difficulty heuristics
# ---------------------------------------------------------------------------

def review_due_by_miss_count(miss_count: int, still_unclear: bool = False) -> str:
    """Spaced-review rule for beginner wrong-note review."""
    if still_unclear:
        days = 1
    elif miss_count <= 1:
        days = 1
    elif miss_count == 2:
        days = 3
    elif miss_count == 3:
        days = 7
    else:
        days = 14
    return (date.today() + timedelta(days=days)).isoformat()


def classify_problem_difficulty(problem: str, problem_type: str = "") -> tuple[str, str]:
    text = f"{problem} {problem_type}".lower()
    score = 1
    reasons: list[str] = []
    if any(x in text for x in ["two", "두 ", "블록", "block a", "block b", "pulley", "도르래", "매달"]):
        score = max(score, 2)
        reasons.append("두 물체 또는 구속조건을 분리해 연립방정식을 세워야 합니다.")
    if any(x in text for x in ["friction", "마찰", "incline", "경사", "curve", "커브", "원운동", "circle"]):
        score = max(score, 3)
        reasons.append("마찰, 경사면, 원운동 조건을 함께 확인해야 합니다.")
    if any(x in text for x in ["rolling", "구름", "회전", "collision", "충돌", "projectile", "탄환", "관성모멘트", "i_g"]):
        score = max(score, 4)
        reasons.append("회전, 구름, 충돌 또는 관성모멘트가 포함됩니다.")
    if sum(1 for x in ["마찰", "friction", "rolling", "curve", "pulley", "collision", "energy", "원운동", "회전"] if x in text) >= 3:
        score = max(score, 5)
        reasons.append("여러 개념이 결합된 복합 시스템입니다.")
    return f"Level {score}", reasons[0] if reasons else "단일 물체 또는 단일 공식 중심의 기본 문제입니다."
