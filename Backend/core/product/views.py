from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import ProductModel, ProductVariantModel
from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductVariantSerializer,
    ProductVariantCreateUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List products",
        description="Returns a list of products with basic product information.",
        responses=ProductListSerializer,
        tags=["Products"],
    ),
    retrieve=extend_schema(
        summary="Retrieve product details",
        description="Returns detailed information for a single product.",
        responses=ProductDetailSerializer,
        tags=["Products"],
    ),
    create=extend_schema(
        summary="Create product",
        description="Creates a new product.",
        request=ProductDetailSerializer,
        responses=ProductDetailSerializer,
        tags=["Products"],
    ),
    update=extend_schema(
        summary="Update product",
        description="Updates an existing product.",
        request=ProductDetailSerializer,
        responses=ProductDetailSerializer,
        tags=["Products"],
    ),
    partial_update=extend_schema(
        summary="Partially update product",
        description="Partially updates an existing product.",
        request=ProductDetailSerializer,
        responses=ProductDetailSerializer,
        tags=["Products"],
    ),
    destroy=extend_schema(
        summary="Delete product",
        description="Deletes an existing product.",
        tags=["Products"],
    ),
)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = (
        ProductModel.objects
        .select_related("category", "brand")
        .prefetch_related(
            "images",
            "specifications",
            "variants",
            "variants__variant_attribute_values__attribute_value__attribute",
        )
    )

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductDetailSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List product variants",
        description="Returns a list of product variants.",
        responses=ProductVariantSerializer,
        tags=["Product Variants"],
    ),
    retrieve=extend_schema(
        summary="Retrieve product variant details",
        description="Returns detailed information for a single product variant.",
        responses=ProductVariantSerializer,
        tags=["Product Variants"],
    ),
    create=extend_schema(
        summary="Create product variant",
        description="Creates a new product variant.",
        request=ProductVariantCreateUpdateSerializer,
        responses=ProductVariantSerializer,
        tags=["Product Variants"],
    ),
    update=extend_schema(
        summary="Update product variant",
        description="Updates an existing product variant.",
        request=ProductVariantCreateUpdateSerializer,
        responses=ProductVariantSerializer,
        tags=["Product Variants"],
    ),
    partial_update=extend_schema(
        summary="Partially update product variant",
        description="Partially updates an existing product variant.",
        request=ProductVariantCreateUpdateSerializer,
        responses=ProductVariantSerializer,
        tags=["Product Variants"],
    ),
    destroy=extend_schema(
        summary="Delete product variant",
        description="Deletes an existing product variant.",
        tags=["Product Variants"],
    ),
)
class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = (
        ProductVariantModel.objects
        .select_related("product", "product__category", "product__brand")
        .prefetch_related("variant_attribute_values__attribute_value__attribute")
    )

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProductVariantCreateUpdateSerializer
        return ProductVariantSerializer
