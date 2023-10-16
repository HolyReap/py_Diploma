from rest_framework import permissions


class UserIsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
    
class UserIsShop(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.type == "shop"

class UserIsBuyer(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.type == "buyer"
