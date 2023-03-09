"""Intermediate API level URLs for the Roon Service"""
from django.urls import include, path

from api.core import views

urlpatterns = [
    # API Root
    path("", views.api_root, name="api_root"),
    ###
    # Questions
    ###
    path("questions/", include("api.questions.urls", namespace="questions")),
    # Answers
    path("questions/answers/", include("api.answers.urls", namespace="answers")),
    # Topics
    path("questions/topics/", include("api.topics.urls", namespace="topics")),
]
