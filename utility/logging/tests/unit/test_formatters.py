"""Unit tests for RequestLogFormatter"""
import json
from datetime import datetime

import pytest

from utility.logging.formatters import RequestLogFormatter


@pytest.mark.jira_test_id('HF-24824')
def test_format(log_info_record):
    """Ensure RequestLogFormatter format method returns valid json"""
    formatter = RequestLogFormatter()
    formatted = formatter.format(log_info_record)

    assert json.loads(formatted)


def test_format_time(log_info_record):
    """Ensure RequestLogFormatter formatTime method produces a string that datetime can parse"""
    formatter = RequestLogFormatter()
    datetime_string = formatter.formatTime(log_info_record)

    assert datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%S.%f')

    datetime_string = formatter.formatTime(log_info_record, '%Y-%m')

    assert datetime.strptime(datetime_string, '%Y-%m')
