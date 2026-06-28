from __future__ import annotations

import json
import re
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .mobile_support import records_to_csv

DEFAULT_DB_PATH = Path(os.getenv("DYNAMICS_SQLITE_PATH", "data/study_records.sqlite3"))

BASE_COLUMNS = {
    "problem_type": "TEXT",
    "applicable_json": "TEXT",
    "not_applicable_json": "TEXT",
    "mistake_tags_json": "TEXT",
    "extra_json": "TEXT",
    "favorite": "INTEGER DEFAULT 0",
    "difficulty": "TEXT",
    "wrong_reasons_json": "TEXT",
    "review_due_at": "TEXT",
    "needs_review": "INTEGER DEFAULT 0",
    "updated_at": "TEXT",
}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _database_url() -> str:
    return os.getenv("DATABASE_URL", "").strip()


def _can_use_postgres() -> bool:
    if not _database_url().startswith(("postgres://", "postgresql://")):
        return False
    try:
        import psycopg  # noqa: F401

        return True
    except Exception:
        return False


def storage_backend() -> str:
    if _database_url().startswith(("postgres://", "postgresql://")):
        return "postgres" if _can_use_postgres() else "sqlite_fallback_missing_psycopg"
    return "sqlite"


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_load(value: Any, default: Any) -> Any:
    try:
        if value in (None, ""):
            return default
        return json.loads(value)
    except Exception:
        return default


def init_db(path: Path = DEFAULT_DB_PATH) -> None:
    if storage_backend() == "postgres":  # pragma: no cover
        _init_postgres()
        return
    _init_sqlite(path)


def _init_sqlite(path: Path = DEFAULT_DB_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS study_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                problem TEXT NOT NULL,
                solution TEXT,
                goal TEXT,
                user_method TEXT,
                recommended TEXT,
                confidence TEXT,
                cues_json TEXT,
                missing_json TEXT,
                misconceptions_json TEXT,
                memo TEXT
            )
            """
        )
        existing = {row[1] for row in conn.execute("PRAGMA table_info(study_records)").fetchall()}
        for column, column_type in BASE_COLUMNS.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE study_records ADD COLUMN {column} {column_type}")
        conn.commit()


def _pg_connect():  # pragma: no cover
    import psycopg

    return psycopg.connect(_database_url())


def _init_postgres() -> None:  # pragma: no cover
    with _pg_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS study_records (
                    id BIGSERIAL PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    problem TEXT NOT NULL,
                    solution TEXT,
                    goal TEXT,
                    user_method TEXT,
                    recommended TEXT,
                    confidence TEXT,
                    cues_json TEXT,
                    missing_json TEXT,
                    misconceptions_json TEXT,
                    memo TEXT,
                    problem_type TEXT,
                    applicable_json TEXT,
                    not_applicable_json TEXT,
                    mistake_tags_json TEXT,
                    extra_json TEXT,
                    favorite INTEGER DEFAULT 0,
                    difficulty TEXT,
                    wrong_reasons_json TEXT,
                    review_due_at TEXT,
                    needs_review INTEGER DEFAULT 0
                )
                """
            )
        conn.commit()




def _auto_wrong_reasons_from_record(record: Dict[str, Any]) -> list[str]:
    text_parts = [
        record.get("problem", ""),
        record.get("problem_type", ""),
        "\n".join(record.get("not_applicable_equations", []) or []),
        "\n".join(record.get("missing", []) or []),
        "\n".join(record.get("misconceptions", []) or []),
        "\n".join(record.get("mistake_tags", []) or []),
    ]
    extra = record.get("extra", {}) or {}
    if isinstance(extra, dict):
        text_parts.append(str(extra.get("support_level", "")))
        text_parts.append(str(extra.get("markdown", "")))
    text = "\n".join(map(str, text_parts))
    rules = [
        (r"FBD|자유물체도|힘을 잘못|작용-반작용|물체 개수", "FBD 오류"),
        (r"좌표축|방향 설정|부호|\+|\-", "좌표축/부호 오류"),
        (r"마찰|μ|mu|friction|f\s*=", "마찰 방향/마찰 조건 오류"),
        (r"마찰 없음|no friction|frictionless|순수 구름|without slipping|no slip|조건 누락|정보 부족|추가 조건", "조건 누락"),
        (r"비적용식|사용 금지|사용 불가|적용 불가|v_G\s*=\s*ωR|a_G\s*=\s*αR|f\s*=\s*μ", "금지식 사용"),
        (r"단위|g =|km/h|cm|rpm|SI", "단위 오류"),
        (r"에너지|F=ma|운동량|각운동량|문제 유형|오판", "문제 유형 오판"),
        (r"계산 실수|계산", "계산 실수"),
        (r"장력|마찰력|수직항력|구심력|개념 혼동", "개념 혼동"),
        (r"원운동|최고점|최저점|바닥점|중심\s*방향|구심력", "원운동 방향 오류"),
        (r"각운동량|H_O|운동량|충돌", "운동량 보존 조건 착각"),
        (r"관성모멘트|I_G|ΣM|모멘트", "관성모멘트 사용 오류"),
    ]
    out: list[str] = []
    for pattern, tag in rules:
        if re.search(pattern, text, flags=re.I) and tag not in out:
            out.append(tag)
    return out[:5]

def _record_values(record: Dict[str, Any]) -> tuple[Any, ...]:
    now = _now()
    wrong_reasons = record.get("wrong_reasons", record.get("mistake_reasons", []))
    if not wrong_reasons:
        wrong_reasons = _auto_wrong_reasons_from_record(record)
    return (
        now,
        now,
        record.get("problem", ""),
        record.get("solution", ""),
        record.get("goal", ""),
        record.get("user_method", ""),
        record.get("recommended", ""),
        record.get("confidence", ""),
        _json_dump(record.get("cues", {})),
        _json_dump(record.get("missing", [])),
        _json_dump(record.get("misconceptions", [])),
        record.get("memo", ""),
        record.get("problem_type", ""),
        _json_dump(record.get("blueprint_equations", record.get("applicable_equations", []))),
        _json_dump(record.get("not_applicable_equations", [])),
        _json_dump(record.get("mistake_tags", [])),
        _json_dump(record.get("extra", {})),
        1 if record.get("favorite") else 0,
        record.get("difficulty", ""),
        _json_dump(wrong_reasons),
        record.get("review_due_at", ""),
        1 if record.get("needs_review") else 0,
    )


def save_record(record: Dict[str, Any], path: Path = DEFAULT_DB_PATH) -> int:
    init_db(path)
    values = _record_values(record)
    if storage_backend() == "postgres":  # pragma: no cover
        return _save_postgres(values)
    return _save_sqlite(values, path)


def _save_sqlite(values: tuple[Any, ...], path: Path = DEFAULT_DB_PATH) -> int:
    with sqlite3.connect(path) as conn:
        cur = conn.execute(
            """
            INSERT INTO study_records
            (created_at, updated_at, problem, solution, goal, user_method, recommended, confidence,
             cues_json, missing_json, misconceptions_json, memo, problem_type,
             applicable_json, not_applicable_json, mistake_tags_json, extra_json, favorite,
             difficulty, wrong_reasons_json, review_due_at, needs_review)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
        conn.commit()
        return int(cur.lastrowid)


def _save_postgres(values: tuple[Any, ...]) -> int:  # pragma: no cover
    with _pg_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO study_records
                (created_at, updated_at, problem, solution, goal, user_method, recommended, confidence,
                 cues_json, missing_json, misconceptions_json, memo, problem_type,
                 applicable_json, not_applicable_json, mistake_tags_json, extra_json, favorite,
                 difficulty, wrong_reasons_json, review_due_at, needs_review)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                values,
            )
            row = cur.fetchone()
        conn.commit()
    return int(row[0])


def _hydrate_row(row: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(row)
    item["cues"] = _json_load(item.get("cues_json"), {})
    item["missing"] = _json_load(item.get("missing_json"), [])
    item["misconceptions"] = _json_load(item.get("misconceptions_json"), [])
    item["applicable_equations"] = _json_load(item.get("applicable_json"), [])
    item["not_applicable_equations"] = _json_load(item.get("not_applicable_json"), [])
    item["mistake_tags"] = _json_load(item.get("mistake_tags_json"), [])
    item["wrong_reasons"] = _json_load(item.get("wrong_reasons_json"), [])
    item["extra"] = _json_load(item.get("extra_json"), {})
    item["favorite"] = bool(item.get("favorite"))
    item["needs_review"] = bool(item.get("needs_review"))
    return item


def list_records(path: Path = DEFAULT_DB_PATH, limit: int = 200) -> List[Dict[str, Any]]:
    init_db(path)
    if storage_backend() == "postgres":  # pragma: no cover
        with _pg_connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM study_records ORDER BY id DESC LIMIT %s", (limit,))
                cols = [d.name for d in cur.description]
                rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        return [_hydrate_row(r) for r in rows]
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM study_records ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [_hydrate_row(dict(r)) for r in rows]


def clear_records(path: Path = DEFAULT_DB_PATH) -> None:
    init_db(path)
    if storage_backend() == "postgres":  # pragma: no cover
        with _pg_connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM study_records")
            conn.commit()
        return
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM study_records")
        conn.commit()


def export_records_json(path: Path = DEFAULT_DB_PATH) -> str:
    return json.dumps(list_records(path, limit=10000), ensure_ascii=False, indent=2)


def export_records_csv(path: Path = DEFAULT_DB_PATH) -> str:
    return records_to_csv(list_records(path, limit=10000))


def export_records_markdown(path: Path = DEFAULT_DB_PATH) -> str:
    records = list_records(path, limit=10000)
    lines = ["# Dynamics Study Records", ""]
    for r in records:
        lines.extend([
            f"## {r.get('created_at', '')} · {r.get('problem_type') or r.get('recommended', '')}",
            "",
            f"**문제:** {r.get('problem', '')}",
            "",
            f"**난이도:** {r.get('difficulty') or '미지정'}",
            "",
            "**틀린 이유:** " + (", ".join(r.get("wrong_reasons", []) or []) or "기록 없음"),
            "",
            "**적용식:**",
        ])
        lines.extend([f"- {x}" for x in r.get("applicable_equations", [])] or ["- 기록 없음"])
        lines.extend(["", "**비적용식/주의:**"])
        lines.extend([f"- {x}" for x in r.get("not_applicable_equations", [])] or ["- 기록 없음"])
        if r.get("missing"):
            lines.extend(["", "**복습할 점:**"])
            lines.extend([f"- {x}" for x in r.get("missing", [])])
        if r.get("review_due_at"):
            lines.extend(["", f"**복습 예정일:** {r.get('review_due_at')}"])
        if r.get("memo"):
            lines.extend(["", f"**메모:** {r.get('memo')}"])
        lines.append("")
    return "\n".join(lines)


def delete_record(record_id: int, path: Path = DEFAULT_DB_PATH) -> None:
    init_db(path)
    if storage_backend() == "postgres":  # pragma: no cover
        with _pg_connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM study_records WHERE id = %s", (int(record_id),))
            conn.commit()
        return
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM study_records WHERE id = ?", (int(record_id),))
        conn.commit()


def set_favorite(record_id: int, favorite: bool, path: Path = DEFAULT_DB_PATH) -> None:
    init_db(path)
    if storage_backend() == "postgres":  # pragma: no cover
        with _pg_connect() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE study_records SET favorite = %s, updated_at = %s WHERE id = %s", (1 if favorite else 0, _now(), int(record_id)))
            conn.commit()
        return
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE study_records SET favorite = ?, updated_at = ? WHERE id = ?", (1 if favorite else 0, _now(), int(record_id)))
        conn.commit()


def update_record(record_id: int, updates: Dict[str, Any], path: Path = DEFAULT_DB_PATH) -> None:
    allowed = {"memo", "difficulty", "review_due_at", "needs_review", "favorite", "wrong_reasons_json"}
    values: Dict[str, Any] = {}
    for key, value in updates.items():
        if key == "wrong_reasons":
            values["wrong_reasons_json"] = _json_dump(value)
        elif key in allowed:
            if key in {"needs_review", "favorite"}:
                values[key] = 1 if value else 0
            else:
                values[key] = value
    if not values:
        return
    values["updated_at"] = _now()
    init_db(path)
    if storage_backend() == "postgres":  # pragma: no cover
        assignments = ", ".join(f"{k} = %s" for k in values)
        params = list(values.values()) + [int(record_id)]
        with _pg_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(f"UPDATE study_records SET {assignments} WHERE id = %s", params)
            conn.commit()
        return
    assignments = ", ".join(f"{k} = ?" for k in values)
    params = list(values.values()) + [int(record_id)]
    with sqlite3.connect(path) as conn:
        conn.execute(f"UPDATE study_records SET {assignments} WHERE id = ?", params)
        conn.commit()
