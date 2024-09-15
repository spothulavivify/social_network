# users/permissions.py

from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Custom permission to check if the user has an Admin role.
    Admins can read, write, and delete.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'

class IsWriter(BasePermission):
    """
    Custom permission to check if the user has a Write role.
    Writers can read and write.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['WRITE', 'ADMIN']

class IsReader(BasePermission):
    """
    Custom permission to check if the user has a Read role.
    Readers can only read data.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['READ', 'WRITE', 'ADMIN']
