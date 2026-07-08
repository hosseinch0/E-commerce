"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from product.views import ProductViewSet, ProductVariantViewSet
from user.views import (
    UserViewSet,
    PhoneOTPViewSet,
    SendOTPAPIView,
    VerifyOTPAPIView,
    PasswordResetRequestAPIView,
    PasswordResetConfirmAPIView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


router = DefaultRouter()

# USERS
router.register(r"users", UserViewSet, basename="user")
router.register(r"otps", PhoneOTPViewSet, basename="otp")

# Products
router.register(r"products", ProductViewSet, basename="product")
router.register(r"product-variants", ProductVariantViewSet,
                basename="product-variant")


urlpatterns = [
    path('admin/', admin.site.urls),

    # Router URLs
    path("api/", include(router.urls)),


    # OTP Auth URLs
    path("api/auth/send-otp/", SendOTPAPIView.as_view(), name="send-otp"),
    path("api/auth/verify-otp/", VerifyOTPAPIView.as_view(), name="verify-otp"),

    # DRF browsable API login/logout
    path("api-auth/", include("rest_framework.urls")),
    path('i18n/', include('django.conf.urls.i18n')),


    # API DOCUMENTATION URLS
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"),
         name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),





    # Password Reset URLs
    path(
        "api/auth/password-reset/request/",
        PasswordResetRequestAPIView.as_view(),
        name="password-reset-request",
    ),
    path(
        "api/auth/password-reset/confirm/",
        PasswordResetConfirmAPIView.as_view(),
        name="password-reset-confirm",
    ),
]
