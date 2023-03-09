"""Admin interface to Question models"""
from django.contrib import admin

from api.questions.models import Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    Admin for Question
    """

    model = Question

    search_fields = ["question_id", "title", "context", "canonical_answer.answer_id", "canonical_answer.description"]
    list_display = (
        "question_id",
        "title",
        "context",
        "canonical_answer_id",
        "owner_name",
        "owner_email",
        "created_at",
        "is_active",
    )

    @admin.display(description="Answer's ID")
    def canonical_answer_id(self, obj):
        if obj.canonical_answer:
            return obj.canonical_answer.answer_id
        else:
            return None

    @admin.display(description="Owner's Name")
    def owner_name(self, obj):
        if obj.owner:
            return obj.owner.name
        else:
            return None

    @admin.display(description="Owner's Email")
    def owner_email(self, obj):
        if obj.owner:
            return obj.owner.email
        else:
            return None

    list_filter = ("is_active",)
    raw_id_fields = ("canonical_answer", "owner")
    readonly_fields = ("question_id",)

    fieldsets = (
        ("Question ID", {"fields": ("question_id",)}),
        ("Foreign Keys", {"fields": raw_id_fields}),
        (
            "Question Info",
            {
                "fields": (
                    "title",
                    "context",
                )
            },
        ),
        (
            "Many-To-Many Info",
            {"fields": ("topics",)},
        ),
        ("Important dates", {"fields": ("created_at", "last_modified", "deactivated_at")}),
        ("Active", {"fields": ("is_active",)}),
    )
