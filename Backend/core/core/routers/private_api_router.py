from rest_framework.routers import DefaultRouter
from user.views import AdminUserViewSet, PhoneOTPAdminViewSet
from notification.views import AdminNotificationViewSet
from django.urls import path, include
from product.views import AdminProductViewSet, AdminProductVariantViewSet

admin_router = DefaultRouter()

admin_router.register("users", AdminUserViewSet, basename="admin-user")
admin_router.register("otp-records", PhoneOTPAdminViewSet,
                      basename="admin-otp")
admin_router.register(
    "notifications", AdminNotificationViewSet, basename="admin-notification")

admin_router.register("products", AdminProductViewSet,
                      basename="admin-product",)

admin_router.register(
    "product-variants", AdminProductVariantViewSet, basename="admin-product-variant")
