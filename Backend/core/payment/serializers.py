from rest_framework import serializers

from .models import PaymentModel


class PaymentSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source="order.id", read_only=True)

    class Meta:
        model = PaymentModel
        fields = [
            "id",
            "order_id",
            "amount_rial",
            "gateway",
            "status",
            "authority",
            "ref_id",
            "error_code",
            "error_message",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PaymentRequestSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField()
    payment_url = serializers.URLField()
