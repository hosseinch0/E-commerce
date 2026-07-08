from django.db.models import Q
from django.utils import timezone

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)

from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import NotificationModel
from .permissions import IsNotificationOwner
from .serializers import (
    NotificationBulkDeleteResponseSerializer,
    NotificationBulkUpdateResponseSerializer,
    NotificationMarkReadSerializer,
    NotificationSerializer,
    NotificationStatsSerializer,
)
from .services import mark_all_as_read


@extend_schema_view(
    list=extend_schema(
        summary="List my notifications",
        description=(
            "Returns authenticated user's notifications. Supports filtering by "
            "read status, notification type, priority, and expired notifications."
        ),
        parameters=[
            OpenApiParameter(
                name="is_read",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter notifications by read status.",
            ),
            OpenApiParameter(
                name="type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter notifications by notification type.",
            ),
            OpenApiParameter(
                name="priority",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter notifications by priority.",
            ),
            OpenApiParameter(
                name="include_expired",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="If true, expired notifications are included. Default is false.",
            ),
        ],
        responses={
            200: NotificationSerializer(many=True),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
        },
        tags=["Notifications"],
    ),
    retrieve=extend_schema(
        summary="Retrieve notification",
        description="Returns a single notification owned by the authenticated user.",
        responses={
            200: NotificationSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            403: OpenApiResponse(description="You do not have permission to access this notification."),
            404: OpenApiResponse(description="Notification not found."),
        },
        tags=["Notifications"],
    ),
    destroy=extend_schema(
        summary="Delete notification",
        description="Deletes one notification owned by the authenticated user.",
        responses={
            204: None,
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            403: OpenApiResponse(description="You do not have permission to delete this notification."),
            404: OpenApiResponse(description="Notification not found."),
        },
        tags=["Notifications"],
    ),
)
class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsNotificationOwner]
    http_method_names = ["get", "delete", "post", "head", "options"]

    def get_queryset(self):
        queryset = NotificationModel.objects.filter(
            recipient=self.request.user,
        )

        is_read = self.request.query_params.get("is_read")
        notification_type = self.request.query_params.get("type")
        priority = self.request.query_params.get("priority")
        include_expired = self.request.query_params.get(
            "include_expired", "false")

        if is_read in ["true", "false"]:
            queryset = queryset.filter(is_read=is_read == "true")

        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        if priority:
            queryset = queryset.filter(priority=priority)

        if include_expired != "true":
            queryset = queryset.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            )

        return queryset.order_by("-created_at")

    @extend_schema(
        summary="Mark notification as read",
        description="Marks a single notification as read.",
        request=None,
        responses={
            200: NotificationSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            403: OpenApiResponse(description="You do not have permission to modify this notification."),
            404: OpenApiResponse(description="Notification not found."),
        },
        examples=[
            OpenApiExample(
                name="Success response",
                value={
                    "id": "7dc9377a-5e35-4c48-8d18-1d364f23c1c4",
                    "title": "Order shipped",
                    "message": "Your order has been shipped.",
                    "is_read": True,
                    "read_at": "2026-07-08T12:00:00Z",
                },
                response_only=True,
            ),
        ],
        tags=["Notifications"],
    )
    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_read()

        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Mark notification as unread",
        description="Marks a single notification as unread.",
        request=None,
        responses={
            200: NotificationSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            403: OpenApiResponse(description="You do not have permission to modify this notification."),
            404: OpenApiResponse(description="Notification not found."),
        },
        examples=[
            OpenApiExample(
                name="Success response",
                value={
                    "id": "7dc9377a-5e35-4c48-8d18-1d364f23c1c4",
                    "title": "Order shipped",
                    "message": "Your order has been shipped.",
                    "is_read": False,
                    "read_at": None,
                },
                response_only=True,
            ),
        ],
        tags=["Notifications"],
    )
    @action(detail=True, methods=["post"], url_path="mark-unread")
    def mark_unread(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_unread()

        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Mark all notifications as read",
        description="Marks all unread notifications of the authenticated user as read.",
        request=None,
        responses={
            200: NotificationBulkUpdateResponseSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided."),
        },
        examples=[
            OpenApiExample(
                name="Success response",
                value={
                    "detail": "All notifications marked as read.",
                    "updated_count": 5,
                },
                response_only=True,
            ),
        ],
        tags=["Notifications"],
    )
    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        updated_count = mark_all_as_read(request.user)

        return Response(
            {
                "detail": "All notifications marked as read.",
                "updated_count": updated_count,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Mark selected notifications as read",
        description="Marks selected notifications as read by their IDs.",
        request=NotificationMarkReadSerializer,
        responses={
            200: NotificationBulkUpdateResponseSerializer,
            400: OpenApiResponse(description="Invalid notification IDs."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
        },
        examples=[
            OpenApiExample(
                name="Request example",
                value={
                    "notification_ids": [
                        "7dc9377a-5e35-4c48-8d18-1d364f23c1c4",
                        "bf38b058-4747-4b66-bf0a-a84dc1f07c5e",
                    ]
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Success response",
                value={
                    "detail": "Selected notifications marked as read.",
                    "updated_count": 2,
                },
                response_only=True,
            ),
        ],
        tags=["Notifications"],
    )
    @action(detail=False, methods=["post"], url_path="mark-selected-read")
    def mark_selected_read(self, request):
        serializer = NotificationMarkReadSerializer(
            data=request.data, context={"request": request},)
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data.get(
            "notification_ids", [])

        updated_count = NotificationModel.objects.filter(
            id__in=notification_ids,
            recipient=request.user,
            is_read=False,
        ).update(
            is_read=True,
            read_at=timezone.now(),
        )

        return Response(
            {
                "detail": "Selected notifications marked as read.",
                "updated_count": updated_count,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Get notification stats",
        description="Returns total, unread, and read notification counts for the authenticated user.",
        request=None,
        responses={
            200: NotificationStatsSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided."),
        },
        examples=[
            OpenApiExample(
                name="Success response",
                value={
                    "total": 20,
                    "unread": 7,
                    "read": 13,
                },
                response_only=True,
            ),
        ],
        tags=["Notifications"],
    )
    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        queryset = NotificationModel.objects.filter(recipient=request.user)

        total = queryset.count()
        unread = queryset.filter(is_read=False).count()
        read = queryset.filter(is_read=True).count()

        return Response(
            {
                "total": total,
                "unread": unread,
                "read": read,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Delete all read notifications",
        description="Deletes all read notifications of the authenticated user.",
        request=None,
        responses={
            200: NotificationBulkDeleteResponseSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided."),
        },
        examples=[
            OpenApiExample(
                name="Success response",
                value={
                    "detail": "Read notifications deleted.",
                    "deleted_count": 10,
                },
                response_only=True,
            ),
        ],
        tags=["Notifications"],
    )
    @action(detail=False, methods=["delete"], url_path="delete-read")
    def delete_read(self, request):
        deleted_count, _ = NotificationModel.objects.filter(
            recipient=request.user,
            is_read=True,
        ).delete()

        return Response(
            {
                "detail": "Read notifications deleted.",
                "deleted_count": deleted_count,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Delete all my notifications",
        description="Deletes all notifications of the authenticated user.",
        request=None,
        responses={
            200: NotificationBulkDeleteResponseSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided."),
        },
        examples=[
            OpenApiExample(
                name="Success response",
                value={
                    "detail": "All notifications deleted.",
                    "deleted_count": 20,
                },
                response_only=True,
            ),
        ],
        tags=["Notifications"],
    )
    @action(detail=False, methods=["delete"], url_path="delete-all")
    def delete_all(self, request):
        deleted_count, _ = NotificationModel.objects.filter(
            recipient=request.user,
        ).delete()

        return Response(
            {
                "detail": "All notifications deleted.",
                "deleted_count": deleted_count,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    list=extend_schema(
        tags=["Admin Notifications"],
        summary="List notifications",
        description="Admin-only endpoint for listing all user notifications.",
        parameters=[
            OpenApiParameter(
                name="include_expired",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Include expired notifications.",
            ),
            OpenApiParameter(
                name="recipient",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter notifications by recipient user UUID.",
            ),
            OpenApiParameter(
                name="is_read",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter by read status.",
            ),
            OpenApiParameter(
                name="type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter by notification type.",
            ),
            OpenApiParameter(
                name="priority",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter by priority.",
            ),
        ],
        responses={200: NotificationSerializer(many=True)},
    ),
    create=extend_schema(
        tags=["Admin Notifications"],
        summary="Create notification",
        description="Admin-only endpoint for creating a notification for a user.",
        request=NotificationSerializer,
        responses={
            201: NotificationSerializer,
            400: OpenApiResponse(description="Invalid notification data."),
        },
    ),
    retrieve=extend_schema(
        tags=["Admin Notifications"],
        summary="Retrieve notification",
        description="Admin-only endpoint for retrieving a notification by ID.",
        responses={
            200: NotificationSerializer,
            404: OpenApiResponse(description="Notification not found."),
        },
    ),
    update=extend_schema(
        tags=["Admin Notifications"],
        summary="Update notification",
        description="Admin-only endpoint for fully updating a notification.",
        request=NotificationSerializer,
        responses={
            200: NotificationSerializer,
            400: OpenApiResponse(description="Invalid notification data."),
            404: OpenApiResponse(description="Notification not found."),
        },
    ),
    partial_update=extend_schema(
        tags=["Admin Notifications"],
        summary="Partially update notification",
        description="Admin-only endpoint for partially updating a notification.",
        request=NotificationSerializer,
        responses={
            200: NotificationSerializer,
            400: OpenApiResponse(description="Invalid notification data."),
            404: OpenApiResponse(description="Notification not found."),
        },
    ),
    destroy=extend_schema(
        tags=["Admin Notifications"],
        summary="Delete notification",
        description="Admin-only endpoint for deleting any notification.",
        responses={
            204: None,
            404: OpenApiResponse(description="Notification not found."),
        },
    ),
)
class AdminNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ["get", "post", "put",
                         "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = NotificationModel.objects.select_related("recipient").all()

        include_expired = self.request.query_params.get(
            "include_expired", "false")
        recipient_id = self.request.query_params.get("recipient")
        is_read = self.request.query_params.get("is_read")
        notification_type = self.request.query_params.get("type")
        priority = self.request.query_params.get("priority")

        if include_expired != "true":
            queryset = queryset.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            )

        if recipient_id:
            queryset = queryset.filter(recipient_id=recipient_id)

        if is_read in ["true", "false"]:
            queryset = queryset.filter(is_read=is_read == "true")

        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset.order_by("-created_at")
