"""
Base serializer
"""
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.fields import CharField


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Base serializer
    """

    CHECK_VALUES = ["\x00", "\n", "\t"]  # NULL_CHARACTER  # NEW_LINE_CHARACTER  # TAB_INDENT_CHARACTER

    REPLACE_VALUES = ["*NULL*", "*NEW_LINE*", "*TAB_IND*"]

    def __init__(self, *args, **kwargs):
        setattr(self.Meta, "extra_kwargs", self._preserve_white_spaces())
        super().__init__(*args, **kwargs)

    @staticmethod
    def cleanse_chars(raw_value, check_values, replace_values):
        """
        Change data to bypass character validators check

        NOTE: check_value=[], replace_value=[]
        """
        for i, check_value in enumerate(check_values):
            replace_value = replace_values[i]
            if check_value in str(raw_value):
                raw_value = raw_value.replace(check_value, replace_value)

        return raw_value

    def _preserve_white_spaces(self):
        """
        Disable trim_whitespaces validator for ALL CharFields
        """

        # A dictionary of {field_name: field_instance}.
        extra_kwargs = {}
        for key, value in list(self.get_fields().items()):
            if isinstance(value, CharField):
                extra_kwargs.update({key: {"trim_whitespace": False}})

        return extra_kwargs

    def to_internal_value(self, data):
        """
        Relaxed validation for tag values

        TODO: FIX THIS ISSUE
        Django 2.0+ introduced ProhibitNullCharactersValidator, that does NOT allow null characters, so need to
            convert them to a string and then convert back to bypass the validator. Also, new line and tab indent
            characters are removed
        """
        for tag, value in data.items():
            data[tag] = self.cleanse_chars(value, check_values=self.CHECK_VALUES, replace_values=self.REPLACE_VALUES)

        return super().to_internal_value(data)


class PaginationSerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=0, default=0)
    page_count = serializers.IntegerField(min_value=0, default=0)
    total_count = serializers.IntegerField(min_value=0, default=0)
    has_next = serializers.BooleanField(default=False)
    has_previous = serializers.BooleanField(default=False)
