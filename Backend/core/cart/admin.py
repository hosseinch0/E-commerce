from django.contrib import admin

from .models import CartModel, CartItemModel


class CartItemInline(admin.TabularInline):
    model = CartItemModel
    extra = 0
    readonly_fields = [
        "id",
        "variant",
        "quantity",
        "unit_price_rial",
        "line_total_rial",
        "created_at",
        "updated_at",
    ]


@admin.register(CartModel)
class CartAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "status",
        "total_items",
        "subtotal_rial",
        "subtotal_toman",
        "created_at",
        "updated_at",
    ]
    list_filter = [
        "status",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "id",
        "user__phone_number",
    ]
    readonly_fields = [
        "id",
        "subtotal_rial",
        "subtotal_toman",
        "total_items",
        "created_at",
        "updated_at",
    ]
    inlines = [CartItemInline]


@admin.register(CartItemModel)
class CartItemAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "cart",
        "variant",
        "quantity",
        "unit_price_rial",
        "line_total_rial",
        "created_at",
    ]
    search_fields = [
        "id",
        "cart__id",
        "variant__sku",
        "variant__product__name",
    ]
    readonly_fields = [
        "id",
        "unit_price_rial",
        "unit_price_toman",
        "line_total_rial",
        "line_total_toman",
        "created_at",
        "updated_at",
    ]
