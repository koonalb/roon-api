import logging
from collections import OrderedDict

import pytest
from django.test import RequestFactory

from mock import patch
from rest_framework.permissions import AllowAny
from rest_framework.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from phi.core.views import api_root
from phi.core.view_exception_handler import view_exception_handling

handled_exception_text = 'text for handled exception'
unhandled_exception_text = 'text for unhandled exception'


def test_handled_exception(caplog):
    """Ensure exceptions are logged with traceback information"""
    try:
        raise Exception(handled_exception_text)
    except Exception as err:
        logging.getLogger('').exception(err)

        assert logging.getLevelName(logging.ERROR) in caplog.text
        assert handled_exception_text in caplog.text


@view_exception_handling()
@api_view(('GET',))
@permission_classes((AllowAny,))
def raise_unhandled_exception(*args, **kwargs):
    """Stub view handler function to simulate an unhandled exception"""
    raise Exception(unhandled_exception_text)


@pytest.mark.django_db
def test_unhandled_exception(client, user, caplog):
    """Ensure unhandled exceptions are logged and result in an http 500 response"""
    with patch('test_logger.api_root', new=raise_unhandled_exception):
        request = RequestFactory().get('/')
        response = api_root(request)

        assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        assert logging.getLevelName(logging.ERROR) in caplog.text
        assert unhandled_exception_text in caplog.text