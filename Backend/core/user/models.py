from datetime import timedelta
import uuid

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class CustomUserManager(UserManager):
    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not phone_number:
            raise ValueError("Superuser must have a phone number")

        if password is None:
            raise ValueError("Superuser must have a password")

        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("The phone number must be set")

        extra_fields.setdefault("is_active", True)

        user = self.model(phone_number=phone_number, **extra_fields)

        if password is None:
            user.set_unusable_password()
        else:
            user.set_password(password)

        user.save(using=self._db)
        return user


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None

    phone_number = PhoneNumberField(unique=True, region="IR")

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return str(self.phone_number)


class PhoneOTPModel(models.Model):
    class Purpose(models.TextChoices):
        LOGIN = "login", "Login"
        SIGNUP = "signup", "Signup"
        PASSWORD_RESET = "password_reset", "Password reset"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="otps",
        blank=True,
        null=True,
    )
    phone_number = PhoneNumberField(region="IR", null=True, blank=True)
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    purpose = models.CharField(
        max_length=20,
        choices=Purpose.choices,
        default=Purpose.LOGIN,
    )

    @staticmethod
    def new_expiry():
        return timezone.now() + timedelta(minutes=5)

    def set_code(self, raw_code):
        self.code_hash = make_password(raw_code)

    def check_code(self, raw_code):
        return check_password(raw_code, self.code_hash)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def mark_used(self):
        self.is_used = True
        self.save(update_fields=["is_used"])
