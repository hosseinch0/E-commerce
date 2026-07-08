from django.urls import path, include
from .views import ProfileAPIView, ChangePasswordAPIView
urlpatterns = [

    path(
        "",
        ProfileAPIView.as_view(),
        name="profile",
    ),
    path(
        "change-password/",
        ChangePasswordAPIView.as_view(),
        name="profile-change-password",
    ),

]
