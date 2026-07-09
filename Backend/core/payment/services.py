import uuid

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from order.models import OrderModel, OrderStatus

from .models import PaymentGateway, PaymentModel, PaymentStatus


class PaymentError(Exception):
    pass


def create_payment_request(*, order: OrderModel, user):
    if order.user_id != user.id:
        raise PaymentError("You cannot pay for this order.")

    if order.status not in [OrderStatus.PLACED, OrderStatus.PENDING]:
        raise PaymentError("This order is not payable.")

    if order.total_amount_rial <= 0:
        raise PaymentError("Order amount is invalid.")

    existing_success_payment = order.payments.filter(
        status=PaymentStatus.SUCCESS
    ).exists()

    if existing_success_payment:
        raise PaymentError("This order is already paid.")

    with transaction.atomic():
        payment = PaymentModel.objects.create(
            order=order,
            user=user,
            amount_rial=order.total_amount_rial,
            gateway=PaymentGateway.SANDBOX,
            status=PaymentStatus.PENDING,
        )

        authority = str(uuid.uuid4())

        payment.authority = authority
        payment.request_payload = {
            "gateway": PaymentGateway.SANDBOX,
            "amount_rial": payment.amount_rial,
            "authority": authority,
        }
        payment.save(update_fields=["authority",
                     "request_payload", "updated_at"])

    callback_url = getattr(
        settings,
        "PAYMENT_SANDBOX_CALLBACK_URL",
        "http://localhost:8000/api/payments/verify/",
    )

    payment_url = f"{callback_url}?Authority={payment.authority}&Status=OK"

    return {
        "payment": payment,
        "payment_url": payment_url,
    }


@transaction.atomic
def verify_payment(*, authority: str, status: str):
    try:
        payment = (
            PaymentModel.objects
            .select_for_update()
            .select_related("order")
            .get(authority=authority)
        )
    except PaymentModel.DoesNotExist:
        raise PaymentError("Payment not found.")

    if payment.status == PaymentStatus.SUCCESS:
        return payment

    if status != "OK":
        payment.status = PaymentStatus.FAILED
        payment.error_code = status
        payment.error_message = "Payment was cancelled or failed by gateway."
        payment.verify_payload = {
            "authority": authority,
            "status": status,
        }
        payment.save(
            update_fields=[
                "status",
                "error_code",
                "error_message",
                "verify_payload",
                "updated_at",
            ]
        )

        payment.order.status = OrderStatus.FAILED
        payment.order.save(update_fields=["status", "updated_at"])

        return payment

    ref_id = f"SANDBOX-{uuid.uuid4()}"

    payment.status = PaymentStatus.SUCCESS
    payment.ref_id = ref_id
    payment.paid_at = timezone.now()
    payment.verify_payload = {
        "authority": authority,
        "status": status,
        "ref_id": ref_id,
    }
    payment.save(
        update_fields=[
            "status",
            "ref_id",
            "paid_at",
            "verify_payload",
            "updated_at",
        ]
    )

    payment.order.status = OrderStatus.PAID
    payment.order.save(update_fields=["status", "updated_at"])

    return payment
