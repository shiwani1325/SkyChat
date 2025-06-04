from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    
    def has_permission(self, request, view):
        return bool(request.user and hasattr(request.user, 'role') and request.user.role == 'superadmin')

class IsOrganisation(BasePermission):
    
    def has_permission(self, request, view):
        return bool(request.user and hasattr(request.user, 'role') and request.user.role == 'organisation')