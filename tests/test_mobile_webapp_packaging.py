from __future__ import annotations

from pathlib import Path

from dynamics_core.mobile_support import (
    MISTAKE_REASON_OPTIONS,
    MOBILE_TABS,
    check_password,
    load_env_file,
    records_to_csv,
    review_due_date,
)
from dynamics_core.storage import (
    export_records_csv,
    list_records,
    save_record,
    storage_backend,
    update_record,
)


def test_mobile_tabs_and_mistake_reasons_defined():
    assert MOBILE_TABS == ["문제 분석", "오답노트", "복습", "설정"]
    assert "힘 그림을 잘못 그림" in MISTAKE_REASON_OPTIONS
    assert "각운동량 보존 조건을 잘못 판단함" in MISTAKE_REASON_OPTIONS


def test_env_password_loader_and_checker(tmp_path, monkeypatch):
    monkeypatch.delenv("APP_PASSWORD", raising=False)
    env = tmp_path / ".env"
    env.write_text("APP_PASSWORD=secret123\nOPENAI_API_KEY=not-shown\n", encoding="utf-8")
    load_env_file(env)
    assert check_password("secret123") is True
    assert check_password("wrong") is False


def test_review_due_date_outputs_iso_or_blank():
    assert review_due_date("직접 표시 안 함") == ""
    assert len(review_due_date("3일 후")) == 10


def test_storage_extended_fields_csv_update_roundtrip(tmp_path):
    db = tmp_path / "records.sqlite3"
    rid = save_record(
        {
            "problem": "A block on a smooth horizontal plane is connected to a hanging block over a pulley.",
            "solution": "T = ma",
            "goal": "가속도",
            "recommended": "수평면 블록-도르래",
            "confidence": "0.9",
            "problem_type": "마찰 없는 수평면 블록-도르래",
            "blueprint_equations": ["f = 0", "T = m_A a", "m_B g - T = m_B a"],
            "not_applicable_equations": ["f = μN_A 적용 금지"],
            "wrong_reasons": ["마찰 방향을 잘못 판단함"],
            "difficulty": "보통",
            "review_due_at": "2099-01-01",
            "needs_review": True,
            "favorite": False,
        },
        path=db,
    )
    update_record(rid, {"favorite": True, "wrong_reasons": ["문제 조건을 잘못 읽음"], "difficulty": "어려움"}, path=db)
    records = list_records(path=db)
    assert records[0]["favorite"] is True
    assert records[0]["difficulty"] == "어려움"
    assert records[0]["wrong_reasons"] == ["문제 조건을 잘못 읽음"]
    csv_text = export_records_csv(path=db)
    assert "problem_type" in csv_text
    assert "문제 조건을 잘못 읽음" in csv_text


def test_records_to_csv_has_mobile_backup_columns():
    csv_text = records_to_csv([
        {"id": 1, "problem": "p", "wrong_reasons": ["기타"], "review_due_at": "2099-01-01", "favorite": True}
    ])
    for header in ["wrong_reasons", "review_due_at", "favorite", "problem"]:
        assert header in csv_text


def test_readme_and_deployment_docs_exist():
    root = Path.cwd()
    for rel in [
        "README.md",
        "docs/DEPLOYMENT.md",
        "docs/REDEPLOYMENT.md",
        "docs/DATABASE_BACKUP_RESTORE.md",
        "docs/MOBILE_HOME_SCREEN.md",
        "docs/OPERATING_COSTS.md",
        "docs/SUPABASE_SCHEMA.sql",
    ]:
        assert (root / rel).exists(), rel
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "개인용 모바일" in readme
    assert "APP_PASSWORD" in readme
    assert "DATABASE_URL" in readme


def test_mobile_support_misc_branches(tmp_path, monkeypatch):
    from dynamics_core.mobile_support import (
        get_secret,
        is_due,
        password_configured,
        public_settings_status,
        redact_secrets,
        stable_input_hash,
        today_iso,
    )

    missing = tmp_path / "missing.env"
    load_env_file(missing)
    monkeypatch.delenv("APP_PASSWORD", raising=False)
    assert password_configured() is False
    assert check_password("anything") is True
    assert get_secret("NO_SUCH_SECRET", "fallback") == "fallback"
    assert len(stable_input_hash("abc")) == 16
    assert is_due({"review_due_at": ""}) is False
    assert is_due({"review_due_at": "2000-01-01"}, today=today_iso()) is True
    monkeypatch.setenv("APP_PASSWORD", "super-secret")
    assert "[REDACTED]" in redact_secrets("pw=super-secret")
    status = public_settings_status()
    assert status["앱 비밀번호"] == "사용 중"


def test_storage_exports_clear_and_empty_update(tmp_path):
    from dynamics_core.storage import clear_records, export_records_json, export_records_markdown

    db = tmp_path / "records.sqlite3"
    rid = save_record(
        {
            "problem": "p",
            "solution": "s",
            "goal": "g",
            "recommended": "rec",
            "confidence": "0.8",
            "problem_type": "type",
            "blueprint_equations": ["eq1"],
            "not_applicable_equations": ["bad"],
            "missing": ["missing item"],
            "misconceptions": ["mis"],
            "memo": "memo",
            "review_due_at": "2099-01-01",
        },
        path=db,
    )
    update_record(rid, {"not_allowed": "ignored"}, path=db)
    md = export_records_markdown(path=db)
    js = export_records_json(path=db)
    assert "missing item" in md
    assert "복습 예정일" in md
    assert "memo" in md
    assert '"problem"' in js
    clear_records(path=db)
    assert list_records(path=db) == []


def test_storage_backend_database_url_without_psycopg_fallback(monkeypatch):
    from dynamics_core.storage import storage_backend

    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    assert storage_backend() in {"postgres", "sqlite_fallback_missing_psycopg"}
