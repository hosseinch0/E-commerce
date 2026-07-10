from hashlib import sha256

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.exceptions import ValidationError
from rest_framework.throttling import SimpleRateThrottle


class IPThrottle(SimpleRateThrottle):
    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class PhoneNumberThrottle(SimpleRateThrottle):
    phone_field = PhoneNumberField()

    def get_cache_key(self, request, view):
        raw_phone_number = request.data.get("phone_number")

        if not raw_phone_number:
            return None

        try:
            phone_number = self.phone_field.run_validation(raw_phone_number)
            normalized_phone = str(phone_number)
        except ValidationError:
            normalized_phone = str(raw_phone_number).strip()

        identifier = sha256(normalized_phone.encode()).hexdigest()

        return self.cache_format % {
            "scope": self.scope,
            "ident": identifier,
        }


class OTPSendIPThrottle(IPThrottle):
    scope = "otp_send_ip"


class OTPSendPhoneThrottle(PhoneNumberThrottle):
    scope = "otp_send_phone"


class OTPVerifyIPThrottle(IPThrottle):
    scope = "otp_verify_ip"


class OTPVerifyPhoneThrottle(PhoneNumberThrottle):
    scope = "otp_verify_phone"
