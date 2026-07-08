# core/api_router.py

from rest_framework.routers import DefaultRouter

from product.views import ProductViewSet, ProductVariantViewSet
from notification.views import NotificationViewSet
from user.views import UserViewSet, PhoneOTPViewSet

router = DefaultRouter()


router.register("products", ProductViewSet, basename="product")
router.register("product-variants", ProductVariantViewSet,
                basename="product-variant")
router.register("user/notifications", NotificationViewSet,
                basename="notification")
router.register("users", UserViewSet, basename="user")
router.register("otps", PhoneOTPViewSet, basename="otp")
