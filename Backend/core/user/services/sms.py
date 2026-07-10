import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


logger = logging.getLogger(__name__)


def mask_phone_number(phone_number):
    value = str(phone_number)

    if len(value) <= 4:
        return "*" * len(value)

    return f"{'*' * (len(value) - 4)}{value[-4:]}"


def send_otp_sms(phone_number, code):
    """
    Send an OTP through the configured backend.

    Development:
        When DEBUG=True and SMS_OTP_BACKEND is not configured, the OTP is
        printed to the console for local testing.

    Production:
        SMS_OTP_BACKEND must contain the dotted path to a callable accepting
        keyword arguments named ``phone_number`` and ``code``.
    """
    backend_path = getattr(settings, "SMS_OTP_BACKEND", None)
    masked_phone = mask_phone_number(phone_number)

    if backend_path:
        if backend_path == "user.services.sms.send_otp_sms":
            raise ImproperlyConfigured(
                "SMS_OTP_BACKEND cannot point to send_otp_sms itself."
            )

        backend = import_string(backend_path)

        try:
            result = backend(
                phone_number=phone_number,
                code=code,
            )
        except Exception:
            logger.exception(
                "OTP SMS delivery failed for phone number %s.",
                masked_phone,
            )
            raise

        logger.info(
            "OTP SMS submitted for phone number %s.",
            masked_phone,
        )
        return result

    if settings.DEBUG:
        logger.warning(
            "Using the development SMS backend for phone number %s.",
            masked_phone,
        )
        print(f"Development OTP for {masked_phone}: {code}")
        return True

    raise ImproperlyConfigured(
        "SMS_OTP_BACKEND must be configured when DEBUG=False."
    )
