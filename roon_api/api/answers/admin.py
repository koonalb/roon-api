"""Admin interface to Answer models"""
from django.contrib import admin

from api.answers.models import Answer, AnswerTag


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """
    Admin for Answer
    """

    model = Answer

    search_fields = ["answer_id", "description", "question.question_id", "question.title"]
    list_display = (
        "answer_id",
        "description",
        "question_title",
        "owner_name",
        "owner_email",
        "created_at",
        "is_active",
    )

    @admin.display(description="Question's Title")
    def question_title(self, obj):
        if obj.question:
            return obj.question.title
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
    raw_id_fields = ("question", "owner")
    readonly_fields = ("answer_id",)

    fieldsets = (
        ("Answer ID", {"fields": ("answer_id",)}),
        ("Foreign Keys", {"fields": raw_id_fields}),
        (
            "Answer Info",
            {"fields": ("description",)},
        ),
        (
            "Many-To-Many Info",
            {"fields": ("tags",)},
        ),
        ("Important dates", {"fields": ("created_at", "last_modified", "deactivated_at")}),
        ("Active", {"fields": ("is_active",)}),
    )


@admin.register(AnswerTag)
class AnswerTagAdmin(admin.ModelAdmin):
    """
    Admin for AnswerTag
    """

    model = AnswerTag

    search_fields = ["tag_id", "title"]
    list_display = (
        "tag_id",
        "title",
        "created_at",
        "is_active",
    )

    list_filter = ("is_active",)
    raw_id_fields = ()
    readonly_fields = ("tag_id",)

    fieldsets = (
        ("Answer ID", {"fields": ("tag_id",)}),
        ("Foreign Keys", {"fields": raw_id_fields}),
        (
            "Tag Info",
            {"fields": ("title",)},
        ),
        ("Important dates", {"fields": ("created_at", "last_modified", "deactivated_at")}),
        ("Active", {"fields": ("is_active",)}),
    )
