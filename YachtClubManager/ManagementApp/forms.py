from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from CalendarApp.models import EventCategory
from .models import Role, MemberType, MemberTypeRelationship, SALUTATION_CHOICES, COUNTRIES, US_STATES, VESSEL_TYPE_CHOICES, VESSEL_POWER_CHOICES, VESSEL_TIE_CHOICES
import pytz

ClubUser = get_user_model()

# Timezone choices
TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]
TIMEZONE_CHOICES.insert(0, ('', ''))



class MemberTypeForm(forms.ModelForm):
    """Form for creating and editing member types"""
    
    class Meta:
        model = MemberType
        fields = ['name', 'description', 'is_active', 'can_be_parent', 'can_be_child']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Member type name (e.g., Full Member, Associate)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description of this member type'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_be_parent': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_be_child': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Member Type Name',
            'description': 'Description',
            'is_active': 'Active',
            'can_be_parent': 'Can Be Parent',
            'can_be_child': 'Can Be Child/Dependent',
        }
        help_texts = {
            'is_active': 'Whether this member type is currently active.',
            'can_be_parent': 'Members with this type can have dependent members (children, spouses, etc.)',
            'can_be_child': 'Members with this type can be assigned to a parent member',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
        return name


class MemberTypeRelationshipForm(forms.ModelForm):
    """Form for creating and editing member type relationships"""
    
    class Meta:
        model = MemberTypeRelationship
        fields = ['parent_type', 'child_type', 'relationship_name', 'max_children', 'is_active']
        widgets = {
            'parent_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'child_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'relationship_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Child, Spouse, First Mate'
            }),
            'max_children': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Leave blank for unlimited'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'parent_type': 'Parent Member Type',
            'child_type': 'Child/Dependent Member Type',
            'relationship_name': 'Relationship Name',
            'max_children': 'Maximum Children Per Parent',
            'is_active': 'Active',
        }
        help_texts = {
            'relationship_name': 'Name of the relationship (e.g., "Child", "Spouse", "First Mate")',
            'max_children': 'Maximum number of children of this type allowed per parent. Leave blank for unlimited.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show all active member types, but prefer those configured as parent/child
        # This allows users to see all options and configure member types if needed
        all_active_types = MemberType.objects.filter(is_active=True).order_by('display_order', 'name')
        
        # For parent type: show all active types, but prioritize those that can be parents
        parent_types = MemberType.objects.filter(can_be_parent=True, is_active=True).order_by('display_order', 'name')
        if parent_types.exists():
            self.fields['parent_type'].queryset = parent_types
        else:
            # If no types are configured as parents, show all active types with a warning
            self.fields['parent_type'].queryset = all_active_types
        
        # For child type: show all active types, but prioritize those that can be children
        child_types = MemberType.objects.filter(can_be_child=True, is_active=True).order_by('display_order', 'name')
        if child_types.exists():
            self.fields['child_type'].queryset = child_types
        else:
            # If no types are configured as children, show all active types with a warning
            self.fields['child_type'].queryset = all_active_types
        
        # Add help text if no types are configured
        if not parent_types.exists():
            self.fields['parent_type'].help_text = '⚠️ No member types are configured to be parents. Please edit member types and enable "Can Be Parent" first.'
        if not child_types.exists():
            self.fields['child_type'].help_text = '⚠️ No member types are configured to be children. Please edit member types and enable "Can Be Child" first.'
    
    def clean(self):
        cleaned_data = super().clean()
        parent_type = cleaned_data.get('parent_type')
        child_type = cleaned_data.get('child_type')
        
        if parent_type and child_type:
            if parent_type == child_type:
                raise forms.ValidationError('Parent and child types cannot be the same.')
            
            if not parent_type.can_be_parent:
                raise forms.ValidationError(f'"{parent_type.name}" is not configured to be a parent type.')
            
            if not child_type.can_be_child:
                raise forms.ValidationError(f'"{child_type.name}" is not configured to be a child type.')
        
        return cleaned_data


class RoleForm(forms.ModelForm):
    """Form for creating and editing roles"""
    
    class Meta:
        model = Role
        fields = ['name', 'description', 'can_view_events', 'can_create_events', 
                  'can_edit_events', 'can_delete_events', 'can_manage_categories', 
                  'can_manage_users', 'can_access_admin']
        widgets = {
            'name': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description of this role and its permissions'
            }),
            'can_view_events': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_create_events': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_edit_events': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_delete_events': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_manage_categories': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_manage_users': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_access_admin': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Role Name',
            'description': 'Description',
            'can_view_events': 'Can View Events',
            'can_create_events': 'Can Create Events',
            'can_edit_events': 'Can Edit Events',
            'can_delete_events': 'Can Delete Events',
            'can_manage_categories': 'Can Manage Categories',
            'can_manage_users': 'Can Manage Users',
            'can_access_admin': 'Can Access Admin Panel',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
        return name


class EventCategoryForm(forms.ModelForm):
    """Form for creating and editing event categories"""
    
    class Meta:
        model = EventCategory
        fields = ['name', 'description', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name (e.g., Racing, Social, Training)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of this category'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'style': 'width: 100px; height: 40px;',
            }),
        }
        labels = {
            'name': 'Category Name',
            'description': 'Description',
            'color': 'Display Color',
        }
        help_texts = {
            'color': 'This color will be used to display events of this category on the calendar.',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if not name:
                raise forms.ValidationError('Category name cannot be empty.')
        return name


class ClubUserCreateForm(forms.ModelForm):
    """Form for creating new club users"""
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Password must be at least 8 characters long.'
    )
    password2 = forms.CharField(
        label='Password Confirmation',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Enter the same password as above, for verification.'
    )
    
    is_dependent = forms.BooleanField(
        required=False,
        label='Is this a dependent/child member?',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_dependent'}),
        help_text='Check if this member is a dependent (child, spouse, etc.) of another member'
    )
    
    parent_member = forms.ModelChoiceField(
        queryset=ClubUser.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_parent_member'}),
        label='Parent Member',
        help_text='Select the parent member if this is a dependent'
    )
    
    relationship_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_relationship_type'}),
        label='Relationship Type',
        help_text='Type of relationship (e.g., Child, Spouse, First Mate)'
    )

    class Meta:
        model = ClubUser
        fields = ['email', 'first_name', 'last_name', 'primary_phone_number', 'role', 'member_types', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'member_types': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'email': 'Email Address',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'primary_phone_number': 'Primary Phone Number',
            'role': 'Role',
            'member_types': 'Member Types',
            'is_active': 'Active',
        }
        help_texts = {
            'member_types': 'Select at least one member type. Hold Ctrl/Cmd to select multiple.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for parent member - only show members who can be parents
        parent_member_types = MemberType.objects.filter(can_be_parent=True, is_active=True)
        self.fields['parent_member'].queryset = ClubUser.objects.filter(
            member_types__in=parent_member_types,
            is_active=True
        ).distinct().order_by('last_name', 'first_name')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if ClubUser.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return password2
    
    def clean_member_types(self):
        member_types = self.cleaned_data.get('member_types')
        if not member_types:
            raise forms.ValidationError('At least one member type must be selected.')
        return member_types
    
    def clean(self):
        cleaned_data = super().clean()
        is_dependent = cleaned_data.get('is_dependent')
        parent_member = cleaned_data.get('parent_member')
        relationship_type = cleaned_data.get('relationship_type')
        member_types = cleaned_data.get('member_types')
        
        if is_dependent:
            if not parent_member:
                raise forms.ValidationError({'parent_member': 'Parent member is required for dependent members.'})
            
            if not relationship_type:
                raise forms.ValidationError({'relationship_type': 'Relationship type is required for dependent members.'})
            
            # Validate that the member types allow being a child
            if member_types:
                child_types = [mt for mt in member_types if mt.can_be_child]
                if not child_types:
                    raise forms.ValidationError({'member_types': 'At least one selected member type must be configured to allow being a child/dependent.'})
                
                # Check if there's a valid relationship between parent's types and child's types
                parent_types = parent_member.member_types.filter(can_be_parent=True)
                valid_relationship = MemberTypeRelationship.objects.filter(
                    parent_type__in=parent_types,
                    child_type__in=child_types,
                    is_active=True
                ).exists()
                
                if not valid_relationship:
                    raise forms.ValidationError({
                        'member_types': 'No valid parent-child relationship exists between the selected member types and the parent member\'s types.'
                    })
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])  # Django handles salting/hashing
        
        # Set parent relationship if this is a dependent
        if self.cleaned_data.get('is_dependent'):
            user.parent_member = self.cleaned_data.get('parent_member')
            user.relationship_type = self.cleaned_data.get('relationship_type', '')
        else:
            user.parent_member = None
            user.relationship_type = ''
        
        if commit:
            user.save()
            # Save many-to-many relationships
            self.save_m2m()
        return user


class ClubUserUpdateForm(forms.ModelForm):
    """Form for updating existing club users"""
    password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Leave blank to keep the current password.'
    )
    password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    is_dependent = forms.BooleanField(
        required=False,
        label='Is this a dependent/child member?',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_dependent'}),
        help_text='Check if this member is a dependent (child, spouse, etc.) of another member'
    )
    
    parent_member = forms.ModelChoiceField(
        queryset=ClubUser.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_parent_member'}),
        label='Parent Member',
        help_text='Select the parent member if this is a dependent'
    )
    
    relationship_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_relationship_type'}),
        label='Relationship Type',
        help_text='Type of relationship (e.g., Child, Spouse, First Mate)'
    )

    class Meta:
        model = ClubUser
        fields = ['email', 'first_name', 'last_name', 'primary_phone_number', 'role', 'member_types', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'member_types': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'email': 'Email Address',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'primary_phone_number': 'Primary Phone Number',
            'role': 'Role',
            'member_types': 'Member Types',
            'is_active': 'Active',
        }
        help_texts = {
            'member_types': 'Select at least one member type. Hold Ctrl/Cmd to select multiple.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for parent member - only show members who can be parents
        parent_member_types = MemberType.objects.filter(can_be_parent=True, is_active=True)
        # Exclude self from parent options
        parent_queryset = ClubUser.objects.filter(
            member_types__in=parent_member_types,
            is_active=True
        ).distinct().order_by('last_name', 'first_name')
        
        if self.instance and self.instance.pk:
            parent_queryset = parent_queryset.exclude(pk=self.instance.pk)
        
        self.fields['parent_member'].queryset = parent_queryset
        
        # Set initial values if editing existing user
        if self.instance and self.instance.pk:
            self.fields['is_dependent'].initial = bool(self.instance.parent_member)
            self.fields['parent_member'].initial = self.instance.parent_member
            self.fields['relationship_type'].initial = self.instance.relationship_type

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email is being changed and if new email already exists
        if self.instance and self.instance.email != email:
            if ClubUser.objects.filter(email=email).exists():
                raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError('Passwords do not match.')
        return password2
    
    def clean_member_types(self):
        member_types = self.cleaned_data.get('member_types')
        if not member_types:
            raise forms.ValidationError('At least one member type must be selected.')
        return member_types
    
    def clean(self):
        cleaned_data = super().clean()
        is_dependent = cleaned_data.get('is_dependent')
        parent_member = cleaned_data.get('parent_member')
        relationship_type = cleaned_data.get('relationship_type')
        member_types = cleaned_data.get('member_types')
        
        if is_dependent:
            if not parent_member:
                raise forms.ValidationError({'parent_member': 'Parent member is required for dependent members.'})
            
            if not relationship_type:
                raise forms.ValidationError({'relationship_type': 'Relationship type is required for dependent members.'})
            
            # Prevent circular relationships
            if self.instance and self.instance.pk and parent_member.pk == self.instance.pk:
                raise forms.ValidationError({'parent_member': 'A member cannot be their own parent.'})
            
            # Validate that the member types allow being a child
            if member_types:
                child_types = [mt for mt in member_types if mt.can_be_child]
                if not child_types:
                    raise forms.ValidationError({'member_types': 'At least one selected member type must be configured to allow being a child/dependent.'})
                
                # Check if there's a valid relationship between parent's types and child's types
                parent_types = parent_member.member_types.filter(can_be_parent=True)
                valid_relationship = MemberTypeRelationship.objects.filter(
                    parent_type__in=parent_types,
                    child_type__in=child_types,
                    is_active=True
                ).exists()
                
                if not valid_relationship:
                    raise forms.ValidationError({
                        'member_types': 'No valid parent-child relationship exists between the selected member types and the parent member\'s types.'
                    })
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)  # Django handles salting/hashing
        
        # Set parent relationship if this is a dependent
        if self.cleaned_data.get('is_dependent'):
            user.parent_member = self.cleaned_data.get('parent_member')
            user.relationship_type = self.cleaned_data.get('relationship_type', '')
        else:
            user.parent_member = None
            user.relationship_type = ''
        
        if commit:
            user.save()
            # Save many-to-many relationships
            self.save_m2m()
        return user


class ProfileUpdateForm(forms.ModelForm):
    """Form for users to update their own profile (no role or is_active changes)"""
    password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Leave blank to keep the current password.'
    )
    password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    # Override timezone field to use ChoiceField since model field doesn't have choices
    timezone = forms.ChoiceField(
        choices=TIMEZONE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label='Timezone'
    )

    class Meta:
        model = ClubUser
        fields = [
            # General Information
            'salutation', 'first_name', 'middle_initial', 'last_name', 'professional_designation',
            'date_of_birth', 'nickname', 'primary_phone_number', 'email',
            # Spouse Information
            'spouse_first_name', 'spouse_last_name',
            # Primary Address
            'country', 'address1', 'address2', 'city', 'state', 'zip_code', 'timezone', 'secondary_phone_number',
            # Work Information
            'company', 'occupation_title', 'work_phone',
            # Vessel Information
            'vessel_type', 'vessel_name', 'vessel_moorage_location', 'vessel_manufacturer', 'vessel_model',
            'vessel_loa', 'vessel_beam', 'vessel_draft', 'vessel_cruising_speed',
            'vessel_power_requirements', 'vessel_tie_preferences',
            # Photos
            'member_photo', 'vessel_photo',
        ]
        widgets = {
            # General Information
            'salutation': forms.Select(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_initial': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '1', 'style': 'width: 60px;'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'professional_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'nickname': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            # Spouse Information
            'spouse_first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'spouse_last_name': forms.TextInput(attrs={'class': 'form-control'}),
            # Primary Address
            'country': forms.Select(attrs={'class': 'form-control'}),
            'address1': forms.TextInput(attrs={'class': 'form-control'}),
            'address2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            # timezone is defined as ChoiceField above, so don't include widget here
            'secondary_phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            # Work Information
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'occupation_title': forms.TextInput(attrs={'class': 'form-control'}),
            'work_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            # Vessel Information
            'vessel_type': forms.Select(attrs={'class': 'form-control'}),
            'vessel_name': forms.TextInput(attrs={'class': 'form-control'}),
            'vessel_moorage_location': forms.TextInput(attrs={'class': 'form-control'}),
            'vessel_manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'vessel_model': forms.TextInput(attrs={'class': 'form-control'}),
            'vessel_loa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '32.0'}),
            'vessel_beam': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '14.5'}),
            'vessel_draft': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '3.4'}),
            'vessel_cruising_speed': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '8.5'}),
            'vessel_power_requirements': forms.Select(attrs={'class': 'form-control'}),
            'vessel_tie_preferences': forms.Select(attrs={'class': 'form-control'}),
            # Photos
            'member_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'vessel_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            # General Information
            'salutation': 'Salutation',
            'first_name': 'First Name',
            'middle_initial': 'Middle Initial',
            'last_name': 'Last Name',
            'professional_designation': 'Professional Designation',
            'date_of_birth': 'Date of Birth',
            'nickname': 'Nickname',
            'primary_phone_number': 'Primary Phone Number',
            'email': 'Email Address',
            # Spouse Information
            'spouse_first_name': 'Spouse First Name',
            'spouse_last_name': 'Spouse Last Name',
            # Primary Address
            'country': 'Country',
            'address1': 'Address 1',
            'address2': 'Address 2',
            'city': 'City',
            'state': 'State',
            'zip_code': 'Zip Code',
            'timezone': 'Timezone',
            'secondary_phone_number': 'Secondary Phone Number',
            # Work Information
            'company': 'Company',
            'occupation_title': 'Occupation/Title',
            'work_phone': 'Work Phone',
            # Vessel Information
            'vessel_type': 'Vessel Type',
            'vessel_name': 'Vessel Name',
            'vessel_moorage_location': 'Moorage Location',
            'vessel_manufacturer': 'Manufacturer/Builder',
            'vessel_model': 'Model',
            'vessel_loa': 'Vessel LOA (feet)',
            'vessel_beam': 'Vessel Beam (feet)',
            'vessel_draft': 'Vessel Draft (feet)',
            'vessel_cruising_speed': 'Average Cruising Speed (knots)',
            'vessel_power_requirements': 'Vessel Power Requirements',
            'vessel_tie_preferences': 'Vessel Tie Preferences',
            # Photos
            'member_photo': 'Member Photo',
            'vessel_photo': 'Vessel Photo',
        }
        help_texts = {
            'date_of_birth': 'Year is stored but will not be displayed publicly.',
            'middle_initial': 'Single letter only.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set choices for Select fields (must be done after super() to ensure instance is populated)
        self.fields['salutation'].choices = SALUTATION_CHOICES
        self.fields['country'].choices = COUNTRIES
        self.fields['state'].choices = US_STATES
        # Timezone is already a ChoiceField, so it has choices set
        self.fields['vessel_type'].choices = VESSEL_TYPE_CHOICES
        self.fields['vessel_power_requirements'].choices = VESSEL_POWER_CHOICES
        self.fields['vessel_tie_preferences'].choices = VESSEL_TIE_CHOICES
        
        # Mark required fields
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['address1'].required = True
        self.fields['city'].required = True
        self.fields['state'].required = True
        self.fields['zip_code'].required = True
        # timezone is already required=True in field definition above

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email is being changed and if new email already exists
        if self.instance and self.instance.email != email:
            if ClubUser.objects.filter(email=email).exists():
                raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError('Passwords do not match.')
        return password2

    def clean_middle_initial(self):
        middle_initial = self.cleaned_data.get('middle_initial', '').strip().upper()
        if middle_initial and len(middle_initial) > 1:
            raise forms.ValidationError('Middle initial must be a single letter.')
        return middle_initial

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)  # Django handles salting/hashing
        if commit:
            user.save()
        return user

