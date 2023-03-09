from django.urls import path

from api.answers import views

app_name = "answers"

urlpatterns = [
    path("", views.answers_root, name="root"),
    path("create/", views.answers_create, name="create"),
    path("update/", views.answers_update, name="update"),
    path("info/", views.answers_info, name="info"),
    path("info/<answer_id>/", views.answers_info, name="info"),
    path("search/", views.answers_search, name="search"),
]

