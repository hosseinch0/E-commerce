from django.conf import settings
from django.db import models
from django.db.models import Q
import uuid


class CartStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    CHECKED_OUT = "checked_out", "Checked out"
    ABANDONED = "abandoned", "Abandoned"


class CartModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carts",
    )

    status = models.CharField(
        max_length=20,
        choices=CartStatus.choices,
        default=CartStatus.ACTIVE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status=CartStatus.ACTIVE),
                name="unique_active_cart_per_user",
            )
        ]

    @property
    def subtotal_rial(self):
        return sum(item.line_total_rial for item in self.items.select_related("variant"))

    @property
    def subtotal_toman(self):
        return self.subtotal_rial // 10

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"{self.user} - {self.status}"


class CartItemModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    cart = models.ForeignKey(
        CartModel,
        on_delete=models.CASCADE,
        related_name="items",
    )

    variant = models.ForeignKey(
        "product.ProductVariantModel",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )

    quantity = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "variant"],
                name="unique_variant_per_cart",
            )
        ]

    @property
    def unit_price_rial(self):
        return self.variant.price_rial

    @property
    def unit_price_toman(self):
        return self.variant.price_toman

    @property
    def line_total_rial(self):
        return self.unit_price_rial * self.quantity

    @property
    def line_total_toman(self):
        return self.line_total_rial // 10

    def __str__(self):
        return f"{self.variant} x {self.quantity}"
