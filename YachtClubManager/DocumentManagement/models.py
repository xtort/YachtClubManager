from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
from ManagementApp.models import Role
import os
import re

User = get_user_model()


def sanitize_folder_name(name):
    """Sanitize folder name for filesystem compatibility"""
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Remove or replace special characters that are problematic in filenames
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Remove leading/trailing dots and spaces
    name = name.strip('. ')
    # Ensure it's not empty
    if not name:
        name = 'unnamed_folder'
    return name


def get_document_upload_path(instance, filename):
    """Generate upload path based on folder hierarchy"""
    # Get the folder path
    folder_path_parts = []
    current_folder = instance.folder
    
    # Build path from root to current folder
    while current_folder:
        folder_path_parts.insert(0, sanitize_folder_name(current_folder.name))
        current_folder = current_folder.parent
    
    # Join folder parts (use forward slashes - Django handles OS-specific paths)
    folder_path = '/'.join(folder_path_parts) if folder_path_parts else 'root'
    
    # Return full path: documents/FolderName/SubFolderName/filename.ext
    # Use forward slashes - Django's FileField handles OS-specific path separators
    return f'documents/{folder_path}/{filename}'


class DocumentFolder(models.Model):
    """Folder structure for document management with hierarchical support"""
    name = models.CharField(max_length=255, help_text='Folder name')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subfolders',
        help_text='Parent folder (leave empty for root folder)'
    )
    description = models.TextField(blank=True, help_text='Folder description')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_folders',
        help_text='User who created this folder'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = [['name', 'parent']]
        verbose_name = 'Document Folder'
        verbose_name_plural = 'Document Folders'
    
    def __str__(self):
        return self.get_full_path()
    
    def get_full_path(self):
        """Get the full path of the folder"""
        if self.parent:
            return f"{self.parent.get_full_path()}/{self.name}"
        return self.name
    
    def get_filesystem_path(self):
        """Get filesystem-safe path of the folder"""
        if self.parent:
            parent_path = self.parent.get_filesystem_path()
            return os.path.join(parent_path, sanitize_folder_name(self.name))
        return sanitize_folder_name(self.name)
    
    def clean(self):
        """Validate that folder doesn't reference itself as parent"""
        if self.parent == self:
            raise ValidationError('A folder cannot be its own parent.')
        
        # Prevent circular references
        if self.parent:
            current = self.parent
            while current:
                if current == self:
                    raise ValidationError('Circular reference detected in folder hierarchy.')
                current = current.parent
    
    def get_all_ancestors(self):
        """Get all ancestor folders"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors
    
    def get_all_descendants(self):
        """Get all descendant folders recursively"""
        descendants = []
        for subfolder in self.subfolders.all():
            descendants.append(subfolder)
            descendants.extend(subfolder.get_all_descendants())
        return descendants
    
    def get_absolute_url(self):
        return reverse('document_management:folder_detail', kwargs={'pk': self.pk})


class FolderPermission(models.Model):
    """RBAC permissions for folders - cascades to subfolders and files"""
    folder = models.ForeignKey(
        DocumentFolder,
        on_delete=models.CASCADE,
        related_name='permissions',
        help_text='Folder this permission applies to'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='folder_permissions',
        help_text='Role this permission applies to'
    )
    can_view = models.BooleanField(
        default=False,
        help_text='Can view folder and its contents'
    )
    can_add = models.BooleanField(
        default=False,
        help_text='Can add files and subfolders'
    )
    can_edit = models.BooleanField(
        default=False,
        help_text='Can edit folder and its contents'
    )
    can_delete = models.BooleanField(
        default=False,
        help_text='Can delete folder and its contents'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['folder', 'role']]
        verbose_name = 'Folder Permission'
        verbose_name_plural = 'Folder Permissions'
        ordering = ['folder', 'role']
    
    def __str__(self):
        return f"{self.folder.name} - {self.role.get_name_display()}"


class DocumentFile(models.Model):
    """Files stored within document folders"""
    folder = models.ForeignKey(
        DocumentFolder,
        on_delete=models.CASCADE,
        related_name='files',
        help_text='Folder containing this file'
    )
    name = models.CharField(max_length=255, help_text='File name')
    file = models.FileField(
        upload_to=get_document_upload_path,
        help_text='Upload file'
    )
    description = models.TextField(blank=True, help_text='File description')
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_files',
        help_text='User who uploaded this file'
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='File size in bytes'
    )
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        help_text='MIME type of the file'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = [['folder', 'name']]
        verbose_name = 'Document File'
        verbose_name_plural = 'Document Files'
    
    def __str__(self):
        return f"{self.folder.get_full_path()}/{self.name}"
    
    def get_absolute_url(self):
        return reverse('document_management:file_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        """Calculate file size and MIME type on save"""
        if self.file:
            self.file_size = self.file.size
            # Try to get MIME type from file
            import mimetypes
            mime_type, _ = mimetypes.guess_type(self.file.name)
            if mime_type:
                self.mime_type = mime_type
        super().save(*args, **kwargs)
    
    def get_file_size_display(self):
        """Return human-readable file size"""
        if not self.file_size:
            return "Unknown"
        size = float(self.file_size)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
