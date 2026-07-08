from rest_framework import permissions


class IsNotificationOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.recipient == request.user
