from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import CartModel, CartItemModel, CartStatus


def get_or_create_active_cart(user):
    cart, _ = CartModel.objects.get_or_create(
        user=user,
        status=CartStatus.ACTIVE,
    )
    return cart


def validate_variant_for_cart(variant, quantity):
    product = variant.product

    if product.status != product.StatusChoices.ACTIVE:
        raise ValidationError({"variant": "This product is not available."})

    if not product.is_active:
        raise ValidationError({"variant": "This product is not active."})

    if not variant.is_active:
        raise ValidationError(
            {"variant": "This product variant is not active."})

    if quantity < 1:
        raise ValidationError({"quantity": "Quantity must be at least 1."})

    if variant.available_stock < quantity:
        raise ValidationError(
            {
                "quantity": (
                    f"Only {variant.available_stock} item(s) are available."
                )
            }
        )


@transaction.atomic
def add_variant_to_cart(*, user, variant, quantity):
    cart = get_or_create_active_cart(user)

    item, created = CartItemModel.objects.select_for_update().get_or_create(
        cart=cart,
        variant=variant,
        defaults={"quantity": quantity},
    )

    if created:
        validate_variant_for_cart(variant, quantity)
        return item

    new_quantity = item.quantity + quantity
    validate_variant_for_cart(variant, new_quantity)

    item.quantity = new_quantity
    item.save(update_fields=["quantity", "updated_at"])

    return item


@transaction.atomic
def update_cart_item_quantity(*, item, quantity):
    validate_variant_for_cart(item.variant, quantity)

    item.quantity = quantity
    item.save(update_fields=["quantity", "updated_at"])

    return item


@transaction.atomic
def clear_cart(cart):
    cart.items.all().delete()
    return cart
