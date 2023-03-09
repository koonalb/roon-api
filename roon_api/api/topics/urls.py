from django.urls import path

from api.topics import views

app_name = "topics"

urlpatterns = [
    path("", views.topics_root, name="root"),
    path("create/", views.topics_create, name="create"),
    path("update/", views.topics_update, name="update"),
    path("info/", views.topics_info, name="info"),
    path("info/<topic_id>/", views.topics_info, name="info"),
    path("search/", views.topics_search, name="search"),
]

