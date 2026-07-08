from rest_framework.routers import DefaultRouter
from product.views import ProductViewSet, ProductVariantViewSet
from notification.views import NotificationViewSet, AdminNotificationViewSet
from user.views import ProfileAPIView, ChangePasswordAPIView
from django.urls import path, include

router = DefaultRouter()


router.register("products", ProductViewSet, basename="product")
router.register("product-variants", ProductVariantViewSet,
                basename="product-variant")
router.register("user/notifications", NotificationViewSet,
                basename="notification")
