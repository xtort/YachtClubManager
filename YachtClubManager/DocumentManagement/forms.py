from django import forms
from .models import DocumentFolder, DocumentFile, FolderPermission
from ManagementApp.models import Role


class DocumentFolderForm(forms.ModelForm):
    """Form for creating and editing document folders"""
    
    class Meta:
        model = DocumentFolder
        fields = ['name', 'parent', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Folder name'
            }),
            'parent': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional folder description'
            }),
        }
        labels = {
            'name': 'Folder Name',
            'parent': 'Parent Folder',
            'description': 'Description',
        }
        help_texts = {
            'parent': 'Select a parent folder or leave empty for root folder',
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        exclude_folder = kwargs.pop('exclude_folder', None)
        super().__init__(*args, **kwargs)
        
        # Filter parent folders to only show accessible folders
        if self.user:
            from .utils import get_accessible_folders
            accessible_folders = get_accessible_folders(self.user, permission_type='add')
            if exclude_folder:
                accessible_folders = accessible_folders.exclude(id=exclude_folder.id)
            self.fields['parent'].queryset = accessible_folders
        else:
            self.fields['parent'].queryset = DocumentFolder.objects.none()
        
        # Add empty option for parent
        self.fields['parent'].required = False
        self.fields['parent'].empty_label = '-- Root Folder --'


class DocumentFileForm(forms.ModelForm):
    """Form for uploading document files"""
    
    class Meta:
        model = DocumentFile
        fields = ['folder', 'name', 'file', 'description']
        widgets = {
            'folder': forms.Select(attrs={
                'class': 'form-control'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'File name (optional, defaults to uploaded file name)'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '*/*'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional file description'
            }),
        }
        labels = {
            'folder': 'Folder',
            'name': 'File Name',
            'file': 'File',
            'description': 'Description',
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter folders to only show folders where user can add files
        if self.user:
            from .utils import get_accessible_folders
            accessible_folders = get_accessible_folders(self.user, permission_type='add')
            self.fields['folder'].queryset = accessible_folders
        else:
            self.fields['folder'].queryset = DocumentFolder.objects.none()
        
        # Make name optional (will use file name if not provided)
        self.fields['name'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        folder = cleaned_data.get('folder')
        file = cleaned_data.get('file')
        name = cleaned_data.get('name')
        
        # If no name provided, use file name
        if file and not name:
            cleaned_data['name'] = file.name
        
        # Check for duplicate file name in folder
        if folder and name:
            existing_file = DocumentFile.objects.filter(folder=folder, name=name)
            if self.instance.pk:
                existing_file = existing_file.exclude(pk=self.instance.pk)
            if existing_file.exists():
                raise forms.ValidationError(
                    f'A file with the name "{name}" already exists in this folder.'
                )
        
        return cleaned_data


class FolderPermissionForm(forms.ModelForm):
    """Form for setting folder permissions for roles"""
    
    class Meta:
        model = FolderPermission
        fields = ['role', 'can_view', 'can_add', 'can_edit', 'can_delete']
        widgets = {
            'role': forms.Select(attrs={
                'class': 'form-control'
            }),
            'can_view': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_add': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_edit': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_delete': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'role': 'Role',
            'can_view': 'Can View',
            'can_add': 'Can Add',
            'can_edit': 'Can Edit',
            'can_delete': 'Can Delete',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].queryset = Role.objects.all().order_by('name')

