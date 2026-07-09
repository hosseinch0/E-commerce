from django.db import transaction
from .models import OrderModel, OrderItemModel, OrderStatus
from cart.models import CartModel, CartStatus


@transaction.atomic
def create_order_from_cart(user):
    cart = CartModel.objects.select_for_update().get(
        user=user, status=CartStatus.ACTIVE)
    cart_items = cart.items.select_related("variant__product").all()

    if not cart_items.exists():
        raise ValueError("Cart is empty.")

    order = OrderModel.objects.create(user=user, status=OrderStatus.PLACED)

    total_rial = 0
    for item in cart_items:
        variant = item.variant
        # Create Snapshot
        OrderItemModel.objects.create(
            order=order,
            product_id=variant.product.id,
            product_name=variant.product.name,
            variant_id=variant.id,
            variant_sku=variant.sku,
            variant_display_name=variant.display_name,
            attributes_snapshot=variant.attributes_snapshot,
            unit_price_rial=variant.price_rial,
            quantity=item.quantity
        )
        total_rial += (variant.price_rial * item.quantity)

    order.total_amount_rial = total_rial
    order.save()

    # Clean up cart
    cart.status = CartStatus.CHECKED_OUT
    cart.save()

    return order
