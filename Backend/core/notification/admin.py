from django.contrib import admin

from .models import NotificationModel


@admin.register(NotificationModel)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "recipient",
        "title",
        "notification_type",
        "priority",
        "is_read",
        "created_at",
        "expires_at",
    ]

    list_filter = [
        "notification_type",
        "priority",
        "is_read",
        "created_at",
        "expires_at",
    ]

    search_fields = [
        "id",
        "recipient__phone_number",
        "recipient__username",
        "recipient__email",
        "title",
        "message",
    ]

    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "read_at",
    ]

    ordering = ["-created_at"]

    fieldsets = (
        (
            "Main Info",
            {
                "fields": (
                    "id",
                    "recipient",
                    "title",
                    "message",
                    "notification_type",
                    "priority",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "is_read",
                    "read_at",
                    "expires_at",
                )
            },
        ),
        (
            "Action / Metadata",
            {
                "fields": (
                    "action_url",
                    "metadata",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
