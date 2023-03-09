"""Functional tests for logging configuration"""
import logging


def test_root_logger_stream():
    """Ensure root logger logs to stdout"""
    # stdout gets intercepted by pytest, so the logger stream handler changes.
    # Check that the logger is sending to 'console' since stdout is intercepted.
    assert 'console' in str(logging.getLogger().handlers[0].name)


def test_audit_logger_filename():
    """Ensure audit logger logs to audit log file"""
    # get output locations of the audit logger's handlers
    assert logging.getLogger('audit').handlers[0].baseFilename == '/tmp/audit.log'
