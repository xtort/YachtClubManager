from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, FileResponse
from django.db.models import Q

from .models import DocumentFolder, DocumentFile, FolderPermission
from .forms import DocumentFolderForm, DocumentFileForm, FolderPermissionForm
from .mixins import (
    DocumentManagementRequiredMixin,
    FolderViewMixin,
    FolderAddMixin,
    FolderEditMixin,
    FolderDeleteMixin
)
from .utils import get_accessible_folders, check_folder_permission


class FolderListView(DocumentManagementRequiredMixin, ListView):
    """List all folders in a tree structure"""
    model = DocumentFolder
    template_name = 'DocumentManagement/folder_list.html'
    context_object_name = 'folders'
    
    def get_queryset(self):
        """Get root folders (folders without parents)"""
        return DocumentFolder.objects.filter(parent=None).order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_folders'] = DocumentFolder.objects.all().order_by('name')
        return context


class FolderDetailView(FolderViewMixin, DetailView):
    """View folder details, subfolders, and files"""
    model = DocumentFolder
    template_name = 'DocumentManagement/folder_detail.html'
    context_object_name = 'folder'
    permission_type = 'view'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        folder = self.object
        
        # Get subfolders user can view
        subfolders = folder.subfolders.all()
        accessible_subfolders = [
            sf for sf in subfolders 
            if check_folder_permission(self.request.user, sf, 'view')
        ]
        context['subfolders'] = accessible_subfolders
        
        # Get files user can view (if they have view permission on folder)
        context['files'] = folder.files.all().order_by('name')
        
        # Get permissions for this folder
        context['permissions'] = folder.permissions.all().select_related('role')
        
        # Check user's permissions on this folder
        context['can_add'] = check_folder_permission(self.request.user, folder, 'add')
        context['can_edit'] = check_folder_permission(self.request.user, folder, 'edit')
        context['can_delete'] = check_folder_permission(self.request.user, folder, 'delete')
        
        # Get breadcrumbs
        context['breadcrumbs'] = folder.get_all_ancestors()
        
        return context


class FolderCreateView(DocumentManagementRequiredMixin, CreateView):
    """Create a new folder"""
    model = DocumentFolder
    form_class = DocumentFolderForm
    template_name = 'DocumentManagement/folder_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(
            self.request,
            f'Folder "{form.instance.name}" has been created successfully!'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        if self.object.parent:
            return reverse_lazy('document_management:folder_detail', kwargs={'pk': self.object.parent.pk})
        return reverse_lazy('document_management:folder_list')


class FolderUpdateView(FolderEditMixin, UpdateView):
    """Update an existing folder"""
    model = DocumentFolder
    form_class = DocumentFolderForm
    template_name = 'DocumentManagement/folder_form.html'
    permission_type = 'edit'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['exclude_folder'] = self.object
        return kwargs
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Folder "{form.instance.name}" has been updated successfully!'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('document_management:folder_detail', kwargs={'pk': self.object.pk})


class FolderDeleteView(FolderDeleteMixin, DeleteView):
    """Delete a folder"""
    model = DocumentFolder
    template_name = 'DocumentManagement/folder_confirm_delete.html'
    permission_type = 'delete'
    
    def get_success_url(self):
        if self.object.parent:
            return reverse_lazy('document_management:folder_detail', kwargs={'pk': self.object.parent.pk})
        return reverse_lazy('document_management:folder_list')
    
    def form_valid(self, form):
        folder_name = self.object.name
        messages.success(
            self.request,
            f'Folder "{folder_name}" and all its contents have been deleted successfully!'
        )
        return super().form_valid(form)


class FileUploadView(DocumentManagementRequiredMixin, CreateView):
    """Upload a new file"""
    model = DocumentFile
    form_class = DocumentFileForm
    template_name = 'DocumentManagement/file_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        # Pre-select folder if provided
        folder_id = self.request.GET.get('folder')
        if folder_id:
            try:
                folder = DocumentFolder.objects.get(pk=folder_id)
                if check_folder_permission(self.request.user, folder, 'add'):
                    kwargs['initial'] = {'folder': folder}
            except DocumentFolder.DoesNotExist:
                pass
        
        return kwargs
    
    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        
        # Check permission on selected folder
        if not check_folder_permission(self.request.user, form.instance.folder, 'add'):
            messages.error(self.request, 'You do not have permission to add files to this folder.')
            return self.form_invalid(form)
        
        messages.success(
            self.request,
            f'File "{form.instance.name}" has been uploaded successfully!'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('document_management:folder_detail', kwargs={'pk': self.object.folder.pk})


class FileDetailView(DetailView):
    """View file details"""
    model = DocumentFile
    template_name = 'DocumentManagement/file_detail.html'
    context_object_name = 'file'
    
    def dispatch(self, request, *args, **kwargs):
        file_obj = self.get_object()
        # Check if user can view the folder containing this file
        if not check_folder_permission(request.user, file_obj.folder, 'view'):
            raise PermissionDenied("You don't have permission to view this file.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        file_obj = self.object
        
        # Check user's permissions on the folder
        context['can_edit'] = check_folder_permission(self.request.user, file_obj.folder, 'edit')
        context['can_delete'] = check_folder_permission(self.request.user, file_obj.folder, 'delete')
        
        return context


class FileDownloadView(DetailView):
    """Download a file"""
    model = DocumentFile
    
    def dispatch(self, request, *args, **kwargs):
        file_obj = self.get_object()
        # Check if user can view the folder containing this file
        if not check_folder_permission(request.user, file_obj.folder, 'view'):
            raise PermissionDenied("You don't have permission to download this file.")
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        file_obj = self.get_object()
        return FileResponse(
            file_obj.file.open(),
            as_attachment=True,
            filename=file_obj.name
        )


class FileUpdateView(UpdateView):
    """Update file metadata"""
    model = DocumentFile
    form_class = DocumentFileForm
    template_name = 'DocumentManagement/file_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        file_obj = self.get_object()
        # Check if user can edit the folder containing this file
        if not check_folder_permission(request.user, file_obj.folder, 'edit'):
            raise PermissionDenied("You don't have permission to edit this file.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'File "{form.instance.name}" has been updated successfully!'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('document_management:file_detail', kwargs={'pk': self.object.pk})


class FileDeleteView(DeleteView):
    """Delete a file"""
    model = DocumentFile
    template_name = 'DocumentManagement/file_confirm_delete.html'
    
    def dispatch(self, request, *args, **kwargs):
        file_obj = self.get_object()
        # Check if user can delete files in the folder containing this file
        if not check_folder_permission(request.user, file_obj.folder, 'delete'):
            raise PermissionDenied("You don't have permission to delete this file.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('document_management:folder_detail', kwargs={'pk': self.object.folder.pk})
    
    def form_valid(self, form):
        file_name = self.object.name
        messages.success(
            self.request,
            f'File "{file_name}" has been deleted successfully!'
        )
        return super().form_valid(form)


class FolderPermissionCreateView(DocumentManagementRequiredMixin, CreateView):
    """Create folder permission"""
    model = FolderPermission
    form_class = FolderPermissionForm
    template_name = 'DocumentManagement/permission_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.folder = get_object_or_404(DocumentFolder, pk=kwargs['folder_id'])
        # Only admins can set permissions
        if not (request.user.has_permission('manage_users') or request.user.has_permission('access_admin')):
            raise PermissionDenied("You don't have permission to manage folder permissions.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {'folder': self.folder}
        return kwargs
    
    def form_valid(self, form):
        form.instance.folder = self.folder
        messages.success(
            self.request,
            f'Permission for role "{form.instance.role.get_name_display()}" has been set successfully!'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('document_management:folder_detail', kwargs={'pk': self.folder.pk})


class FolderPermissionUpdateView(DocumentManagementRequiredMixin, UpdateView):
    """Update folder permission"""
    model = FolderPermission
    form_class = FolderPermissionForm
    template_name = 'DocumentManagement/permission_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Only admins can set permissions
        if not (request.user.has_permission('manage_users') or request.user.has_permission('access_admin')):
            raise PermissionDenied("You don't have permission to manage folder permissions.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('document_management:folder_detail', kwargs={'pk': self.object.folder.pk})


class FolderPermissionDeleteView(DocumentManagementRequiredMixin, DeleteView):
    """Delete folder permission"""
    model = FolderPermission
    template_name = 'DocumentManagement/permission_confirm_delete.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Only admins can set permissions
        if not (request.user.has_permission('manage_users') or request.user.has_permission('access_admin')):
            raise PermissionDenied("You don't have permission to manage folder permissions.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('document_management:folder_detail', kwargs={'pk': self.object.folder.pk})


@login_required
def document_management_dashboard(request):
    """Dashboard view for document management"""
    # Check if user has admin or manage_users permission
    if not (request.user.has_permission('manage_users') or request.user.has_permission('access_admin')):
        raise PermissionDenied("You don't have permission to access document management.")
    
    # Get root folders
    root_folders = DocumentFolder.objects.filter(parent=None).order_by('name')
    
    # Get accessible folders for the user
    accessible_folders = get_accessible_folders(request.user, permission_type='view')
    
    context = {
        'root_folders': root_folders,
        'accessible_folders': accessible_folders,
    }
    
    return render(request, 'DocumentManagement/dashboard.html', context)
