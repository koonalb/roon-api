"""Unit Tests for RequestLogFilter"""
import json

import pytest
from django.conf import settings
from django.http import (
    QueryDict,
    RawPostDataException,
    HttpRequest # pylint: disable=W0611
)
from django.test import RequestFactory
from mock import (
    patch,
    PropertyMock
)
from rest_framework import status

from phi.core.data_anonymizer import DataAnonymizer
from utility.logging.filters import RequestLogFilter


def test_set_record_defaults(log_info_record):
    """Ensure RequestLogFilter sets expected log record attribute defaults"""
    log_filter = RequestLogFilter()
    log_filter.set_record_defaults(log_info_record)

    # Check that all the expected fields exist on the record after calling set_record_defaults
    for field in RequestLogFilter.get_fields():
        if 'dd.' in field and settings.ENABLE_DATADOG_TRACING:
            continue
        if isinstance(field, str) and field != 'message':
            assert hasattr(log_info_record, field)
        elif isinstance(field, tuple):
            assert hasattr(log_info_record, field[0])


def test_filter_request(log_info_record, mock_request, dummy_string):
    """Ensure RequestLogFilter filter method attaches expected attributes to the log record for requests"""
    log_filter = RequestLogFilter()
    log_filter.request = mock_request
    log_filter.filter(log_info_record)

    # Check expected request fields are set
    assert log_info_record.region is not None
    assert log_info_record.host is not None
    assert log_info_record.trace == dummy_string
    assert log_info_record.src_ip == mock_request.META['HTTP_X_FORWARDED_FOR']
    assert log_info_record.http_method == mock_request.method
    assert log_info_record.endpoint == mock_request.path
    assert log_info_record.user == mock_request.requester
    assert log_info_record.agent == mock_request.META['HTTP_USER_AGENT']
    assert log_info_record.version == mock_request.version
    assert log_info_record.object == ''
    assert log_info_record.action == 'root'
    assert log_info_record.parameters == {}

    # Check expected response fields are not set
    for attr in ['http_status', 'duration', 'status', 'response']:
        assert getattr(log_info_record, attr) is None


def test_filter_no_user_agent(log_info_record, mock_request):
    """Ensure RequestLogFilter filter method functions when no user agent is present in request"""
    del mock_request.META['HTTP_USER_AGENT']
    log_filter = RequestLogFilter()
    log_filter.request = mock_request
    log_filter.filter(log_info_record)


@pytest.mark.jira_test_id('HF-24825')
def test_filter_response_success(log_info_record, mock_request, mock_response):
    """Ensure RequestLogFilter filter method attaches expected attributes to the log record for successful responses"""
    log_filter = RequestLogFilter()
    log_filter.request = mock_request
    log_filter.response = mock_response

    for code in range(100, 512):
        if status.is_success(code) or status.is_redirect(code):
            mock_response.status_code = code
            log_filter.filter(log_info_record)
            assert log_info_record.http_status == mock_response.status_code
            assert log_info_record.duration == mock_response.duration
            assert log_info_record.status == 'Success'
            assert not log_info_record.response


@pytest.mark.jira_test_id('HF-24829')
def test_filter_response_failure(monkeypatch, log_error_record, mock_request, mock_response, dummy_string):
    """Ensure RequestLogFilter filter method attaches expected attributes to the log record for failure responses"""
    log_filter = RequestLogFilter()
    log_filter.request = mock_request
    log_filter.response = mock_response

    for code in range(100, 512):
        if not status.is_success(code) and not status.is_redirect(code):
            mock_response.status_code = code
            log_filter.filter(log_error_record)
            assert log_error_record.http_status == mock_response.status_code
            assert log_error_record.duration == mock_response.duration
            assert log_error_record.status == 'Fail'
            assert log_error_record.response


def test_sanitize_parameters(mock_request, dummy_string):
    """Ensure RequestLogFilter sanitizes GET and POST parameters correctly"""
    mock_request.method = 'GET'
    mock_request.GET = QueryDict({})

    # Check empty GET parameters behave correctly
    assert RequestLogFilter.sanitize_parameters(mock_request) == {}

    mock_request.method = 'POST'
    mock_request.content_type = 'application/json'
    mock_request.body = "{}"

    # Check empty POST parameters behave correctly
    assert RequestLogFilter.sanitize_parameters(mock_request) == {}

    anon_string = DataAnonymizer.ANONYMIZE_STRING
    raw = {
        'non_phi_field': dummy_string,
        'phi__patient_first_name': dummy_string,
        'password': dummy_string
    }

    mock_request.method = 'GET'
    query_string = "non_phi_field=%s&phi__patient_first_name=%s&password=%s" \
                   % (dummy_string, dummy_string, dummy_string)
    mock_request.GET = QueryDict(query_string)
    anonymized_get = {
        'non_phi_field': [dummy_string],
        'phi__patient_first_name': anon_string,
        'password': anon_string,
    }

    # Check GET parameters are sanitized
    assert RequestLogFilter.sanitize_parameters(mock_request) == anonymized_get

    mock_request.method = 'POST'
    mock_request.body = json.dumps(raw)
    anonymized_post = {
        'non_phi_field': dummy_string,
        'phi__patient_first_name': anon_string,
        'password': anon_string,
    }

    # Check POST parameters are sanitized
    assert RequestLogFilter.sanitize_parameters(mock_request) == anonymized_post

    mock_request.method = 'GET'
    query_string = "non_phi_field=%s&message=%s&accession_number=%s" \
                   % (dummy_string, dummy_string, dummy_string)
    mock_request.GET = QueryDict(query_string)
    anonymized_get = {
        'non_phi_field': [dummy_string],
        'message': anon_string,
        'accession_number': anon_string,
    }

    # Check HL7Message GET parameters are sanitized
    assert RequestLogFilter.sanitize_parameters(mock_request) == anonymized_get

    mock_request.method = 'POST'
    raw = {
        'non_phi_field': dummy_string,
        'placer_order_id': dummy_string,
        'destination_id': dummy_string
    }
    mock_request.body = json.dumps(raw)
    anonymized_post = {
        'non_phi_field': dummy_string,
        'placer_order_id': anon_string,
        'destination_id': dummy_string,
    }

    # Check HL7Message POST parameters are sanitized
    assert RequestLogFilter.sanitize_parameters(mock_request) == anonymized_post


def test_sanitize_invalid_params(mock_request):
    """Ensure RequestLogFilter handles POST parameters with invalid data"""
    mock_request.method = 'POST'
    mock_request.content_type = 'application/json'
    mock_request.body = "{'test: bad json"

    # Check invalid json POST is handled correctly
    assert RequestLogFilter.sanitize_parameters(mock_request) == {'body': mock_request.body}


def test_sanitize_unknown_params(mock_request):
    """Ensure RequestLogFilter handles POST parameters with invalid data"""
    mock_request.method = 'POST'
    mock_request.content_type = 'text/html'
    mock_request.body = "input data"

    # Check invalid json POST is handled correctly
    assert RequestLogFilter.sanitize_parameters(mock_request) == {'body': mock_request.body}


def test_sanitize_oversized_params():
    """Ensure RequestLogFilter handles POST parameters with data that is too large"""
    request = RequestFactory().post('/', content_type='application/json')
    request.META['CONTENT_LENGTH'] = settings.DATA_UPLOAD_MAX_MEMORY_SIZE + 1

    # Check invalid json POST is handled correctly
    assert RequestLogFilter.sanitize_parameters(request) == {
        'body': 'Request body exceeded %s bytes '
                '(settings.DATA_UPLOAD_MAX_MEMORY_SIZE)' % settings.DATA_UPLOAD_MAX_MEMORY_SIZE
    }


def test_sanitize_unreadable_params():
    """Ensure unreadable post bodies are handled correctly"""
    with patch('test_filters.HttpRequest.body', new_callable=PropertyMock) as mock_request_body:
        mock_request_body.side_effect = IOError()
        request = RequestFactory().post('/', content_type='application/json')

        # Check invalid json POST is handled correctly
        assert RequestLogFilter.sanitize_parameters(request) == {
            'body': 'Unreadable POST body'
        }


def test_sanitize_post_body_exc():
    """Ensure RawPostDataException are handled correctly"""
    with patch('test_filters.HttpRequest.body', new_callable=PropertyMock) as mock_request_body:
        mock_request_body.side_effect = RawPostDataException()
        request = RequestFactory().post('/', content_type='multipart/form-data')

        # Check invalid json POST is handled correctly
        assert RequestLogFilter.sanitize_parameters(request) == {
            'body': 'Unreadable POST body'
        }
