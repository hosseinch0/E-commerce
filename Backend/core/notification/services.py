from typing import Optional

from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import NotificationModel

User = get_user_model()


def create_notification(
    *,
    recipient,
    title: str,
    message: str,
    notification_type: str = NotificationModel.TypeChoices.INFO,
    priority: str = NotificationModel.PriorityChoices.NORMAL,
    action_url: Optional[str] = None,
    metadata: Optional[dict] = None,
    expires_at=None,
) -> NotificationModel:
    """
    Create one notification for one user.
    """

    return NotificationModel.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
        action_url=action_url,
        metadata=metadata or {},
        expires_at=expires_at,
    )


def create_bulk_notifications(
    *,
    recipients,
    title: str,
    message: str,
    notification_type: str = NotificationModel.TypeChoices.INFO,
    priority: str = NotificationModel.PriorityChoices.NORMAL,
    action_url: Optional[str] = None,
    metadata: Optional[dict] = None,
    expires_at=None,
):
    """
    Create notifications for multiple users efficiently.
    """

    notifications = [
        NotificationModel(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            action_url=action_url,
            metadata=metadata or {},
            expires_at=expires_at,
        )
        for recipient in recipients
    ]

    return NotificationModel.objects.bulk_create(notifications)


def mark_all_as_read(user):
    return NotificationModel.objects.filter(
        recipient=user,
        is_read=False,
    ).update(
        is_read=True,
        read_at=timezone.now(),
    )


def delete_expired_notifications():
    return NotificationModel.objects.filter(
        expires_at__isnull=False,
        expires_at__lte=timezone.now(),
    ).delete()
