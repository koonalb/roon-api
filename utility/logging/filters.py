"""Defines RequestLogFilter"""
import json
import logging
import socket

import requests
from django.conf import settings
from django.core.exceptions import RequestDataTooBig
from django.http import QueryDict, RawPostDataException
from django.urls import resolve, Resolver404, NoReverseMatch
from rest_framework import status

from api.core.data_anonymizer import cleanse_data
from api.core.utils import extract_protocol_and_ip


class RequestLogFilter(logging.Filter):
    """Log filter for adding http request and http response derived attributes to log records"""

    _fields = [
        ("timestamp", "asctime"),
        "trace",
        "region",
        "host",
        "host_ip",
        "app",
        "version",
        "request_version",
        "action",
        "object",
        "src_ip",
        "user",
        "agent",
        "http_method",
        "endpoint",
        "parameters",
        "http_status",
        "status",
        "response",
        "duration",
        ("log_level", "levelname"),
        ("exception", "exc_text"),
        "message",
    ]
    metadata = None
    # local ec2 instance metadata url
    metadata_url = "http://169.254.169.254/latest/dynamic/instance-identity/document"

    def __init__(self):
        self.request = None
        self.response = None
        self.app = "Roon"
        self.version = None
        self.duration = None

        try:
            if self.metadata is None:
                self.metadata = requests.get(self.metadata_url, timeout=1).json()
            self.region = self.metadata["region"]
            self.host_ip = self.metadata["privateIp"]
            self.host = socket.gethostname()
        except (ValueError, KeyError, requests.ConnectionError, requests.ConnectTimeout):
            self.region = "Unknown"
            self.host_ip = self.host = socket.getfqdn()
        super(RequestLogFilter, self).__init__()

    @classmethod
    def get_fields(cls):
        """
        Returns _fields
        """
        return cls._fields

    def filter(self, record):
        self.app = settings.SERVICE_NAME
        self.set_record_defaults(record)

        if self.request is not None:
            record.trace = self.request.META.get("HTTP_X_REQUEST_ID", record.trace)
            record.version = getattr(self.request, "system_version", None)
            record.request_version = getattr(self.request, "version", None)
            record.http_method = self.request.method
            record.endpoint = self.request.path
            _, record.src_ip = extract_protocol_and_ip(self.request)
            record.user = getattr(self.request, "requester", None)
            if "HTTP_USER_AGENT" in self.request.META:
                record.agent = self.request.META["HTTP_USER_AGENT"]
            try:
                record.action = resolve(self.request.path).view_name
                record.object = resolve(self.request.path).app_name
            except (Resolver404, NoReverseMatch):
                record.action = "Unknown"
                record.object = "Unknown"
            record.parameters = self.sanitize_parameters(self.request)

        if self.response is not None:
            record.http_status = getattr(self.response, "status_code", "Unknown status")
            record.duration = getattr(self.response, "duration", record.duration)
            if not status.is_redirect(record.http_status) and not status.is_success(record.http_status):
                record.status = "Fail"
                try:
                    record.response = self.response.data
                except Exception:
                    pass
            else:
                record.status = "Success"

        return record

    def set_record_defaults(self, record):
        """Sets default values for all expected attributes"""
        record.timestamp = record.created
        record.trace = None
        record.region = self.region
        record.host = self.host
        record.host_ip = self.host_ip
        record.app = self.app
        record.version = self.version
        record.request_version = None
        record.action = None
        record.object = None
        record.src_ip = None
        record.user = None
        record.agent = None
        record.http_method = None
        record.endpoint = None
        record.parameters = None
        record.http_status = None
        record.status = None
        record.response = None
        record.duration = None
        record.exception = None
        record.log_level = record.levelno

    @staticmethod
    def sanitize_parameters(request):
        """
        helper method to extract request GET query parameter or POST data
        Method also deals with PHI and password obfuscation
        """
        from django.conf import settings

        parameters = {}
        if request.method == "GET":
            # parameters appear as lists since query parameters may have multiple values per key
            # request.GET is a QueryDict, QueryDict api changed in django 2
            parameters = dict(request.GET.lists())
        elif request.method == "POST":
            try:
                if request.content_type == "application/json":
                    parameters = json.loads(request.body)
                elif request.content_type == "application/x-www-form-urlencoded":
                    # form data is treated the same as query parameters, each key's value is a list
                    parameters = dict(QueryDict(request.body).lists())
                else:
                    parameters = {"body": request.body}
            except RequestDataTooBig:
                parameters = {
                    "body": (
                        "Request body exceeded %s bytes (settings.DATA_UPLOAD_MAX_MEMORY_SIZE)"
                        % settings.DATA_UPLOAD_MAX_MEMORY_SIZE
                    )
                }
            except (IOError, RawPostDataException):
                parameters = {"body": "Unreadable POST body"}
            except Exception:
                parameters = {"body": request.body}

        return cleanse_data(parameters) if parameters else parameters
