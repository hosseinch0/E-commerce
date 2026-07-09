from rest_framework import serializers
from product.models import ProductVariantModel

from .models import CartModel, CartItemModel
from .services import add_variant_to_cart, update_cart_item_quantity


class CartVariantProductSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.SlugField()


class CartVariantSerializer(serializers.ModelSerializer):
    product = CartVariantProductSerializer(read_only=True)
    available_stock = serializers.IntegerField(read_only=True)
    price_toman = serializers.IntegerField(read_only=True)
    compare_at_price_toman = serializers.IntegerField(read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductVariantModel
        fields = [
            "id",
            "product",
            "sku",
            "display_name",
            "price_rial",
            "price_toman",
            "compare_at_price_rial",
            "compare_at_price_toman",
            "available_stock",
            "is_in_stock",
            "has_discount",
            "discount_percent",
            "attributes_snapshot",
        ]


class CartItemSerializer(serializers.ModelSerializer):
    variant = CartVariantSerializer(read_only=True)
    unit_price_rial = serializers.IntegerField(read_only=True)
    unit_price_toman = serializers.IntegerField(read_only=True)
    line_total_rial = serializers.IntegerField(read_only=True)
    line_total_toman = serializers.IntegerField(read_only=True)

    class Meta:
        model = CartItemModel
        fields = [
            "id",
            "variant",
            "quantity",
            "unit_price_rial",
            "unit_price_toman",
            "line_total_rial",
            "line_total_toman",
            "created_at",
            "updated_at",
        ]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal_rial = serializers.IntegerField(read_only=True)
    subtotal_toman = serializers.IntegerField(read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = CartModel
        fields = [
            "id",
            "status",
            "items",
            "subtotal_rial",
            "subtotal_toman",
            "total_items",
            "created_at",
            "updated_at",
        ]


class AddCartItemSerializer(serializers.Serializer):
    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariantModel.objects.select_related("product").filter(
            is_active=True,
            product__is_active=True,
            product__status="active",
        )
    )
    quantity = serializers.IntegerField(min_value=1)

    def save(self, **kwargs):
        return add_variant_to_cart(
            user=self.context["request"].user,
            variant=self.validated_data["variant"],
            quantity=self.validated_data["quantity"],
        )


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

    def save(self, **kwargs):
        return update_cart_item_quantity(
            item=self.context["item"],
            quantity=self.validated_data["quantity"],
        )


class AdminCartUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    phone_number = serializers.CharField()
    is_active = serializers.BooleanField()


class AdminCartSerializer(serializers.ModelSerializer):
    user = AdminCartUserSerializer(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    subtotal_rial = serializers.IntegerField(read_only=True)
    subtotal_toman = serializers.IntegerField(read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = CartModel
        fields = [
            "id",
            "user",
            "status",
            "items",
            "subtotal_rial",
            "subtotal_toman",
            "total_items",
            "created_at",
            "updated_at",
        ]
