from django.urls import path, include
from .views import (
    ProfileAPIView,
    ChangePasswordAPIView,
    SetPasswordAPIView,
    PasswordResetConfirmAPIView,
    PasswordResetRequestAPIView,
)
urlpatterns = [

    path("", ProfileAPIView.as_view(), name="profile"),
    path("change-password/", ChangePasswordAPIView.as_view(),
         name="profile-change-password"),
    path("set-password/", SetPasswordAPIView.as_view(),
         name="profile-set-password"),

    path("password-reset/request/", PasswordResetRequestAPIView.as_view(),
         name="password-reset-request"),
    path(
        "password-reset/confirm/", PasswordResetConfirmAPIView.as_view(), name="password-reset-confirm"),

]
