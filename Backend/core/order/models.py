import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PLACED = "placed", "Placed"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class OrderModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(
        max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    total_amount_rial = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Order"
        verbose_name_plural = "Orders"


class OrderItemModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        OrderModel,
        on_delete=models.CASCADE,
        related_name="items",
    )
    # Historical Snapshots
    product_id = models.UUIDField()
    product_name = models.CharField(max_length=255)
    variant_id = models.UUIDField()
    variant_sku = models.CharField(max_length=100)
    variant_display_name = models.CharField(max_length=255)
    attributes_snapshot = models.JSONField(default=dict)

    # Financial Snapshots
    unit_price_rial = models.BigIntegerField(validators=[MinValueValidator(0)])
    quantity = models.PositiveIntegerField(default=1)
    line_total_rial = models.BigIntegerField(validators=[MinValueValidator(0)])

    def save(self, *args, **kwargs):
        self.line_total_rial = self.unit_price_rial * self.quantity
        super().save(*args, **kwargs)
