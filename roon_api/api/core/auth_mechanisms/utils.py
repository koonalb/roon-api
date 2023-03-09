"""
Override to JWT Token Auth to send requests to the Auth Microservice
"""
import logging

import requests
from django.conf import settings
from django.http import HttpRequest
from rest_framework import exceptions
from rest_framework.request import Request
from rest_framework_jwt.settings import api_settings

# Setup logger
LOGGER = logging.getLogger("roon")

jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_auth_url = settings.HF_AUTH_SERVICE_URL


def verify_token_and_get_user(token, decoded_payload, headers):
    """
    Verifies token with the Auth Microservice and returns the payload and nested users attrs.
    """

    data = {"token": token}
    headers.update(data)
    _handle_token_action(data, "verify", headers)

    return get_user_from_token(token)


def send_credentials_and_get_user(email, password, headers):
    """
    Obtains a token with the Auth Microservice and returns the payload and nested user attrs.
    """

    data = {"email": email, "password": password}
    token = _handle_token_action(data, "obtain", headers).get("token")

    return get_user_from_token(token)


def _handle_token_action(data, action, headers):
    """
    Handle verification and obtaining of tokens
    """

    endpoint = jwt_auth_url
    endpoint += "tokens/{}/".format(action)

    response = requests.post(endpoint, json=data, headers=get_http_headers(headers))
    if response.status_code != requests.codes.ok:
        LOGGER.error(response.content)
        raise exceptions.AuthenticationFailed(response.content)
    response_body = response.json()
    if "token" not in response_body:
        LOGGER.error("Bad token response.\n" + str(response_body))
        raise exceptions.AuthenticationFailed(response.content)

    return response_body


def get_http_headers(og_headers):
    """
    Get all request headers specified by request_sub_headers
    """

    request_sub_headers = ["HTTP_", "REMOTE_ADDR"]

    headers = {
        k.replace("HTTP_", "").replace("_", "-").title(): v
        for k, v in og_headers.items()
        if any(x in k for x in request_sub_headers)
    }

    # Accept:
    # This is removed by default, since we allow the downstream service decide what is allowed
    # If a request is coming from the browsable API, the response data that is returned from the downstream
    #   service is in html form and not in json.

    # Content-Length:
    # Remove Content-Length and let the python request library calculate that
    #   when sending to other services.

    # Content-Type:
    # Remove Content-Type and let the python request library set it
    #   when sending data to other services.

    # Host:
    # Remove Host and let the python request library set it
    #   when sending data to other services.
    for key in ["Accept", "Content-Length", "Content-Type", "Host"]:
        headers.pop(key, None)

    if "token" in og_headers:
        if isinstance(og_headers["token"], bytes):
            token = og_headers["token"].decode("utf-8")
        else:
            token = og_headers["token"]
        headers.update({"Authorization": "JWT " + token})

    return headers


def get_user_from_token(token):
    """
    Decode users from token
    """
    return jwt_decode_handler(token)["user"]


def add_token_user_into_request_user(token_user, service_user_model, created=True):
    """
    Adds attributes to the service users account
    from the one provided by the token users
    """
    for attr, attr_value in token_user.items():
        if not created and attr in ["user_id", "email"]:
            continue

        if attr == "groups":
            service_user_model.change_groups([group["name"] for group in token_user["groups"]])
        else:
            try:
                setattr(service_user_model, attr, attr_value)
            except:
                pass

    return service_user_model


def create_dummy_request(headers, user):
    """
    Creation of a dummy request object to be used with all emails

    NOTE: This is done for async celery tasks, since we cannot pickle
          a `request` object into the task signature
    """

    from phi.users.models import PHIUser

    assert isinstance(user, PHIUser)

    dummy_request = HttpRequest()
    dummy_request.META = headers

    request = Request(dummy_request)
    request.user = user

    return request
