"""
Model Serializers for Questions
"""
import copy
import logging
import operator
from functools import reduce

from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.answers.serializers import AnswerSerializer
from api.core.models import EagerLoadingMixin
from api.core.serializer import BaseModelSerializer, PaginationSerializer
from api.questions.models import Question
from api.topics.models import QuestionTopic
from api.topics.serializers import QuestionTopicSerializer
from api.users.api.serializers import UserSerializer

LOGGER = logging.getLogger("roon")


class BaseQuestionSerializer(BaseModelSerializer, EagerLoadingMixin):
    """
    Base Question Serializer
    """

    # Query Optimizations
    _SELECT_RELATED_FIELDS = ["owner", "canonical_answer", "canonical_answer__owner"]
    _PREFETCH_RELATED_FIELDS = [
        "topics",
        "canonical_answer__tags",
        "answers",
        "answers__question",
        "answers__tags",
    ]

    class Meta:
        model = Question
        fields = (
            # Primary
            "question_id",
            # Main information
            "title",
            "context",
        )
        depth = 1


class QuestionSerializer(BaseQuestionSerializer):
    """
    QuestionSerializer serializer.
    """

    # Canonical Answer ID
    canonical_answer_id = serializers.CharField(
        source="canonical_answer.answer_id", allow_null=True, allow_blank=True, required=False
    )

    # Related
    answers = AnswerSerializer(many=True, read_only=True)
    owner = UserSerializer(many=False, read_only=True)

    # Many-to-Many
    topics = QuestionTopicSerializer(many=True, read_only=False, required=False)

    class Meta:
        model = Question
        data_fields = (
            # Canonical
            "canonical_answer_id",
            # FK/Related
            "answers",
            "owner",
            # Many-to-Many
            "topics",
            # Dates
            "created_at",
            "last_modified",
            "deactivated_at",
        )
        fields = tuple(set(copy.deepcopy(BaseQuestionSerializer.Meta.fields + data_fields)))
        depth = 1

    @staticmethod
    def validate_topics(value):
        """
        Validation function to detect duplicate topics
        """
        topics = set()
        duplicates = set()

        for topic in value:
            title = topic["title"].strip()
            if title in topics:
                duplicates.add(title)
            else:
                topics.add(title)

        if duplicates:
            raise ValidationError(f"Duplicate topics detected: {', '.join(duplicates)}")

        return value

    def create(self, validated_data: dict[...]):
        """
        Override method used to create a new Question object
        """
        # Pop topic(s) data out of the incoming data
        topics = validated_data.pop("topics", None)
        # Create the question data object
        question = self.Meta.model.objects.create(**validated_data)

        if topics:
            self.add_topics(question, topics)

            # Save the question data object
            question.save()

        return question

    def update(self, instance: Question, validated_data):
        """
        Override method for serializer update used to update Question data
        """
        raise NotImplemented("Update functionality has not been created")

    @staticmethod
    def add_topics(instance: Question, topics: list[dict[str, str]]):
        """
        Adds question topics to model instance, does not save the model
        """
        titles = [topic["title"] for topic in topics]

        # Add all existing tags
        q_objs = [Q(title__iexact=topic["title"].strip()) for topic in topics]
        existing_topics: list[QuestionTopic] = QuestionTopic.active_objects.filter(reduce(operator.or_, q_objs))
        instance.topics.add(*existing_topics)

        # Collect all the non-existent topics that need to be added
        added = [topic.title for topic in existing_topics]
        add_topics = [topic for topic in titles if topic not in added]

        for title in add_topics:
            # Create the new topic
            topic = QuestionTopic(title=title)
            topic.save()
            # Add the topic to the question object
            instance.topics.add(topic)


class QuestionOnlySerializer(BaseQuestionSerializer, EagerLoadingMixin):
    # Query Optimizations
    _SELECT_RELATED_FIELDS = []
    _PREFETCH_RELATED_FIELDS = []


class QuestionPaginationSerializer(serializers.Serializer):
    """
    Paginated QuestionSerializer serializer.
    """
    pagination_info = PaginationSerializer(many=False, read_only=True)
    questions = QuestionSerializer(many=False, read_only=True)
