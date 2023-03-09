"""
Decorators for uniform view-exception handling
"""

import logging
from functools import wraps

import requests
from django import db
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, FieldError, ValidationError, MultipleObjectsReturned
from django.core.paginator import PageNotAnInteger
from django.db.utils import Error, IntegrityError, DatabaseError, OperationalError
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from api.core.exceptions import (
    SearchWithOperatorException,
    ServiceBaseException,
    ResourceAccessDeniedException,
    DateSearchError,
    HTTP409ResponseException,
    MissingParameterException,
    HTTP400ResponseException,
    HTTP412ResponseException,
)
from api.core.models import error_constructor

LOGGER = logging.getLogger("roon")


def _build_rest_response(err_msg, status_code):
    """
    Helper function to build a Response object
    # TODO: Investigate why these exceptions need special Response
    #       attributes value set. why the following works
    #       when handling exceptions in view function but not in this decorator
    #
    # return Response(error_constructor(err_msg),
    #                status=status.HTTP_400_BAD_REQUEST)
    """

    # allow caller to construct their own error message structure
    if not isinstance(err_msg, dict) or "error_reason" not in err_msg.keys():
        err_msg = error_constructor(err_msg)

    response = Response(err_msg, content_type="application/json", status=status_code)
    response.accepted_renderer = JSONRenderer()
    response.accepted_media_type = "application/json"
    response.renderer_context = {}
    return response


def _extract_err(err):
    """
    Helper function to extract error message from exception
    """

    err_msg = getattr(err, "message", None)

    if err_msg:
        return err_msg

    err_str = str(err)
    if err_str:
        return err_str

    LOGGER.error("%s has empty str(err) and err.message", type(err))
    return "Missing exception message"


def _format_err_msg(err, prefix="Error"):
    """
    Helper function to  build out the error message
    """
    # ServiceBaseException builds a custom error message
    if isinstance(err, ServiceBaseException):
        return err.raw_message

    return prefix + ": [%s] %s" % (type(err), _extract_err(err))


def view_exception_handling(retry=0):
    """
    Decorator that consolidate handling of common view exceptions.

    Some exception handlers do not call logger because middleware already
    does logging for non 200 response
    """
    retry += 1

    def handling_decorator(func):
        """avoid lint error, sigh"""

        @wraps(func)
        def _handler(*args, **kwargs):
            """avoid lint error, sigh"""

            try:
                return func(*args, **kwargs)

            except ResourceAccessDeniedException as err:
                return _build_rest_response(_format_err_msg(err, "Access denied"), status.HTTP_403_FORBIDDEN)

            except MissingParameterException as err:
                return _build_rest_response(
                    _format_err_msg(err, "Missing parameters"), status.HTTP_428_PRECONDITION_REQUIRED
                )

            except FieldError as err:
                return _build_rest_response(_format_err_msg(err), status.HTTP_400_BAD_REQUEST)

            except DateSearchError as err:
                return _build_rest_response(_format_err_msg(err, "Date search error"), status.HTTP_400_BAD_REQUEST)

            except SearchWithOperatorException as err:
                return _build_rest_response(_format_err_msg(err, "Search error"), status.HTTP_400_BAD_REQUEST)

            except HTTP400ResponseException as err:
                return _build_rest_response(_format_err_msg(err, "Bad Request"), status.HTTP_400_BAD_REQUEST)

            except HTTP409ResponseException as err:
                return _build_rest_response(_format_err_msg(err, "Conflict"), status.HTTP_409_CONFLICT)

            except HTTP412ResponseException as err:
                return _build_rest_response(
                    _format_err_msg(err, "Precondition failed"), status.HTTP_412_PRECONDITION_FAILED
                )

            except (
                TypeError,
                ValueError,
                AttributeError,
                PageNotAnInteger,
                ValidationError,
                MultipleObjectsReturned,
            ) as err:
                return _build_rest_response(
                    _format_err_msg(err, "Invalid parameters or data"), status.HTTP_400_BAD_REQUEST
                )

            # Make sure IntegrityError is above Database Errors as that is the parent exception
            except (IntegrityError,) as err:
                return _build_rest_response(_format_err_msg(err, "Integrity error"), status.HTTP_409_CONFLICT)

            # Make sure OperationalError is above Database Errors as that is the parent exception
            # Re-classifying OperationalErrors as 500, so that upstream services can retry
            # This operation will retry MAX_RETRIES times and reestablish the DB connection each time
            except (OperationalError,) as err:
                retry_message = f"RETRY[{retry}/{settings.MAX_RETRIES}] MySQL server DB issue"
                LOGGER.error(_format_err_msg(err, retry_message))
                while retry < settings.MAX_RETRIES:
                    db.connections.close_all()
                    handler = view_exception_handling(retry)(func)
                    return handler(*args, **kwargs)
                return _build_rest_response(
                    "Server Error, contact Roon to resolve", status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # All Database related errors land here
            except (Error, DatabaseError) as err:
                return _build_rest_response(_format_err_msg(err, "Database error"), status.HTTP_400_BAD_REQUEST)

            except ServiceBaseException as err:
                return _build_rest_response(_format_err_msg(err, "Downstream service error"), err.status_code)

            except ObjectDoesNotExist as err:
                return _build_rest_response(_format_err_msg(err, "Resource not found"), status.HTTP_404_NOT_FOUND)

            except (requests.ConnectionError, requests.ConnectTimeout) as err:
                err_msg = _format_err_msg(err, "Downstream service connection error")
                LOGGER.critical(err_msg)
                return _build_rest_response(err_msg, status.HTTP_500_INTERNAL_SERVER_ERROR)

            except Exception as err:
                LOGGER.exception(_format_err_msg(err, "Unhandled API exception:[%s] %s "))
                return _build_rest_response(
                    "Server Error, contact Roon to resolve", status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return _handler

    return handling_decorator
