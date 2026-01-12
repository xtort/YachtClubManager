from django.contrib import admin
from .models import DocumentFolder, DocumentFile, FolderPermission


@admin.register(DocumentFolder)
class DocumentFolderAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'created_by', 'created_at', 'file_count', 'subfolder_count']
    list_filter = ['created_at', 'parent']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Folder Information', {
            'fields': ('name', 'parent', 'description')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_count(self, obj):
        return obj.files.count()
    file_count.short_description = 'Files'
    
    def subfolder_count(self, obj):
        return obj.subfolders.count()
    subfolder_count.short_description = 'Subfolders'


@admin.register(DocumentFile)
class DocumentFileAdmin(admin.ModelAdmin):
    list_display = ['name', 'folder', 'uploaded_by', 'file_size', 'created_at']
    list_filter = ['created_at', 'folder', 'mime_type']
    search_fields = ['name', 'description', 'folder__name']
    readonly_fields = ['created_at', 'updated_at', 'file_size', 'mime_type']
    
    fieldsets = (
        ('File Information', {
            'fields': ('folder', 'name', 'file', 'description')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'file_size', 'mime_type', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FolderPermission)
class FolderPermissionAdmin(admin.ModelAdmin):
    list_display = ['folder', 'role', 'can_view', 'can_add', 'can_edit', 'can_delete']
    list_filter = ['can_view', 'can_add', 'can_edit', 'can_delete', 'role']
    search_fields = ['folder__name', 'role__name']
    readonly_fields = ['created_at', 'updated_at']
