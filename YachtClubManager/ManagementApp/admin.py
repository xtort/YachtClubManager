from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import Role, ClubUser


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'can_view_events', 'can_create_events', 
                    'can_edit_events', 'can_delete_events', 'can_manage_categories', 
                    'can_manage_users', 'user_count']
    list_filter = ['can_view_events', 'can_create_events', 'can_manage_users']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Role Information', {
            'fields': ('name', 'description')
        }),
        ('Permissions', {
            'fields': (
                'can_view_events',
                'can_create_events',
                'can_edit_events',
                'can_delete_events',
                'can_manage_categories',
                'can_manage_users',
                'can_access_admin',
            )
        }),
    )

    def user_count(self, obj):
        """Show how many users have this role"""
        count = obj.users.count()
        return format_html(
            '<a href="/admin/ManagementApp/clubuser/?role__id__exact={}">{}</a>',
            obj.id,
            count
        )
    user_count.short_description = 'Users'


@admin.register(ClubUser)
class ClubUserAdmin(BaseUserAdmin):
    list_display = ['email', 'get_full_name', 'role', 'phone_number', 'is_active', 'last_login', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering = ['last_name', 'first_name']
    readonly_fields = ['date_joined', 'last_login', 'updated_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone_number')
        }),
        ('Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'updated_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2'),
        }),
    )
