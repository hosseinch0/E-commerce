from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from order.models import OrderModel

from .models import PaymentModel
from .serializers import PaymentSerializer
from .services import PaymentError, create_payment_request, verify_payment


@extend_schema(
    tags=["Payments"],
    summary="List user payments",
    description=(
        "Returns the authenticated user's payment history. "
        "Each payment is connected to an order and includes gateway, amount, "
        "status, authority, reference id, and timestamps."
    ),
    responses={
        200: PaymentSerializer(many=True),
        401: OpenApiResponse(description="Authentication credentials were not provided."),
    },
)
class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PaymentModel.objects.filter(
            user=self.request.user
        ).select_related("order")


@extend_schema(
    tags=["Payments"],
    summary="Retrieve payment detail",
    description=(
        "Returns details of a single payment owned by the authenticated user. "
        "Users cannot access payments that belong to other users."
    ),
    responses={
        200: PaymentSerializer,
        401: OpenApiResponse(description="Authentication credentials were not provided."),
        404: OpenApiResponse(description="Payment not found."),
    },
)
class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "payment_id"

    def get_queryset(self):
        return PaymentModel.objects.filter(
            user=self.request.user
        ).select_related("order")


@extend_schema(
    tags=["Payments"],
    summary="Create payment request for order",
    description=(
        "Creates a new payment request for an order owned by the authenticated user. "
        "The payment amount is calculated from the server-side order total, not from "
        "client input. If the order is payable, the API returns a payment id and a "
        "gateway payment URL."
    ),
    parameters=[
        OpenApiParameter(
            name="order_id",
            type=str,
            location=OpenApiParameter.PATH,
            required=True,
            description="UUID of the order that should be paid.",
        ),
    ],
    request=None,
    responses={
        201: OpenApiResponse(
            description="Payment request created successfully.",
            response={
                "type": "object",
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "format": "uuid",
                        "example": "44d64eb1-5e92-4d16-a7e9-188f77fef58e",
                    },
                    "payment_url": {
                        "type": "string",
                        "format": "uri",
                        "example": "http://localhost:8000/api/payments/verify/?Authority=AUTHORITY&Status=OK",
                    },
                },
            },
        ),
        400: OpenApiResponse(
            description=(
                "Payment cannot be created. Possible reasons: order is not payable, "
                "order amount is invalid, or order has already been paid."
            )
        ),
        401: OpenApiResponse(description="Authentication credentials were not provided."),
        404: OpenApiResponse(description="Order not found."),
    },
)
class CreatePaymentRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = OrderModel.objects.get(id=order_id, user=request.user)
        except OrderModel.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            result = create_payment_request(order=order, user=request.user)
        except PaymentError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = result["payment"]

        return Response(
            {
                "payment_id": payment.id,
                "payment_url": result["payment_url"],
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Payments"],
    summary="Verify payment callback",
    description=(
        "Verifies a payment after the payment gateway redirects back to the backend. "
        "The gateway sends an Authority and Status. If verification succeeds, the "
        "payment status becomes success and the related order status becomes paid. "
        "If verification fails or the user cancels payment, the payment is marked as failed."
    ),
    parameters=[
        OpenApiParameter(
            name="Authority",
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Gateway authority/token returned during payment request creation.",
        ),
        OpenApiParameter(
            name="Status",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description=(
                "Gateway result status. For sandbox flow, use `OK` for successful payment. "
                "Any other value is treated as failed/cancelled."
            ),
        ),
    ],
    responses={
        200: PaymentSerializer,
        400: OpenApiResponse(
            description="Invalid callback data, missing Authority, or payment not found."
        ),
    },
)
class VerifyPaymentView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        authority = request.query_params.get("Authority")
        gateway_status = request.query_params.get("Status")

        if not authority:
            return Response(
                {"detail": "Authority is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = verify_payment(
                authority=authority,
                status=gateway_status,
            )
        except PaymentError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PaymentSerializer(payment)

        return Response(serializer.data, status=status.HTTP_200_OK)
