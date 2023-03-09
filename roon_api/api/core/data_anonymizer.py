"""
Data anonymizer class.
"""
import copy

from django.conf import settings


class DataAnonymizer(object):
    """
    Class anonymizes value of keys matching the predefined field list
    """

    FIELD_PREFIX = []
    ANONYMIZE_FIELDS = []
    ANONYMIZE_STRING = "Anonymized Data"

    def __init__(self, anonymize_fields=None, field_prefix=None, anonymize_value=None):
        """
        Constructor
        """
        self.anonymize_fields = anonymize_fields if anonymize_fields else self.ANONYMIZE_FIELDS
        self.field_prefix = field_prefix if field_prefix else self.FIELD_PREFIX
        self.anonymize_value = anonymize_value if anonymize_value else self.ANONYMIZE_STRING

        to_anonymize = [prefix + field for field in self.anonymize_fields for prefix in self.field_prefix]
        self.anonymize_fields.extend(to_anonymize)

    def run(self, data):
        """
        Method to perform anonymization. Method returns a new dict. The original
            'data' is not changed.
        """
        data = copy.deepcopy(data)

        for key in data:
            if isinstance(data[key], dict):
                data[key] = self.run(data[key])
            elif key in self.anonymize_fields:
                data[key] = self.anonymize_value

        return data


def cleanse_data(data, fields=None):
    """
    Remove sensitive data
    """
    anonymize_fields = []
    anonymize_fields.extend(settings.ANONYMIZE_API_VALUES)
    if fields:
        anonymize_fields.extend(fields)

    field_prefix = []
    field_prefix.extend(settings.ANONYMIZE_API_PREFIX_VALUES)

    anonymizer = DataAnonymizer(anonymize_fields=anonymize_fields, field_prefix=field_prefix)
    return anonymizer.run(data)  # makes a copy
