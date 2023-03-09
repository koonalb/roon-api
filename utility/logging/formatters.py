"""Defines RequestLogMessage and RequestLogFormatter"""
import json
import logging
from collections import OrderedDict
from datetime import datetime

from utility.logging.filters import RequestLogFilter


class RequestLogMessage(OrderedDict):
    """OrderedDict that removes empty attributes"""
    def __init__(self, record):
        super(RequestLogMessage, self).__init__()

        for field in RequestLogFilter.get_fields():
            if isinstance(field, tuple):
                label, name = field
                self[label] = getattr(record, name, None)
                if not self[label]:
                    del self[label]
            elif isinstance(field, str):
                self[field] = getattr(record, field, None)
                if not self[field]:
                    del self[field]


class RequestLogFormatter(logging.Formatter):
    """Custom logging formatter that allows for microsecond resolution in the default asctime attribute."""

    def __init__(self, fmt=None, datefmt=None):
        super(RequestLogFormatter, self).__init__(fmt=fmt, datefmt=datefmt)
        self.converter = self._converter

    def format(self, record):
        super(RequestLogFormatter, self).format(record)
        try:
            return json.dumps(RequestLogMessage(record))
        except TypeError:
            data = RequestLogMessage(record)['parameters']['body'].decode('utf8')
            RequestLogMessage(record)['parameters']['body'] = data
            return json.dumps(RequestLogMessage(record))

    def formatTime(self, record, datefmt=None):
        """Override the default formatTime method to return a formatted time string using datetime"""
        created = self.converter(record.created)
        return created.strftime(datefmt) if datefmt else created.strftime("%Y-%m-%dT%H:%M:%S.%f%z")

    def usesTime(self):
        return True

    @staticmethod
    def _converter(secs=None):
        return datetime.fromtimestamp(secs) if secs else datetime.now()
