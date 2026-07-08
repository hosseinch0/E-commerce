from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from notification.serializers import NotificationBulkDeleteResponseSerializer, NotificationBulkUpdateResponseSerializer
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    inline_serializer,
    OpenApiTypes,
)

from .models import NotificationModel
from .serializers import (
    NotificationSerializer,
    NotificationMarkReadSerializer,
    NotificationStatsSerializer,
)
from .services import mark_all_as_read
from .permissions import IsNotificationOwner


@extend_schema_view(
    list=extend_schema(
        summary="List my notifications",
        description=(
            "Returns authenticated user's notifications. "
            "Supports filtering by read status, notification type, priority, "
            "and expired notifications."
        ),
        parameters=[
            OpenApiParameter(
                name="is_read",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter notifications by read status. Use true or false.",
                examples=[
                    OpenApiExample(
                        "Unread notifications",
                        value=False,
                    ),
                    OpenApiExample(
                        "Read notifications",
                        value=True,
                    ),
                ],
            ),
            OpenApiParameter(
                name="type",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter notifications by notification type.",
            ),
            OpenApiParameter(
                name="priority",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter notifications by priority.",
            ),
            OpenApiParameter(
                name="include_expired",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "If true, expired notifications are included. "
                    "Default is false."
                ),
                examples=[
                    OpenApiExample(
                        "Include expired notifications",
                        value=True,
                    ),
                    OpenApiExample(
                        "Exclude expired notifications",
                        value=False,
                    ),
                ],
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
    create=extend_schema(
        summary="Create notification",
        description=(
            "Creates a notification for the authenticated user. "
            "This endpoint is intended for development only and should be disabled in production."
        ),
        request=NotificationSerializer,
        responses={
            201: NotificationSerializer,
            400: OpenApiResponse(description="Invalid notification data."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
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
class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsNotificationOwner]

    # POST METHOD SHOULD BE DELETED FOR PRODUCTION
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user

        queryset = NotificationModel.objects.filter(recipient=user)

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

    def perform_create(self, serializer):
        """
        Optional behavior:
        If you keep POST enabled, this lets authenticated users create
        notifications for themselves.

        For stricter production usage, you may remove POST from
        http_method_names and only create notifications through services.py.
        """
        serializer.save(recipient=self.request.user)

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
        serializer = NotificationMarkReadSerializer(data=request.data)
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
        summary="List all notifications",
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
        ],
    ),
    retrieve=extend_schema(
        tags=["Admin Notifications"],
        summary="Retrieve any notification",
        description="Admin-only endpoint for retrieving a notification by ID.",
    ),
)
class AdminNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin-only endpoint for viewing all notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        queryset = NotificationModel.objects.select_related("recipient").all()

        include_expired = self.request.query_params.get("include_expired")

        if include_expired != "true":
            queryset = queryset.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            )

        recipient_id = self.request.query_params.get("recipient")
        if recipient_id:
            queryset = queryset.filter(recipient_id=recipient_id)

        is_read = self.request.query_params.get("is_read")
        if is_read in ["true", "false"]:
            queryset = queryset.filter(is_read=is_read == "true")

        notification_type = self.request.query_params.get("type")
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        return queryset.order_by("-created_at")
