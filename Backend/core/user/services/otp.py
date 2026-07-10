import secrets

from django.db import transaction
from django.utils import timezone

from user.models import PhoneOTPModel
from user.services.sms import send_otp_sms


OTP_CODE_LENGTH = 6


def generate_otp_code():
    lower_bound = 10 ** (OTP_CODE_LENGTH - 1)
    available_values = 9 * lower_bound
    return str(lower_bound + secrets.randbelow(available_values))


@transaction.atomic
def issue_and_send_otp(phone_number, purpose, user=None):
    """
    Invalidate active OTPs for the same phone number and purpose,
    create a new OTP, and send it after the transaction commits.

    Sending after commit prevents delivering a code whose database
    transaction is later rolled back.
    """
    now = timezone.now()

    active_otps = PhoneOTPModel.objects.select_for_update().filter(
        phone_number=phone_number,
        purpose=purpose,
        is_used=False,
        expires_at__gt=now,
    )

    active_otps.update(is_used=True)

    code = generate_otp_code()

    otp = PhoneOTPModel.objects.create(
        user=user,
        phone_number=phone_number,
        purpose=purpose,
        expires_at=PhoneOTPModel.new_expiry(),
    )
    otp.set_code(code)
    otp.save(update_fields=["code_hash"])

    transaction.on_commit(
        lambda phone_number=phone_number, code=code: send_otp_sms(
            phone_number=phone_number,
            code=code,
        )
    )

    return otp
