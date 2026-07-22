"""Tests for Phase 15.1: Logging configuration and SensitiveDataFilter."""
import logging
import tempfile
from pathlib import Path

from frigate_intelligence.infrastructure.logging_config import (
    SensitiveDataFilter,
    setup_logging,
)


def _close_handlers() -> None:
    root = logging.getLogger()
    for handler in list(root.handlers):
        handler.close()
        root.removeHandler(handler)


def test_sensitive_data_filter_redacts_sk_keys():
    """SensitiveDataFilter should redact OpenAI-style sk- keys."""
    filt = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Using API key sk-abc123def456ghi789jkl012mno345pqr678",
        args=None,
        exc_info=None,
    )
    assert filt.filter(record)
    assert "sk-abc123" not in str(record.getMessage())
    assert "[REDACTED]" in str(record.getMessage())


def test_sensitive_data_filter_redacts_avalai_keys():
    """SensitiveDataFilter should redact Avalai-style aa- keys."""
    filt = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Token: aa-9ZS4bj4RNfWF5v36MH4dXBETfya0p9aJxJOOFvF6TlJFXCss",
        args=None,
        exc_info=None,
    )
    assert filt.filter(record)
    assert "aa-9ZS4bj" not in str(record.getMessage())
    assert "[REDACTED]" in str(record.getMessage())


def test_sensitive_data_filter_redacts_telegram_tokens():
    """SensitiveDataFilter should redact Telegram bot tokens (digits:hash)."""
    filt = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Sending via bot 8167155080:AAHwD_2EIXJfwVAww9hmZ3a1_Fkn9yFRHO8",
        args=None,
        exc_info=None,
    )
    assert filt.filter(record)
    assert "AAHwD_2E" not in str(record.getMessage())
    assert "[REDACTED]" in str(record.getMessage())


def test_sensitive_data_filter_preserves_normal_messages():
    """SensitiveDataFilter should not alter messages without sensitive data."""
    filt = SensitiveDataFilter()
    original = "Scheduled report job every 24h"
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=original,
        args=None,
        exc_info=None,
    )
    assert filt.filter(record)
    assert str(record.getMessage()) == original


def test_setup_logging_creates_log_directory():
    """setup_logging should create the log directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = str(Path(tmpdir) / "logs")
        assert not Path(log_dir).exists()

        setup_logging(log_dir=log_dir, level="DEBUG")

        assert Path(log_dir).exists()
        assert Path(log_dir).is_dir()
        assert (Path(log_dir) / "app.log").exists()

        _close_handlers()


def test_setup_logging_writes_to_file():
    """setup_logging should route log messages to the file handler."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = str(Path(tmpdir) / "logs")
        setup_logging(log_dir=log_dir, level="DEBUG")

        test_logger = logging.getLogger("test_setup_logging_writes")
        test_logger.info("Test log message for file writing")

        log_file = Path(log_dir) / "app.log"
        content = log_file.read_text(encoding="utf-8")
        assert "Test log message for file writing" in content

        _close_handlers()


def test_setup_logging_respects_level():
    """setup_logging should not log messages below the configured level."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = str(Path(tmpdir) / "logs")
        setup_logging(log_dir=log_dir, level="WARNING")

        test_logger = logging.getLogger("test_setup_logging_level")
        test_logger.info("This INFO should not appear")
        test_logger.warning("This WARNING should appear")

        log_file = Path(log_dir) / "app.log"
        content = log_file.read_text(encoding="utf-8")
        assert "This INFO should not appear" not in content
        assert "This WARNING should appear" in content

        _close_handlers()


def test_setup_logging_redacts_in_file():
    """Log file should contain [REDACTED] instead of actual API keys."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = str(Path(tmpdir) / "logs")
        setup_logging(log_dir=log_dir, level="DEBUG")

        test_logger = logging.getLogger("test_redaction")
        test_logger.info("API key is sk-supersecretkey123456789abcdefghij")

        log_file = Path(log_dir) / "app.log"
        content = log_file.read_text(encoding="utf-8")
        assert "sk-supersecret" not in content
        assert "[REDACTED]" in content

        _close_handlers()
