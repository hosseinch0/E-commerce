from rest_framework.routers import DefaultRouter

from user.views import AdminUserViewSet, PhoneOTPAdminViewSet
from notification.views import AdminNotificationViewSet


admin_router = DefaultRouter()

admin_router.register("users", AdminUserViewSet, basename="admin-user")
admin_router.register("otp-records", PhoneOTPAdminViewSet,
                      basename="admin-otp")
admin_router.register(
    "notifications", AdminNotificationViewSet, basename="admin-notification")
