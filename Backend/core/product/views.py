from rest_framework import mixins, permissions, viewsets

from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from .models import ProductModel, ProductVariantModel
from .serializers import (
    ProductDetailSerializer,
    ProductListSerializer,
    ProductVariantCreateUpdateSerializer,
    ProductVariantSerializer,
)


PRODUCT_QUERYSET = (
    ProductModel.objects
    .select_related("category", "brand")
    .prefetch_related(
        "images",
        "specifications",
        "variants",
        "variants__variant_attribute_values__attribute_value__attribute",
    )
)

PRODUCT_VARIANT_QUERYSET = (
    ProductVariantModel.objects
    .select_related("product", "product__category", "product__brand")
    .prefetch_related("variant_attribute_values__attribute_value__attribute")
)


@extend_schema_view(
    list=extend_schema(
        summary="List products",
        description="Returns a list of products with basic product information.",
        responses={
            200: ProductListSerializer(many=True),
        },
        tags=["Products"],
    ),
    retrieve=extend_schema(
        summary="Retrieve product",
        description="Returns detailed information for a single product.",
        responses={
            200: ProductDetailSerializer,
            404: OpenApiResponse(description="Product not found."),
        },
        tags=["Products"],
    ),
)
class ProductViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = PRODUCT_QUERYSET
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get", "head", "options"]

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer

        return ProductDetailSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List product variants",
        description="Returns a list of product variants.",
        responses={
            200: ProductVariantSerializer(many=True),
        },
        tags=["Product Variants"],
    ),
    retrieve=extend_schema(
        summary="Retrieve product variant",
        description="Returns detailed information for a single product variant.",
        responses={
            200: ProductVariantSerializer,
            404: OpenApiResponse(description="Product variant not found."),
        },
        tags=["Product Variants"],
    ),
)
class ProductVariantViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = PRODUCT_VARIANT_QUERYSET
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get", "head", "options"]


@extend_schema_view(
    list=extend_schema(
        summary="List products",
        description="Admin-only endpoint for listing products.",
        responses={
            200: ProductListSerializer(many=True),
        },
        tags=["Admin Products"],
    ),
    create=extend_schema(
        summary="Create product",
        description="Admin-only endpoint for creating a product.",
        request=ProductDetailSerializer,
        responses={
            201: ProductDetailSerializer,
            400: OpenApiResponse(description="Invalid product data."),
        },
        tags=["Admin Products"],
    ),
    retrieve=extend_schema(
        summary="Retrieve product",
        description="Admin-only endpoint for retrieving a product.",
        responses={
            200: ProductDetailSerializer,
            404: OpenApiResponse(description="Product not found."),
        },
        tags=["Admin Products"],
    ),
    update=extend_schema(
        summary="Update product",
        description="Admin-only endpoint for fully updating a product.",
        request=ProductDetailSerializer,
        responses={
            200: ProductDetailSerializer,
            400: OpenApiResponse(description="Invalid product data."),
            404: OpenApiResponse(description="Product not found."),
        },
        tags=["Admin Products"],
    ),
    partial_update=extend_schema(
        summary="Partially update product",
        description="Admin-only endpoint for partially updating a product.",
        request=ProductDetailSerializer,
        responses={
            200: ProductDetailSerializer,
            400: OpenApiResponse(description="Invalid product data."),
            404: OpenApiResponse(description="Product not found."),
        },
        tags=["Admin Products"],
    ),
    destroy=extend_schema(
        summary="Delete product",
        description="Admin-only endpoint for deleting a product.",
        responses={
            204: None,
            404: OpenApiResponse(description="Product not found."),
        },
        tags=["Admin Products"],
    ),
)
class AdminProductViewSet(viewsets.ModelViewSet):
    queryset = PRODUCT_QUERYSET
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ["get", "post", "put",
                         "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer

        return ProductDetailSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List product variants",
        description="Admin-only endpoint for listing product variants.",
        responses={
            200: ProductVariantSerializer(many=True),
        },
        tags=["Admin Product Variants"],
    ),
    create=extend_schema(
        summary="Create product variant",
        description="Admin-only endpoint for creating a product variant.",
        request=ProductVariantCreateUpdateSerializer,
        responses={
            201: ProductVariantSerializer,
            400: OpenApiResponse(description="Invalid product variant data."),
        },
        tags=["Admin Product Variants"],
    ),
    retrieve=extend_schema(
        summary="Retrieve product variant",
        description="Admin-only endpoint for retrieving a product variant.",
        responses={
            200: ProductVariantSerializer,
            404: OpenApiResponse(description="Product variant not found."),
        },
        tags=["Admin Product Variants"],
    ),
    update=extend_schema(
        summary="Update product variant",
        description="Admin-only endpoint for fully updating a product variant.",
        request=ProductVariantCreateUpdateSerializer,
        responses={
            200: ProductVariantSerializer,
            400: OpenApiResponse(description="Invalid product variant data."),
            404: OpenApiResponse(description="Product variant not found."),
        },
        tags=["Admin Product Variants"],
    ),
    partial_update=extend_schema(
        summary="Partially update product variant",
        description="Admin-only endpoint for partially updating a product variant.",
        request=ProductVariantCreateUpdateSerializer,
        responses={
            200: ProductVariantSerializer,
            400: OpenApiResponse(description="Invalid product variant data."),
            404: OpenApiResponse(description="Product variant not found."),
        },
        tags=["Admin Product Variants"],
    ),
    destroy=extend_schema(
        summary="Delete product variant",
        description="Admin-only endpoint for deleting a product variant.",
        responses={
            204: None,
            404: OpenApiResponse(description="Product variant not found."),
        },
        tags=["Admin Product Variants"],
    ),
)
class AdminProductVariantViewSet(viewsets.ModelViewSet):
    queryset = PRODUCT_VARIANT_QUERYSET
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ["get", "post", "put",
                         "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProductVariantCreateUpdateSerializer

        return ProductVariantSerializer
