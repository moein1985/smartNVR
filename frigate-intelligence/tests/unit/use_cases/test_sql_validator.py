from frigate_intelligence.use_cases.text_to_sql.sql_validator import SQLValidator


def test_valid_select():
    ok, err = SQLValidator.validate("SELECT * FROM event")
    assert ok is True
    assert err is None


def test_drop_rejected():
    ok, err = SQLValidator.validate("DROP TABLE event")
    assert ok is False


def test_insert_rejected():
    ok, err = SQLValidator.validate("INSERT INTO event VALUES (1)")
    assert ok is False


def test_empty_rejected():
    ok, err = SQLValidator.validate("")
    assert ok is False


def test_no_table_rejected():
    ok, err = SQLValidator.validate("SELECT 1")
    assert ok is False


def test_select_with_drop_rejected():
    ok, err = SQLValidator.validate("SELECT * FROM event; DROP TABLE event")
    assert ok is False
    assert "Dangerous" in (err or "")


def test_pragma_rejected():
    ok, err = SQLValidator.validate("SELECT * FROM event; PRAGMA database_list")
    assert ok is False
