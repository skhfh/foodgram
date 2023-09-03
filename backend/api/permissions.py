from rest_framework import permissions


class CurrentUserOrAdminPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        user = request.user
        return user.is_staff or obj.pk == user.pk


class AuthorOrReadOnlyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or request.user == obj.author)
