"""
Model Serializers for Answers + Tags
"""
import logging

from rest_framework import serializers

from api.answers.models import Answer, AnswerTag
from api.core.models import EagerLoadingMixin
from api.core.serializer import BaseModelSerializer
from users.api.serializers import UserSerializer

LOGGER = logging.getLogger("roon")


class AnswerTagSerializer(BaseModelSerializer):
    """
    AnswerTag serializer.
    """

    class Meta:
        model = AnswerTag
        fields = ("tag_id", "title")


class AnswerSerializer(BaseModelSerializer, EagerLoadingMixin):
    """
    AnswerSerializer serializer.
    """

    # Query Optimizations
    _SELECT_RELATED_FIELDS = ["question", "owner"]
    _PREFETCH_RELATED_FIELDS = [
        "tags",
    ]

    # Related
    question_id = serializers.CharField(source="question.question_id", allow_null=True, allow_blank=True)
    # owner = UserSerializer(many=False, read_only=True)

    # Many-to-Many
    tags = AnswerTagSerializer(many=True, read_only=True)

    class Meta:
        model = Answer
        fields = (
            # Primary
            "answer_id",
            # Main information
            "description",
            # FK/Related
            "question_id",
            # "owner",
            # Many-to-Many
            "tags",
            # Dates
            "created_at",
            "last_modified",
            "deactivated_at",
        )
        depth = 1

    def create(self, validated_data):
        """
        Override method used to create a new Answer object
        """
        return self.Meta.model.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Override method for serializer update used to update Answer data
        """
        raise NotImplemented("Update functionality has not been created")
