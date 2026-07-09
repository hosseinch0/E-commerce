from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
import uuid


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"
    REFUNDED = "refunded", "Refunded"


class PaymentGateway(models.TextChoices):
    SANDBOX = "sandbox", "Sandbox"
    ZARINPAL = "zarinpal", "Zarinpal"


class PaymentModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order = models.ForeignKey(
        "order.OrderModel",
        on_delete=models.PROTECT,
        related_name="payments",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    amount_rial = models.BigIntegerField(validators=[MinValueValidator(0)])

    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    gateway = models.CharField(
        max_length=50,
        choices=PaymentGateway.choices,
        default=PaymentGateway.SANDBOX,
    )

    authority = models.CharField(max_length=255, blank=True, null=True)
    ref_id = models.CharField(max_length=255, blank=True, null=True)

    request_payload = models.JSONField(default=dict, blank=True)
    verify_payload = models.JSONField(default=dict, blank=True)

    error_code = models.CharField(max_length=100, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    paid_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"{self.order_id} - {self.amount_rial} - {self.status}"

    @property
    def is_successful(self):
        return self.status == PaymentStatus.SUCCESS
