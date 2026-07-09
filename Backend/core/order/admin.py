from django.contrib import admin
from .models import OrderModel, OrderItemModel


class OrderItemInline(admin.TabularInline):
    model = OrderItemModel
    fk_name = "order"
    extra = 0
    readonly_fields = [
        "product_name", "variant_sku", "unit_price_rial",
        "quantity", "line_total_rial"
    ]


@admin.register(OrderModel)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "status", "total_amount_rial", "created_at"]
    inlines = [OrderItemInline]
    readonly_fields = ["total_amount_rial", "created_at"]
