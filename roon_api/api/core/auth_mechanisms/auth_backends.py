"""
Override ALL auth mechanisms (JWT, Session and Basic) to send requests to the Auth Microservice

"""
import base64
import binascii
import json
import logging

import requests
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.forms import forms
from rest_framework import exceptions, HTTP_HEADER_ENCODING
from rest_framework.authentication import get_authorization_header
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.settings import api_settings

from api.core.auth_mechanisms.utils import (
    verify_token_and_get_user,
    add_token_user_into_request_user,
    send_credentials_and_get_user,
)
from api.core.exceptions import Service500FailureException, Service400FailureException
from api.services.utils import get_from_service
from api.users.models import PHIUser

# Setup logger
LOGGER = logging.getLogger("roon")

JWT_DECODE_HANDLER = api_settings.JWT_DECODE_HANDLER
JWT_GET_USERNAME_FROM_PAYLOAD = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER
JWT_AUTH_URL = settings.HF_AUTH_SERVICE_URL


class RemoteMicroserviceAuthentication(ModelBackend):
    """
    Auth Microservice authentication for Session and Basic

    NOTE: Only used when logging into the API directly (Admin pages)
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate with Auth Microservice when using email and password

        Admin prompt, Rest Framework prompt, and Basic auth
        """

        if not all((username, password)):
            return None
        try:
            # Will raise errors if auth fails
            headers = {}
            if request:
                headers = request.META
            token_user = send_credentials_and_get_user(username, password, headers)

            # Add attrs from token users to the service users
            return self.get_or_create_user(token_user=token_user)

        except exceptions.AuthenticationFailed as err:
            message = json.loads(err.detail)
            message = message.get("error_reason") or message
            raise forms.ValidationError("Sorry, that login was invalid. Reason: %s" % message)
        except (requests.ConnectionError, requests.ConnectTimeout, Service500FailureException) as err:
            message = "Sorry, the Auth Service seems to be unavailable. " "Check in with DevOps!"
            LOGGER.critical(message + " Reason: {}".format(err))
            raise forms.ValidationError(message)

    def get_user(self, user_id):
        """
        This method is used for session auth

        Note: Do Not Change user_id
        """

        try:
            user = PHIUser.objects.get(user_id=str(user_id))

        except PHIUser.DoesNotExist:
            message = "The following user could not be found: %s. " "Retrieving user from Auth Service." % user_id
            LOGGER.info(message)
            user = self.get_or_create_user(user_id=user_id)

        return user

    @staticmethod
    def get_or_create_user(user_id=None, token_user=None):
        """
        To get and create a user from Auth Service
        """

        try:
            if token_user is None:
                assert user_id, "Must supply user_id"

                service_endpoint = JWT_AUTH_URL + "users/info/" + str(user_id)
                token_user = get_from_service(service_endpoint, None, sudo=True).json_data

            if not token_user:
                raise PHIUser.DoesNotExist()

            get_params = {"user_id": token_user["user_id"]}
            creation_params = {"email": token_user["email"]}
            creation_params.update(get_params)

            user, created = PHIUser.objects.get_or_create(defaults=creation_params, **get_params)
            return add_token_user_into_request_user(token_user, user, created=created)

        except (PHIUser.DoesNotExist, Service400FailureException, AssertionError) as err:
            err = getattr(err, "raw_message", err)
            message = "The following user could not be found: %s" % user_id
            LOGGER.critical(message + " Reason: {}".format(err))
            raise forms.ValidationError(message)


class BasicRemoteMicroserviceAuthentication(RemoteMicroserviceAuthentication):
    """
    Handles HTTP Basic auth to api by authenticating credentials against authentication service
    """

    def authenticate(self, request, **kwargs):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != b"basic":
            return None

        username, password = self.parse_credentials(auth)
        user = super().authenticate(request, username=username, password=password)
        return user, auth

    @staticmethod
    def parse_credentials(auth):
        """
        This method was lifted from rest_framework/authentication/BasicAuthentication.authenticate()
        to handle parsing out user credentials from HTTP Basic authentication
        """
        if len(auth) == 1:
            msg = "Invalid basic header. No credentials provided."
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = "Invalid basic header. Credentials string should not contain spaces."
            raise exceptions.AuthenticationFailed(msg)

        try:
            auth_parts = base64.b64decode(auth[1]).decode(HTTP_HEADER_ENCODING).partition(":")
        except (TypeError, UnicodeDecodeError, binascii.Error):
            msg = "Invalid basic header. Credentials not correctly base64 encoded."
            raise exceptions.AuthenticationFailed(msg)

        return auth_parts[0], auth_parts[2]


class RoonJSONWebTokenAuthentication(JSONWebTokenAuthentication):
    """
    Token based authentication using the JSON Web Token standard.

    Extended to contact Auth service instead of local authentication

    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string specified in the setting
    `JWT_AUTH_HEADER_PREFIX`. For example:

        Authorization: JWT eyJhbGciOiAiSFMyNTYiLCAidHlwIj
    """

    def __init__(self, *args, **kwargs):
        self.retrieved_token = None
        super().__init__(*args, **kwargs)

    def authenticate(self, request):
        """
        Returns a two-tuple of `User` and token if a valid signature has been
        supplied using JWT-based authentication.  Otherwise returns `None`.
        """

        self.retrieved_token = self.get_jwt_value(request)
        self._request = request

        return super().authenticate(request)

    def authenticate_credentials(self, payload):
        """
        Returns an active users that matches the payload's user_id and email.
        """

        try:
            token_user = verify_token_and_get_user(self.retrieved_token, payload, self._request.META)

            # Add attrs from token users to the service users
            return RemoteMicroserviceAuthentication.get_or_create_user(token_user=token_user)

        except (requests.ConnectionError, requests.ConnectTimeout, Service500FailureException) as err:
            message = "Sorry, the Auth Service seems to be unavailable. " "Check in with DevOps!"
            LOGGER.critical(message + " Reason: {}".format(err))
            raise forms.ValidationError(message)
