"""
Model Serializers for Topics
"""
import logging

from api.core.serializer import BaseModelSerializer
from api.topics.models import QuestionTopic

LOGGER = logging.getLogger("roon")


class QuestionTopicSerializer(BaseModelSerializer):
    """
    QuestionTopic serializer.
    """

    class Meta:
        model = QuestionTopic
        fields = ("topic_id", "title")
