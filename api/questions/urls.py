from django.urls import path

from api.questions import views

app_name = "questions"

urlpatterns = [
    path("", views.questions_root, name="root"),
    path("create/", views.questions_create, name="create"),
    path("update/", views.questions_update, name="update"),
    path("info/", views.questions_info, name="info"),
    path("info/<question_id>/", views.questions_info, name="info"),
    path("search/", views.questions_search, name="search"),
]

