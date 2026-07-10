from .models import PhoneOTPModel
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from phonenumber_field.serializerfields import PhoneNumberField

from drf_spectacular.utils import (
    inline_serializer,
)
User = get_user_model()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.refresh = attrs["refresh"]
        return attrs

    def save(self, **kwargs):
        request = self.context["request"]

        try:
            token = RefreshToken(self.refresh)

            user_id = str(token["user_id"])
            if user_id != str(request.user.id):
                raise serializers.ValidationError(
                    {"refresh": "This token does not belong to the authenticated user."}
                )

            token.blacklist()
        except TokenError:
            raise serializers.ValidationError(
                {"refresh": "Invalid or expired refresh token."}
            )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
            "date_joined",
            "last_login",
        ]
        read_only_fields = [
            "id",
            "is_active",
            "is_staff",
            "date_joined",
            "last_login",
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "email",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.pop("password_confirm", None)

        if password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            **validated_data,
        )

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "first_name",
            "last_name",
            "email",
        ]
        read_only_fields = ["id", "phone_number"]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    def validate_old_password(self, value):
        user = self.context["request"].user

        if not user.has_usable_password():
            raise serializers.ValidationError(
                "You have not set a password yet. Please use set-password first."
            )

        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")

        return value

    def validate(self, attrs):
        new_password = attrs.get("new_password")
        new_password_confirm = attrs.get("new_password_confirm")

        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )

        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])

        return user


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        user = self.context["request"].user

        if user.has_usable_password():
            raise serializers.ValidationError(
                "You already have a password. Please use change-password instead."
            )

        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )

        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class PhoneOTPSerializer(serializers.ModelSerializer):
    user_phone_number = serializers.CharField(
        source="user.phone_number",
        read_only=True,
    )
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = PhoneOTPModel
        fields = [
            "id",
            "user",
            "user_phone_number",
            "phone_number",
            "created_at",
            "expires_at",
            "attempts",
            "is_used",
            "is_expired",
            "purpose",
        ]
        read_only_fields = [
            "id",
            "user",
            "user_phone_number",
            "created_at",
            "expires_at",
            "attempts",
            "is_used",
            "is_expired",
        ]


class SendOTPSerializer(serializers.Serializer):
    phone_number = PhoneNumberField(required=True, region='IR')
    purpose = serializers.ChoiceField(
        choices=PhoneOTPModel.Purpose.choices,
        default=PhoneOTPModel.Purpose.LOGIN,
    )

    def validate_phone_number(self, value):
        value = str(value).strip()

        if not value:
            raise serializers.ValidationError("Phone number is required.")

        return value


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = PhoneNumberField(required=True, region='IR')
    code = serializers.CharField(
        required=True,
        min_length=4,
        max_length=8,
        write_only=True,
    )
    purpose = serializers.ChoiceField(
        choices=PhoneOTPModel.Purpose.choices,
        default=PhoneOTPModel.Purpose.LOGIN,
    )

    def validate_phone_number(self, value):
        value = str(value).strip()

        if not value:
            raise serializers.ValidationError("Phone number is required.")

        return value

    def validate_code(self, value):
        if not value.isascii() or not value.isdigit():
            raise serializers.ValidationError(
                "OTP code must contain only ASCII digits."
            )
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    phone_number = PhoneNumberField(required=True, region="IR")

    def validate_phone_number(self, value):
        value = str(value).strip()

        if not value:
            raise serializers.ValidationError("Phone number is required.")

        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    phone_number = PhoneNumberField(required=True, region="IR")
    code = serializers.CharField(
        required=True,
        min_length=4,
        max_length=8,
        write_only=True,
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    def validate_code(self, value):
        if not value.isascii() or not value.isdigit():
            raise serializers.ValidationError(
                "OTP code must contain only ASCII digits."
            )
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {
                    "new_password_confirm": (
                        "Password confirmation does not match."
                    )
                }
            )

        return attrs


DetailResponseSerializer = inline_serializer(
    name="DetailResponse",
    fields={
        "detail": serializers.CharField(),
    },
)


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context["request"].user

        if user.has_usable_password():
            raise serializers.ValidationError(
                {"detail": "Password is already set. Use change password instead."}
            )

        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )

        password_validation.validate_password(
            attrs["new_password"],
            user=user,
        )

        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "phone_number")
        read_only_fields = fields
