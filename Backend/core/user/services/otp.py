import random

from user.models import PhoneOTPModel
from user.services.sms import send_otp_sms


def generate_otp_code():
    return str(random.randint(100000, 999999))


def issue_and_send_otp(phone_number, purpose, user=None):
    code = generate_otp_code()

    otp = PhoneOTPModel.objects.create(
        user=user,
        phone_number=phone_number,
        purpose=purpose,
        expires_at=PhoneOTPModel.new_expiry(),
    )
    otp.set_code(code)
    otp.save(update_fields=["code_hash"])

    send_otp_sms(phone_number=phone_number, code=code)
    return otp
