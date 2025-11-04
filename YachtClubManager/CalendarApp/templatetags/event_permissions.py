from django import template

register = template.Library()


@register.filter
def can_edit_events(user):
    """Check if user can edit events"""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.has_permission('edit_events')


@register.filter
def can_create_events(user):
    """Check if user can create events"""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.has_permission('create_events')


@register.filter
def can_delete_events(user):
    """Check if user can delete events"""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.has_permission('delete_events')


@register.filter
def is_admin(user):
    """Check if user has admin role (excludes superusers unless they also have admin role)"""
    if not user or not user.is_authenticated:
        return False
    # Only check for admin role - exclude superusers unless they also have admin role
    if user.role and user.role.name == 'admin':
        return True
    return False


@register.filter
def can_access_member_directory(user):
    """Check if user can access member directory (members, editors, admins - not viewers)"""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    # Viewer role cannot access
    if user.role and user.role.name == 'viewer':
        return False
    # All other authenticated users can access
    return True

