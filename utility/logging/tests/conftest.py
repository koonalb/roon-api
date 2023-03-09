"""Pytest conftest file for defining logging specific pytest fixtures"""
import logging
import sys

import pytest


@pytest.fixture
def log_info_record():
    """Pytest fixture that provides a log record object at the INFO level"""
    return logging.LogRecord('test', logging.INFO, 'test', 'test', 'test', {}, None)


@pytest.fixture
def log_error_record():
    """Pytest fixture that provides a log record object at the ERROR level"""
    return logging.LogRecord('test', logging.ERROR, 'test', 'test', 'test', {}, sys.exc_info())
