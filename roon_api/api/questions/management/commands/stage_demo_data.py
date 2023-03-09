"""
Upload Demo Data
"""
import logging
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand

from api.answers.models import Answer, AnswerTag
from api.questions.models import Question
from api.topics.models import QuestionTopic
from api.users.models import User

LOGGER = logging.getLogger("roon")


class Command(BaseCommand):
    """
    Create demo data
    """

    help = """Create demo data."""

    def handle(self, **options):
        fname = Path(__file__).resolve(strict=True).parent / "FAQCodingExercise - FAQCodingExercise.csv"

        df = pd.read_csv(fname, header=0)
        df = df.reset_index()

        user = User.objects.get(username="koonalb@gmail.com")

        for index, row in df.iterrows():
            # Create Question
            question = Question(title=row["Question Title"], owner=user)
            question.save()

            # Create Topic
            try:
                topics = row["Topics"].strip().split(", ")
                if existing_topics := QuestionTopic.active_objects.filter(title__in=topics):
                    question.topics.add(*existing_topics)

                added_topics = [topic.title for topic in existing_topics]
                add_topics = [topic for topic in topics if topic not in added_topics]

                for title in add_topics:
                    # Create the new topic
                    topic = QuestionTopic(title=title)
                    topic.save()
                    # Add the topic to the question object
                    question.topics.add(topic)
            except Exception as err:
                print(f"{type(err).__name__} Error Topic data: {row['Topics']} and reason: {str(err)}...skipping")

            # Create Answer
            answer = Answer(description=row["Answer"], question=question, owner=user)
            answer.save()

            if possible_answer := row["Possible Multiple Answers"]:
                another_answer = Answer(description=possible_answer, question=question, owner=user)
                another_answer.save()

            if possible_long_answer := row["Long Answer"]:
                another_long_answer = Answer(description=possible_long_answer, question=question, owner=user)
                another_long_answer.save()

            question.canonical_answer = answer
            question.save()

            # Create Answer Tag
            try:
                tags = row["Tags"].strip().split(", ")
                if existing_tags := AnswerTag.active_objects.filter(title__in=tags):
                    answer.tags.add(*existing_tags)

                added_tags = [tag.title for tag in existing_tags]
                add_tags = [tag for tag in tags if tag not in added_tags]

                for title in add_tags:
                    # Create the new tag
                    tag = AnswerTag(title=title)
                    tag.save()
                    # Add the tag to the answer object
                    answer.tags.add(tag)
            except Exception as err:
                print(f"{type(err).__name__} Error Tag data: {row['Tags']} and reason: {str(err)}...skipping")
