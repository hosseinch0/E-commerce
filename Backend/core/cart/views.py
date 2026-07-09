from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view
)
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CartModel, CartItemModel, CartStatus
from .serializers import (
    AddCartItemSerializer,
    AdminCartSerializer,
    CartItemSerializer,
    CartSerializer,
    UpdateCartItemSerializer,
)
from .services import clear_cart, get_or_create_active_cart


@extend_schema_view(
    get=extend_schema(
        tags=["Cart"],
        summary="Retrieve current user's cart",
        description="Returns the authenticated user's active cart with variant items, quantities, prices, and totals.",
        responses={200: CartSerializer},
    )
)
class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = get_or_create_active_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(
        tags=["Cart"],
        summary="Add variant to cart",
        description="Adds a product variant to the authenticated user's active cart. If the variant already exists, its quantity is increased.",
        request=AddCartItemSerializer,
        responses={
            201: CartItemSerializer,
            400: OpenApiResponse(description="Invalid variant, quantity, or insufficient stock."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
        },
    )
)
class CartItemCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddCartItemSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        item = serializer.save()

        return Response(
            CartItemSerializer(item).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    patch=extend_schema(
        tags=["Cart"],
        summary="Update cart item quantity",
        description="Updates the quantity of a cart item owned by the authenticated user.",
        request=UpdateCartItemSerializer,
        responses={
            200: CartItemSerializer,
            400: OpenApiResponse(description="Invalid quantity or insufficient stock."),
            404: OpenApiResponse(description="Cart item not found."),
        },
    ),
    delete=extend_schema(
        tags=["Cart"],
        summary="Remove cart item",
        description="Removes a variant from the authenticated user's active cart.",
        responses={
            204: OpenApiResponse(description="Cart item removed successfully."),
            404: OpenApiResponse(description="Cart item not found."),
        },
    ),
)
class CartItemDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_item(self, request, item_id):
        return generics.get_object_or_404(
            CartItemModel.objects.select_related(
                "cart",
                "variant",
                "variant__product",
            ),
            id=item_id,
            cart__user=request.user,
            cart__status=CartStatus.ACTIVE,
        )

    def patch(self, request, item_id):
        item = self.get_item(request, item_id)

        serializer = UpdateCartItemSerializer(
            data=request.data,
            context={"item": item},
        )
        serializer.is_valid(raise_exception=True)
        item = serializer.save()

        return Response(
            CartItemSerializer(item).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, item_id):
        item = self.get_item(request, item_id)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    delete=extend_schema(
        tags=["Cart"],
        summary="Clear current user's cart",
        description="Removes all items from the authenticated user's active cart.",
        responses={
            204: OpenApiResponse(description="Cart cleared successfully."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
        },
    )
)
class CartClearAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart = get_or_create_active_cart(request.user)
        clear_cart(cart)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    get=extend_schema(
        tags=["Admin Cart"],
        summary="List carts",
        description="Admin endpoint for listing customer carts. Supports filtering by cart status.",
        parameters=[
            OpenApiParameter(
                name="status",
                required=False,
                type=str,
                description="Filter by cart status: active, checked_out, abandoned.",
            ),
        ],
        responses={200: AdminCartSerializer(many=True)},
    )
)
class AdminCartListAPIView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminCartSerializer

    def get_queryset(self):
        queryset = CartModel.objects.select_related("user").prefetch_related(
            "items__variant__product",
        )

        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset


@extend_schema_view(
    get=extend_schema(
        tags=["Admin Cart"],
        summary="Retrieve cart details",
        description="Admin endpoint for retrieving one cart with customer and item details.",
        responses={
            200: AdminCartSerializer,
            404: OpenApiResponse(description="Cart not found."),
        },
    )
)
class AdminCartDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminCartSerializer
    lookup_url_kwarg = "cart_id"

    def get_queryset(self):
        return CartModel.objects.select_related("user").prefetch_related(
            "items__variant__product",
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Admin Cart"],
        summary="List carts for a user",
        description="Admin endpoint for retrieving all carts belonging to a specific user.",
        responses={200: AdminCartSerializer(many=True)},
    )
)
class AdminUserCartListAPIView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminCartSerializer

    def get_queryset(self):
        return CartModel.objects.select_related("user").prefetch_related(
            "items__variant__product",
        ).filter(user_id=self.kwargs["user_id"])
