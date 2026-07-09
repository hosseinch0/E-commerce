from django.urls import path

from .views import (
    AdminCartDetailAPIView,
    AdminCartListAPIView,
    AdminUserCartListAPIView,
    CartAPIView,
    CartClearAPIView,
    CartItemCreateAPIView,
    CartItemDetailAPIView,
)

urlpatterns = [
    path("", CartAPIView.as_view(), name="cart-detail"),
    path("items/", CartItemCreateAPIView.as_view(), name="cart-item-create"),
    path("items/<uuid:item_id>/",
         CartItemDetailAPIView.as_view(), name="cart-item-detail"),
    path("clear/", CartClearAPIView.as_view(), name="cart-clear"),

    path("admin/carts/", AdminCartListAPIView.as_view(), name="admin-cart-list"),
    path("admin/carts/<uuid:cart_id>/",
         AdminCartDetailAPIView.as_view(), name="admin-cart-detail"),
    path("admin/carts/users/<uuid:user_id>/",
         AdminUserCartListAPIView.as_view(), name="admin-user-cart-list"),
]
