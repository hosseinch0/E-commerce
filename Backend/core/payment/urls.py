from django.urls import path

from .views import (
    CreatePaymentRequestView,
    PaymentDetailView,
    PaymentListView,
    VerifyPaymentView,
)

urlpatterns = [
    path("", PaymentListView.as_view(), name="payment-list"),
    path("<uuid:payment_id>/",
         PaymentDetailView.as_view(), name="payment-detail"),
    path(
        "orders/<uuid:order_id>/request/",
        CreatePaymentRequestView.as_view(),
        name="payment-request",
    ),
    path("verify/", VerifyPaymentView.as_view(), name="payment-verify"),
]
