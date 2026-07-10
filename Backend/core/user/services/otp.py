import secrets
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from user.models import PhoneOTPModel
from user.services.sms import send_otp_sms

User = get_user_model()

OTP_CODE_LENGTH = 6
MAX_OTP_ATTEMPTS = 5


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


class OTPVerificationError(Exception):
    pass


class OTPNotFoundError(OTPVerificationError):
    pass


class OTPExpiredError(OTPVerificationError):
    pass


class OTPMaxAttemptsError(OTPVerificationError):
    pass


class OTPInvalidCodeError(OTPVerificationError):
    pass


class OTPGenericError(OTPVerificationError):
    pass


def consume_otp(phone_number, purpose, code):
    verification_error = None
    user = None

    try:
        with transaction.atomic():
            otp = (
                PhoneOTPModel.objects.select_for_update()
                .select_related("user")
                .filter(
                    phone_number=phone_number,
                    purpose=purpose,
                    is_used=False,
                )
                .order_by("-created_at")
                .first()
            )

            if otp is None:
                verification_error = OTPNotFoundError()

            elif otp.expires_at <= timezone.now():
                otp.is_used = True
                otp.save(update_fields=["is_used"])
                verification_error = OTPExpiredError()

            elif otp.attempts >= MAX_OTP_ATTEMPTS:
                otp.is_used = True
                otp.save(update_fields=["is_used"])
                verification_error = OTPMaxAttemptsError()

            elif not otp.check_code(code):
                otp.attempts += 1
                update_fields = ["attempts"]

                if otp.attempts >= MAX_OTP_ATTEMPTS:
                    otp.is_used = True
                    update_fields.append("is_used")
                    verification_error = OTPMaxAttemptsError()
                else:
                    verification_error = OTPInvalidCodeError()

                otp.save(update_fields=update_fields)

            else:
                if purpose == PhoneOTPModel.Purpose.SIGNUP:
                    if otp.user_id:
                        user = otp.user
                    else:
                        user = User.objects.create_user(
                            phone_number=otp.phone_number
                        )
                        otp.user = user

                elif purpose in (
                    PhoneOTPModel.Purpose.LOGIN,
                    PhoneOTPModel.Purpose.PASSWORD_RESET,
                ):
                    user = otp.user

                    if user is None:
                        raise OTPGenericError(
                            "OTP has no associated user."
                        )

                else:
                    raise OTPGenericError("Unsupported OTP purpose.")

                otp.is_used = True
                otp.save(update_fields=["user", "is_used"])

    except OTPVerificationError:
        raise
    except Exception as exc:
        raise OTPGenericError(
            "OTP verification could not be completed."
        ) from exc

    # Raise after atomic() commits attempt/expiry changes.
    if verification_error is not None:
        raise verification_error

    return user
