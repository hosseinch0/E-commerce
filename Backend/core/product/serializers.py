from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import (
    BrandModel,
    CategoryModel,
    ProductAttributeModel,
    ProductAttributeValueModel,
    ProductImageModel,
    ProductModel,
    ProductSpecificationModel,
    ProductVariantAttributeValueModel,
    ProductVariantModel,
)


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = CategoryModel
        fields = [
            "id",
            "name",
            "slug",
            "parent",
            "children",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True, context=self.context).data


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandModel
        fields = [
            "id",
            "name",
            "slug",
            "is_active",
        ]
        read_only_fields = ["id", "slug"]


class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttributeModel
        fields = [
            "id",
            "name",
            "slug",
        ]
        read_only_fields = ["id", "slug"]


class ProductAttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(
        source="attribute.name", read_only=True)

    class Meta:
        model = ProductAttributeValueModel
        fields = [
            "id",
            "attribute",
            "attribute_name",
            "value",
            "slug",
        ]
        read_only_fields = ["id", "slug"]


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImageModel
        fields = [
            "id",
            "product",
            "image",
            "image_url",
            "alt_text",
            "is_primary",
            "sort_order",
        ]
        read_only_fields = ["id", "image_url"]

    def get_image_url(self, obj):
        if not obj.image:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(obj.image.url)

        return obj.image.url


class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecificationModel
        fields = [
            "id",
            "product",
            "key",
            "value",
            "sort_order",
        ]
        read_only_fields = ["id"]


class ProductVariantAttributeValueSerializer(serializers.ModelSerializer):
    attribute = serializers.CharField(
        source="attribute_value.attribute.name",
        read_only=True,
    )
    value = serializers.CharField(
        source="attribute_value.value",
        read_only=True,
    )

    class Meta:
        model = ProductVariantAttributeValueModel
        fields = [
            "id",
            "variant",
            "attribute_value",
            "attribute",
            "value",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        instance = ProductVariantAttributeValueModel(**attrs)

        try:
            instance.clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict if hasattr(
                error, "message_dict") else error.messages)

        return attrs


class ProductVariantSerializer(serializers.ModelSerializer):
    attribute_items = ProductVariantAttributeValueSerializer(
        source="variant_attribute_values",
        many=True,
        read_only=True,
    )

    available_stock = serializers.IntegerField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)

    price_toman = serializers.IntegerField(read_only=True)
    compare_at_price_toman = serializers.IntegerField(read_only=True)
    cost_price_toman = serializers.IntegerField(read_only=True)

    has_discount = serializers.BooleanField(read_only=True)
    discount_amount_rial = serializers.IntegerField(read_only=True)
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
            "cost_price_rial",
            "cost_price_toman",
            "stock",
            "reserved_stock",
            "available_stock",
            "is_in_stock",
            "is_active",
            "sort_order",
            "attributes_snapshot",
            "attribute_items",
            "weight_grams",
            "has_discount",
            "discount_amount_rial",
            "discount_percent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "display_name",
            "attributes_snapshot",
            "available_stock",
            "is_in_stock",
            "price_toman",
            "compare_at_price_toman",
            "cost_price_toman",
            "has_discount",
            "discount_amount_rial",
            "discount_percent",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        instance = ProductVariantModel(**attrs)

        if self.instance:
            for field, value in attrs.items():
                setattr(instance, field, value)

        try:
            instance.clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict if hasattr(
                error, "message_dict") else error.messages)

        return attrs


class ProductVariantCreateUpdateSerializer(serializers.ModelSerializer):
    attribute_value_ids = serializers.PrimaryKeyRelatedField(
        queryset=ProductAttributeValueModel.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = ProductVariantModel
        fields = [
            "id",
            "product",
            "sku",
            "price_rial",
            "compare_at_price_rial",
            "cost_price_rial",
            "stock",
            "reserved_stock",
            "is_active",
            "sort_order",
            "weight_grams",
            "attribute_value_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        instance = self.instance or ProductVariantModel()

        for field, value in attrs.items():
            if field != "attribute_value_ids":
                setattr(instance, field, value)

        try:
            instance.clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict if hasattr(
                error, "message_dict") else error.messages)

        return attrs

    def create(self, validated_data):
        attribute_values = validated_data.pop("attribute_value_ids", [])
        variant = ProductVariantModel.objects.create(**validated_data)

        for attribute_value in attribute_values:
            ProductVariantAttributeValueModel.objects.create(
                variant=variant,
                attribute_value=attribute_value,
            )

        return variant

    def update(self, instance, validated_data):
        attribute_values = validated_data.pop("attribute_value_ids", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if attribute_values is not None:
            instance.variant_attribute_values.all().delete()

            for attribute_value in attribute_values:
                ProductVariantAttributeValueModel.objects.create(
                    variant=instance,
                    attribute_value=attribute_value,
                )

        return instance


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name", read_only=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True)
    primary_image = serializers.SerializerMethodField()
    default_variant = serializers.SerializerMethodField()

    class Meta:
        model = ProductModel
        fields = [
            "id",
            "category",
            "category_name",
            "brand",
            "brand_name",
            "name",
            "slug",
            "short_description",
            "status",
            "is_active",
            "is_featured",
            "primary_image",
            "default_variant",
            "created_at",
            "updated_at",
            "published_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def get_primary_image(self, obj):
        image = obj.images.filter(is_primary=True).first()

        if not image:
            image = obj.images.order_by("sort_order", "id").first()

        if not image or not image.image:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(image.image.url)

        return image.image.url

    def get_default_variant(self, obj):
        variant = obj.default_variant

        if not variant:
            return None

        return {
            "id": variant.id,
            "sku": variant.sku,
            "display_name": variant.display_name,
            "price_rial": variant.price_rial,
            "price_toman": variant.price_toman,
            "compare_at_price_rial": variant.compare_at_price_rial,
            "compare_at_price_toman": variant.compare_at_price_toman,
            "available_stock": variant.available_stock,
            "is_in_stock": variant.is_in_stock,
            "has_discount": variant.has_discount,
            "discount_amount_rial": variant.discount_amount_rial,
            "discount_percent": variant.discount_percent,
            "attributes_snapshot": variant.attributes_snapshot,
        }


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=CategoryModel.objects.all(),
        source="category",
        write_only=True,
    )
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=BrandModel.objects.all(),
        source="brand",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ProductModel
        fields = [
            "id",
            "category",
            "category_id",
            "brand",
            "brand_id",
            "name",
            "slug",
            "short_description",
            "description",
            "status",
            "is_active",
            "is_featured",
            "meta_title",
            "meta_description",
            "images",
            "specifications",
            "variants",
            "created_at",
            "updated_at",
            "published_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]
