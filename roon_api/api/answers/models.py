"""Model definitions for Answers + Tags"""
import logging
import uuid
from datetime import datetime

from django.db import models

from api.core.models import CoreModel
from api.core.utils import computed_model_keys

LOGGER = logging.getLogger("roon")


class Answer(CoreModel):
    """
    Roon health data answer to a particular question
    """

    # Primary
    answer_id = models.UUIDField("Answer ID", primary_key=True, default=uuid.uuid4, editable=False)

    # Main information
    description = models.TextField("Description", blank=False, null=False, db_index=True)

    # Relationships
    question = models.ForeignKey(
        "questions.Question", related_name="answers", blank=False, null=False, on_delete=models.deletion.CASCADE
    )
    owner = models.ForeignKey("users.User", blank=True, null=True, on_delete=models.deletion.SET_NULL)
    tags = models.ManyToManyField("answers.AnswerTag", blank=True)

    class Meta:
        db_table = "answer"
        verbose_name = "Answer"
        verbose_name_plural = "Answers"

    def __str__(self):
        return f"Answer: ID: {self.answer_id} and Question: {self.question.title}"

    def save(self, *args, **kwargs):
        if not self.answer_id:
            self.answer_id = uuid.uuid4()

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
            "answer_id",
        ]
        exclude.extend(CoreModel.model_keys())
        return computed_model_keys(cls, field_name_exclusions=exclude, field_type_exclusions=[])


class AnswerTag(CoreModel):
    """
    Tag of the supplied Answer
    """

    # Primary
    tag_id = models.UUIDField("Tag ID", primary_key=True, default=uuid.uuid4, editable=False)

    # Tag data
    title = models.CharField("Tag Title", max_length=256, blank=False, null=False, unique=True)

    class Meta:
        db_table = "answer_tag"
        verbose_name = "Answer Tag"
        verbose_name_plural = "Answer Tags"

    def __str__(self):
        return f"AnswerTag: ID: {self.tag_id} and Title: {self.title}"

    def save(self, **kwargs):
        if not self.tag_id:
            self.tag_id = uuid.uuid4()
        self.title = self.cleanse(self.title)

        self.last_modified = datetime.utcnow()
        super().save(**kwargs)
        return self

    @classmethod
    def cleanse(cls, value):
        """
        Helper method that strips whitespace
        unless the provided value is whitespace
        """
        if not value.isspace():
            return value.strip()
        return value

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
            "tag_id",
        ]

        exclude.extend(CoreModel.model_keys())
        return computed_model_keys(cls, field_name_exclusions=exclude, field_type_exclusions=[])
