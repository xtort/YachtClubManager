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
    """Check if user has admin role or can manage users"""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    # Check if user has admin role or can manage users
    if user.role and user.role.name == 'admin':
        return True
    return user.has_permission('manage_users')

