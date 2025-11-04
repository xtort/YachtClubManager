from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin


class RoleRequiredMixin(AccessMixin):
    """Mixin to require specific role permissions"""
    required_permission = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user has the required permission
        if self.required_permission:
            if not request.user.has_permission(self.required_permission):
                raise PermissionDenied("You don't have permission to access this page.")
        
        return super().dispatch(request, *args, **kwargs)


class UserManagementRequiredMixin(RoleRequiredMixin):
    """Mixin for views that require user management permissions"""
    required_permission = 'manage_users'


class CategoryManagementRequiredMixin(RoleRequiredMixin):
    """Mixin for views that require category management permissions"""
    required_permission = 'manage_categories'


class EventEditRequiredMixin(RoleRequiredMixin):
    """Mixin for views that require event editing permissions"""
    required_permission = 'edit_events'


class EventDeleteRequiredMixin(RoleRequiredMixin):
    """Mixin for views that require event deletion permissions"""
    required_permission = 'delete_events'

