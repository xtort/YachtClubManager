from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin
from .utils import check_folder_permission


class FolderPermissionMixin(AccessMixin):
    """Mixin to check folder permissions"""
    permission_type = 'view'
    folder_lookup_field = 'pk'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Get folder from kwargs
        folder_id = kwargs.get(self.folder_lookup_field)
        if folder_id:
            from .models import DocumentFolder
            try:
                folder = DocumentFolder.objects.get(pk=folder_id)
                if not check_folder_permission(request.user, folder, self.permission_type):
                    raise PermissionDenied(
                        f"You don't have permission to {self.permission_type} this folder."
                    )
            except DocumentFolder.DoesNotExist:
                raise PermissionDenied("Folder not found.")
        
        return super().dispatch(request, *args, **kwargs)


class FolderViewMixin(FolderPermissionMixin):
    """Mixin for views that require view permission"""
    permission_type = 'view'


class FolderAddMixin(FolderPermissionMixin):
    """Mixin for views that require add permission"""
    permission_type = 'add'


class FolderEditMixin(FolderPermissionMixin):
    """Mixin for views that require edit permission"""
    permission_type = 'edit'


class FolderDeleteMixin(FolderPermissionMixin):
    """Mixin for views that require delete permission"""
    permission_type = 'delete'


class DocumentManagementRequiredMixin(AccessMixin):
    """Mixin for document management views - requires admin or user management permission"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Admin users or users with manage_users permission can access
        if not (request.user.has_permission('manage_users') or 
                request.user.has_permission('access_admin')):
            raise PermissionDenied("You don't have permission to manage documents.")
        
        return super().dispatch(request, *args, **kwargs)

