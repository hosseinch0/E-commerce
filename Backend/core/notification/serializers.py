from rest_framework import serializers

from .models import NotificationModel
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    inline_serializer,
)


class NotificationSerializer(serializers.ModelSerializer):
    recipient_id = serializers.UUIDField(source="recipient.id", read_only=True)

    class Meta:
        model = NotificationModel
        fields = [
            "id",
            "recipient_id",
            "title",
            "message",
            "notification_type",
            "priority",
            "is_read",
            "read_at",
            "action_url",
            "metadata",
            "created_at",
            "updated_at",
            "expires_at",
            "is_expired",
        ]
        read_only_fields = [
            "id",
            "recipient_id",
            "is_read",
            "read_at",
            "created_at",
            "updated_at",
            "is_expired",
        ]


class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationModel
        fields = [
            "recipient",
            "title",
            "message",
            "notification_type",
            "priority",
            "action_url",
            "metadata",
            "expires_at",
        ]


class NotificationMarkReadSerializer(serializers.Serializer):
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=False,
    )


class NotificationStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    unread = serializers.IntegerField()
    read = serializers.IntegerField()


NotificationBulkUpdateResponseSerializer = inline_serializer(
    name="NotificationBulkUpdateResponse",
    fields={
        "detail": serializers.CharField(),
        "updated_count": serializers.IntegerField(),
    },
)

NotificationBulkDeleteResponseSerializer = inline_serializer(
    name="NotificationBulkDeleteResponse",
    fields={
        "detail": serializers.CharField(),
        "deleted_count": serializers.IntegerField(),
    },
)
