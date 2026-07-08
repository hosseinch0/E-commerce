from django.contrib import admin

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


class ProductImageInline(admin.TabularInline):
    model = ProductImageModel
    extra = 1
    fields = ["image", "alt_text", "is_primary", "sort_order"]


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecificationModel
    extra = 1
    fields = ["key", "value", "sort_order"]


class ProductVariantInline(admin.TabularInline):
    model = ProductVariantModel
    extra = 0
    fields = [
        "sku",
        "display_name",
        "price_rial",
        "compare_at_price_rial",
        "stock",
        "reserved_stock",
        "is_active",
        "sort_order",
    ]
    readonly_fields = ["display_name"]


class ProductVariantAttributeValueInline(admin.TabularInline):
    model = ProductVariantAttributeValueModel
    extra = 1
    fields = ["attribute_value"]


@admin.register(CategoryModel)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    autocomplete_fields = ["parent"]
    ordering = ["name"]


@admin.register(BrandModel)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    ordering = ["name"]


@admin.register(ProductModel)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category",
        "brand",
        "status",
        "is_active",
        "is_featured",
        "created_at",
    ]
    list_filter = [
        "status",
        "is_active",
        "is_featured",
        "category",
        "brand",
        "created_at",
    ]
    search_fields = ["name", "slug", "short_description"]
    prepopulated_fields = {"slug": ["name"]}
    autocomplete_fields = ["category", "brand"]
    readonly_fields = ["id", "created_at", "updated_at"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]
    inlines = [
        ProductImageInline,
        ProductSpecificationInline,
        ProductVariantInline,
    ]

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "id",
                "category",
                "brand",
                "name",
                "slug",
                "short_description",
                "description",
            )
        }),
        ("Status", {
            "fields": (
                "status",
                "is_active",
                "is_featured",
                "published_at",
            )
        }),
        ("SEO", {
            "fields": (
                "meta_title",
                "meta_description",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )


@admin.register(ProductImageModel)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ["product", "image", "is_primary", "sort_order"]
    list_filter = ["is_primary"]
    search_fields = ["product__name", "alt_text"]
    autocomplete_fields = ["product"]
    ordering = ["product", "sort_order"]


@admin.register(ProductAttributeModel)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    ordering = ["name"]


@admin.register(ProductAttributeValueModel)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ["attribute", "value", "slug"]
    list_filter = ["attribute"]
    search_fields = ["attribute__name", "value", "slug"]
    prepopulated_fields = {"slug": ["value"]}
    autocomplete_fields = ["attribute"]
    ordering = ["attribute__name", "value"]


@admin.register(ProductSpecificationModel)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ["product", "key", "value", "sort_order"]
    search_fields = ["product__name", "key", "value"]
    autocomplete_fields = ["product"]
    ordering = ["product", "sort_order"]


@admin.register(ProductVariantModel)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = [
        "sku",
        "product",
        "display_name",
        "price_rial",
        "price_toman",
        "stock",
        "reserved_stock",
        "available_stock",
        "is_active",
    ]
    list_filter = ["is_active", "product__category", "product__brand"]
    search_fields = ["sku", "product__name", "display_name"]
    autocomplete_fields = ["product"]
    readonly_fields = [
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
    ordering = ["product", "sort_order", "id"]
    inlines = [ProductVariantAttributeValueInline]

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "product",
                "sku",
                "display_name",
                "is_active",
                "sort_order",
            )
        }),
        ("Pricing", {
            "fields": (
                "price_rial",
                "price_toman",
                "compare_at_price_rial",
                "compare_at_price_toman",
                "cost_price_rial",
                "cost_price_toman",
                "has_discount",
                "discount_amount_rial",
                "discount_percent",
            )
        }),
        ("Inventory", {
            "fields": (
                "stock",
                "reserved_stock",
                "available_stock",
                "is_in_stock",
            )
        }),
        ("Shipping", {
            "fields": (
                "weight_grams",
            )
        }),
        ("Cached Attributes", {
            "fields": (
                "attributes_snapshot",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )


@admin.register(ProductVariantAttributeValueModel)
class ProductVariantAttributeValueAdmin(admin.ModelAdmin):
    list_display = ["variant", "attribute_value", "get_attribute"]
    list_filter = ["attribute_value__attribute"]
    search_fields = [
        "variant__sku",
        "variant__product__name",
        "attribute_value__attribute__name",
        "attribute_value__value",
    ]
    autocomplete_fields = ["variant", "attribute_value"]

    @admin.display(description="Attribute")
    def get_attribute(self, obj):
        return obj.attribute_value.attribute.name
