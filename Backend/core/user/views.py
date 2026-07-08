from django.contrib.auth import get_user_model
from django.db import transaction
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from user.services.otp import issue_and_send_otp
from user.services.auth import get_tokens_for_user

from .models import PhoneOTPModel
from .serializers import (
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PhoneOTPSerializer,
    SendOTPSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
    VerifyOTPSerializer,
)
from .serializers import LogoutSerializer

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="List users",
        description="Returns all users ordered by newest registration first.",
        responses=UserSerializer,
        tags=["Users"],
    ),
    retrieve=extend_schema(
        summary="Retrieve user",
        description="Returns a single user by ID.",
        responses=UserSerializer,
        tags=["Users"],
    ),
    create=extend_schema(
        summary="Create user",
        description="Creates a new user account using a phone number.",
        request=UserCreateSerializer,
        responses={201: UserSerializer},
        tags=["Users"],
    ),
    update=extend_schema(
        summary="Update user",
        description="Updates all editable user fields.",
        request=UserUpdateSerializer,
        responses=UserSerializer,
        tags=["Users"],
    ),
    partial_update=extend_schema(
        summary="Partially update user",
        description="Partially updates editable user fields.",
        request=UserUpdateSerializer,
        responses=UserSerializer,
        tags=["Users"],
    ),
    destroy=extend_schema(
        summary="Delete user",
        description="Deletes a user account.",
        responses={204: None},
        tags=["Users"],
    ),
    me=extend_schema(
        summary="Get or update current user",
        description="GET returns the authenticated user's profile. PATCH updates the authenticated user's profile.",
        request=UserUpdateSerializer,
        responses=UserSerializer,
        tags=["Users"],
    ),
    change_password=extend_schema(
        summary="Change password",
        description="Changes the authenticated user's password.",
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(
                description="Password changed successfully.",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"detail": "Password changed successfully."},
                    )
                ],
            )
        },
        tags=["Users"],
    ),
)
class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Logout user",
        description="Logs out the authenticated user. Usually used to blacklist or invalidate the refresh token.",
        request=LogoutSerializer,
        responses={
            200: OpenApiResponse(
                description="Logged out successfully.",
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "detail": "Logged out successfully."
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Invalid logout request.",
                examples=[
                    OpenApiExample(
                        name="Invalid token",
                        value={
                            "refresh": [
                                "This field is required."
                            ]
                        },
                    )
                ],
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided or are invalid.",
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={
                            "detail": "Authentication credentials were not provided."
                        },
                    )
                ],
            ),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = LogoutSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]

        if self.action in ["me", "change_password"]:
            return [permissions.IsAuthenticated()]

        return [permissions.IsAdminUser()]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer

        if self.action in ["update", "partial_update", "me"]:
            return UserUpdateSerializer

        return UserSerializer

    @action(
        detail=False,
        methods=["get", "patch"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def me(self, request):
        user = request.user

        if request.method == "GET":
            serializer = UserSerializer(user)
            return Response(serializer.data)

        serializer = UserUpdateSerializer(
            user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(UserSerializer(user).data)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def change_password(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class SendOTPAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    # API DOCUMENTATION PART
    @extend_schema(
        summary="Send OTP code",
        description="Sends a one-time password code to a phone number for login, signup, or password reset.",
        request=SendOTPSerializer,
        responses={
            201: OpenApiResponse(
                description="OTP code sent successfully.",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"detail": "OTP code sent successfully."},
                    )
                ],
            ),
            400: OpenApiResponse(description="Invalid phone number or purpose."),
        },
        tags=["OTP"],
    )
    # VIEW FUNCTIONALITY
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        purpose = serializer.validated_data["purpose"]

        user = User.objects.filter(phone_number=phone_number).first()

        if purpose == PhoneOTPModel.Purpose.LOGIN and not user:
            return Response(
                {"detail": "OTP code sent successfully."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if purpose == PhoneOTPModel.Purpose.SIGNUP and user:
            return Response(
                {"detail": "OTP code sent successfully."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if purpose == PhoneOTPModel.Purpose.PASSWORD_RESET and not user:
            return Response(
                {"detail": "OTP code sent successfully."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        issue_and_send_otp(
            phone_number=phone_number,
            purpose=purpose,
            user=user,
        )

        return Response(
            {"detail": "OTP code sent successfully."},
            status=status.HTTP_201_CREATED,
        )


class VerifyOTPAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    # API DOCUMENTATION PART
    @extend_schema(
        summary="Verify OTP code",
        description="Verifies an OTP code. For signup, creates the user if the phone number is not already registered.",
        request=VerifyOTPSerializer,
        responses={
            200: OpenApiResponse(
                response=UserSerializer,
                description="OTP verified successfully.",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "detail": "OTP verified successfully.",
                            "access": "token",
                            "refresh": "token",
                            "user": {
                                "id": "5954f233-76b2-4606-806c-3f6816378b88",
                                "phone_number": "+989175991704",
                                "first_name": "",
                                "last_name": "",
                                "email": "",
                                "is_active": "true",
                                "is_staff": "true",
                                "date_joined": "2026-07-07T18:48:10.045879Z",
                                "last_login": "2026-07-08T10:52:00.632008Z"
                            },
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Invalid, expired, or over-attempted OTP code."
            ),
        },
        tags=["OTP"],
    )
    @transaction.atomic
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]
        purpose = serializer.validated_data["purpose"]

        otp = (
            PhoneOTPModel.objects.select_for_update()
            .filter(
                phone_number=phone_number,
                purpose=purpose,
                is_used=False,
            )
            .order_by("-created_at")
            .first()
        )

        if not otp:
            return Response(
                {"detail": "OTP code not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp.is_expired:
            return Response(
                {"detail": "OTP code has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp.attempts >= 5:
            return Response(
                {"detail": "Too many attempts. Please request a new OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not otp.check_code(code):
            otp.attempts += 1
            otp.save(update_fields=["attempts"])

            return Response(
                {"detail": "Invalid OTP code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = otp.user

        if purpose == PhoneOTPModel.Purpose.SIGNUP and not user:
            user = User.objects.create_user(phone_number=phone_number)
            otp.user = user
            otp.save(update_fields=["user"])

        if purpose == PhoneOTPModel.Purpose.LOGIN and not user:
            return Response(
                {"detail": "OTP sent successfully."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if purpose == PhoneOTPModel.Purpose.PASSWORD_RESET:
            return Response(
                {"detail": "Use the password reset confirm endpoint for password reset OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp.mark_used()

        tokens = get_tokens_for_user(user)

        return Response(
            {
                "detail": "OTP verified successfully.",
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Request password reset OTP",
        description="Sends a password reset OTP code to an existing user's phone number.",
        request=PasswordResetRequestSerializer,
        responses={
            201: OpenApiResponse(
                description="Password reset OTP sent successfully.",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"detail": "Password reset OTP sent successfully."},
                    )
                ],
            ),
            400: OpenApiResponse(
                description="User with this phone number does not exist."
            ),
        },
        tags=["Password Reset"],
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        user = User.objects.filter(phone_number=phone_number).first()

        if not user:
            return Response(
                {"detail": "User with this phone number does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        issue_and_send_otp(
            phone_number=phone_number,
            purpose=PhoneOTPModel.Purpose.PASSWORD_RESET,
            user=user,
        )

        return Response(
            {"detail": "Password reset OTP sent successfully."},
            status=status.HTTP_201_CREATED,
        )


class PasswordResetConfirmAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Confirm password reset",
        description="Verifies the password reset OTP and sets a new password.",
        request=PasswordResetConfirmSerializer,
        responses={
            200: OpenApiResponse(
                description="Password reset successfully.",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"detail": "Password reset successfully."},
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Invalid, expired, or over-attempted OTP code."
            ),
        },
        tags=["Password Reset"],
    )
    @transaction.atomic
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]
        new_password = serializer.validated_data["new_password"]

        otp = (
            PhoneOTPModel.objects.select_for_update()
            .filter(
                phone_number=phone_number,
                purpose=PhoneOTPModel.Purpose.PASSWORD_RESET,
                is_used=False,
            )
            .order_by("-created_at")
            .first()
        )

        if not otp:
            return Response(
                {"detail": "OTP code not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp.is_expired:
            return Response(
                {"detail": "OTP code has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp.attempts >= 5:
            return Response(
                {"detail": "Too many attempts. Please request a new OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not otp.check_code(code):
            otp.attempts += 1
            otp.save(update_fields=["attempts"])

            return Response(
                {"detail": "Invalid OTP code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = otp.user or User.objects.filter(
            phone_number=phone_number).first()

        if not user:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])

        otp.mark_used()

        return Response(
            {"detail": "Password reset successfully."},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    list=extend_schema(
        summary="List OTP records",
        description="Admin-only endpoint for listing OTP records.",
        responses=PhoneOTPSerializer,
        tags=["Admin OTP"],
    ),
    retrieve=extend_schema(
        summary="Retrieve OTP record",
        description="Admin-only endpoint for retrieving a single OTP record.",
        responses=PhoneOTPSerializer,
        tags=["Admin OTP"],
    ),
)
class PhoneOTPViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PhoneOTPModel.objects.select_related(
        "user").order_by("-created_at")
    serializer_class = PhoneOTPSerializer
    permission_classes = [permissions.IsAdminUser]
