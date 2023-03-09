"""Model definitions for Questions"""
import logging
import uuid
from datetime import datetime

from django.db import models

from api.core.models import CoreModel
from api.core.utils import computed_model_keys

LOGGER = logging.getLogger("roon")


class Question(CoreModel):
    """
    Roon health data question to be asked
    """

    # Primary
    question_id = models.UUIDField("Question ID", primary_key=True, default=uuid.uuid4, editable=False)

    # Main information
    title = models.CharField("Title", max_length=256, blank=False, null=False, db_index=True)
    context = models.TextField("Context", max_length=256, blank=True, null=True, db_index=True, default=None)
    canonical_answer = models.ForeignKey(
        "answers.Answer",
        to_field="answer_id",
        related_name="canonical_answer",
        blank=True,
        null=True,
        on_delete=models.deletion.SET_NULL,
    )

    # Relationships
    owner = models.ForeignKey("users.User", blank=True, null=True, on_delete=models.deletion.SET_NULL)
    topics = models.ManyToManyField("topics.QuestionTopic", blank=True)

    class Meta:
        db_table = "question"
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def __str__(self):
        return f"Question: ID: {self.question_id} and Title: {self.title}"

    def save(self, *args, **kwargs):
        if not self.question_id:
            self.question_id = uuid.uuid4()

        self.last_modified = datetime.utcnow()
        super().save(*args, **kwargs)

        return self

    @classmethod
    def param_transform(cls):
        """
        Either model or serializer computed properties
        """

        return {}

    @classmethod
    def model_keys(cls):
        """
        List of attributes associated with this model class
        """
        exclude = [
            "question_id",
        ]
        exclude.extend(CoreModel.model_keys())
        return computed_model_keys(cls, field_name_exclusions=exclude, field_type_exclusions=[])
