"""Admin interface to Topic models"""
from django.contrib import admin

from api.topics.models import QuestionTopic


@admin.register(QuestionTopic)
class QuestionTopicAdmin(admin.ModelAdmin):
    """
    Admin for Question Topics
    """

    model = QuestionTopic

    search_fields = [
        "title",
    ]

    list_display = ("title", "is_active")
    readonly_fields = ("topic_id",)

    fieldsets = (
        ("Topic ID", {"fields": ("topic_id",)}),
        ("Topic Info", {"fields": ("title",)}),
        ("Important dates", {"fields": ("created_at", "last_modified", "deactivated_at")}),
        ("Active", {"fields": ("is_active",)}),
    )
