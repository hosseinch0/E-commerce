from rest_framework import generics, status
from rest_framework.response import Response
from .models import OrderModel
from .serializers import OrderSerializer
from .services import create_order_from_cart
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view


@extend_schema_view(
    get=extend_schema(
        tags=["Orders"],
        summary="List user orders",
        description=(
            "Returns the authenticated user's orders. "
            "Each order includes its current status, total amount, timestamps, "
            "and order item snapshots depending on the OrderSerializer structure."
        ),
        responses={
            200: OrderSerializer(many=True),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
        },
    ),
    post=extend_schema(
        tags=["Orders"],
        summary="Create order from cart",
        description=(
            "Creates a new order from the authenticated user's current cart. "
            "The backend reads cart items, creates order item snapshots, calculates "
            "the order total on the server side, and returns the created order. "
            "The client does not send product prices, quantities, or total amount in "
            "the request body for this endpoint."
        ),
        request=None,
        responses={
            201: OrderSerializer,
            400: OpenApiResponse(
                description=(
                    "Order could not be created. Possible reasons include empty cart, "
                    "invalid cart items, unavailable product variants, or insufficient stock."
                )
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
        },
    ),
)
class OrderListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return OrderModel.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        order = create_order_from_cart(request.user)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
