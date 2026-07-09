from rest_framework import serializers
from .models import OrderModel, OrderItemModel


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItemModel
        fields = [
            "product_name", "variant_display_name", "variant_sku",
            "attributes_snapshot", "unit_price_rial", "quantity", "line_total_rial"
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = OrderModel
        fields = ["id", "status", "total_amount_rial", "items", "created_at"]
        read_only_fields = ["id", "status",
                            "total_amount_rial", "items", "created_at"]
