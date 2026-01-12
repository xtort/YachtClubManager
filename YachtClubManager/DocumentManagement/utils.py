"""
Utility functions for document management permissions
"""
from ManagementApp.models import Role


def get_user_roles(user):
    """Get all roles for a user"""
    if not user.is_authenticated:
        return Role.objects.none()
    return user.roles.all()


def check_folder_permission(user, folder, permission_type='view'):
    """
    Check if user has a specific permission on a folder.
    Permissions cascade from parent folders.
    
    Args:
        user: User instance
        folder: DocumentFolder instance
        permission_type: 'view', 'add', 'edit', or 'delete'
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    from .models import FolderPermission
    
    if not user.is_authenticated:
        return False
    
    # Admin users have all permissions
    if user.has_permission('manage_users') or user.has_permission('access_admin'):
        return True
    
    # Get all user roles
    user_roles = get_user_roles(user)
    if not user_roles.exists():
        return False
    
    # Check permissions starting from root folder up to current folder
    folders_to_check = folder.get_all_ancestors() + [folder]
    
    for folder_to_check in folders_to_check:
        # Check if any of user's roles have the required permission
        for role in user_roles:
            try:
                perm = FolderPermission.objects.get(folder=folder_to_check, role=role)
                if permission_type == 'view' and perm.can_view:
                    return True
                elif permission_type == 'add' and perm.can_add:
                    return True
                elif permission_type == 'edit' and perm.can_edit:
                    return True
                elif permission_type == 'delete' and perm.can_delete:
                    return True
            except FolderPermission.DoesNotExist:
                continue
    
    return False


def get_accessible_folders(user, permission_type='view'):
    """
    Get all folders a user can access based on permission type.
    
    Args:
        user: User instance
        permission_type: 'view', 'add', 'edit', or 'delete'
    
    Returns:
        QuerySet: Folders the user can access
    """
    from .models import DocumentFolder, FolderPermission
    
    if not user.is_authenticated:
        return DocumentFolder.objects.none()
    
    # Admin users can access all folders
    if user.has_permission('manage_users') or user.has_permission('access_admin'):
        return DocumentFolder.objects.all()
    
    # Get user roles
    user_roles = get_user_roles(user)
    if not user_roles.exists():
        return DocumentFolder.objects.none()
    
    # Get folders where user has the required permission
    permission_field = f'can_{permission_type}'
    permissions = FolderPermission.objects.filter(
        role__in=user_roles,
        **{permission_field: True}
    ).select_related('folder')
    
    folder_ids = set()
    for perm in permissions:
        folder_ids.add(perm.folder_id)
        # Include all subfolders (permissions cascade down)
        for descendant in perm.folder.get_all_descendants():
            folder_ids.add(descendant.id)
    
    return DocumentFolder.objects.filter(id__in=folder_ids)


def can_access_folder(user, folder, permission_type='view'):
    """Alias for check_folder_permission for backward compatibility"""
    return check_folder_permission(user, folder, permission_type)

