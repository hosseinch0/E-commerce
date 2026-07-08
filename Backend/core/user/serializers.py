from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import PhoneOTPModel


User = get_user_model()


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
    phone_number = serializers.CharField(required=True)
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
    phone_number = serializers.CharField(required=True)
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
        value = str(value).strip()

        if not value.isdigit():
            raise serializers.ValidationError(
                "OTP code must contain only digits.")

        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)

    def validate_phone_number(self, value):
        value = str(value).strip()

        if not value:
            raise serializers.ValidationError("Phone number is required.")

        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
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
        value = str(value).strip()

        if not value.isdigit():
            raise serializers.ValidationError(
                "OTP code must contain only digits.")

        return value

    def validate(self, attrs):
        new_password = attrs.get("new_password")
        new_password_confirm = attrs.get("new_password_confirm")

        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )

        return attrs
