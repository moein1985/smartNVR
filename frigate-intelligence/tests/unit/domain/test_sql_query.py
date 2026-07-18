from frigate_intelligence.domain.value_objects.sql_query import SQLQuery


def test_is_select_valid():
    q = SQLQuery("SELECT * FROM event")
    assert q.is_select is True


def test_is_select_invalid():
    q = SQLQuery("DROP TABLE event")
    assert q.is_select is False


def test_is_safe_valid():
    q = SQLQuery("SELECT * FROM event WHERE label = 'person'")
    assert q.is_safe is True


def test_is_safe_drop():
    q = SQLQuery("SELECT * FROM event; DROP TABLE event")
    assert q.is_safe is False


def test_normalized_strips_semicolon():
    q = SQLQuery("SELECT 1;")
    assert q.normalized == "SELECT 1"
