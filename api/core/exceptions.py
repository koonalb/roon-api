"""Custom exceptions for roon service"""
import json


class ServiceBaseException(Exception):
    """
    Base class for API exceptions
    """

    def __init__(self, content, *args, **kwargs):
        try:
            self.raw_message = json.loads(content) if content else {}
        except ValueError:
            self.raw_message = {"error_reason": content}
        self.status_code = kwargs.pop("status_code", None)

        # error reason is established by all services when raising errors
        # however, 3rd party libraries for auth use `detail` instead
        self.error_reason = self.raw_message.get("error_reason", None) or self.raw_message.get(
            "detail", self.raw_message
        )
        self.internal_code = self.raw_message.get("internal_code", None)
        super(ServiceBaseException, self).__init__(*args)


class InvalidCreateDataError(Exception):
    """Error if create data is invalid"""

    pass


class SearchWithOperatorException(Exception):
    """
    Error if failure in Advanced search
    """

    pass


class DateSearchError(Exception):
    """
    Invalid search parameters sent
    """

    pass


class ResourceAccessDeniedException(Exception):
    """
    Error if access is denied to an API resource
    """

    pass


class SourceTypeRequiredException(Exception):
    """
    Error if source_exception is not supplied
    """

    pass


class ConflictingParameterException(Exception):
    """
    Conflicting parameter error
    """

    pass


class MissingParameterException(Exception):
    """
    Missing parameter error
    """

    pass


class Service500FailureException(ServiceBaseException):
    """
    Error if call to the Service returns 500
    """

    pass


class Service400FailureException(ServiceBaseException):
    """
    Error if call to the Service returns 400
    """

    pass


class Service300FailureException(ServiceBaseException):
    """
    Error if call to the Service returns 300
    """

    pass


class ServiceDataFailureException(ServiceBaseException):
    """
    Error if call to the API does not return any data on a 200 status code
    """

    pass


class HTTP409ResponseException(Exception):
    """
    Error for 409 Conflict
    """

    pass


class HTTP400ResponseException(Exception):
    """
    Error for 400 Bad Request
    """

    pass


class HTTP412ResponseException(Exception):
    """
    Error for 412 Bad Request
    """

    pass
