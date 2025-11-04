from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from CalendarApp.models import EventCategory
from .models import Role, SALUTATION_CHOICES, COUNTRIES, US_STATES, VESSEL_TYPE_CHOICES, VESSEL_POWER_CHOICES, VESSEL_TIE_CHOICES
import pytz

ClubUser = get_user_model()

# Timezone choices
TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]
TIMEZONE_CHOICES.insert(0, ('', ''))



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

    class Meta:
        model = ClubUser
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'role', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'email': 'Email Address',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'phone_number': 'Phone Number',
            'role': 'Role',
            'is_active': 'Active',
        }

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

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])  # Django handles salting/hashing
        if commit:
            user.save()
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

    class Meta:
        model = ClubUser
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'role', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'email': 'Email Address',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'phone_number': 'Phone Number',
            'role': 'Role',
            'is_active': 'Active',
        }

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

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)  # Django handles salting/hashing
        if commit:
            user.save()
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

    class Meta:
        model = ClubUser
        fields = [
            # General Information
            'salutation', 'first_name', 'middle_initial', 'last_name', 'professional_designation',
            'date_of_birth', 'nickname', 'phone_number', 'email',
            # Spouse Information
            'spouse_first_name', 'spouse_last_name',
            # Primary Address
            'country', 'address1', 'address2', 'city', 'state', 'zip_code', 'timezone', 'primary_phone',
            # Work Information
            'company', 'occupation_title', 'work_phone',
            # Vessel Information
            'vessel_type', 'vessel_name', 'vessel_loa', 'vessel_beam', 'vessel_draft',
            'vessel_power_requirements', 'vessel_tie_preferences',
            # Photos
            'member_photo', 'vessel_photo',
        ]
        widgets = {
            # General Information
            'salutation': forms.Select(attrs={'class': 'form-control'}, choices=SALUTATION_CHOICES),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_initial': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '1', 'style': 'width: 60px;'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'professional_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nickname': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            # Spouse Information
            'spouse_first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'spouse_last_name': forms.TextInput(attrs={'class': 'form-control'}),
            # Primary Address
            'country': forms.Select(attrs={'class': 'form-control'}, choices=COUNTRIES),
            'address1': forms.TextInput(attrs={'class': 'form-control'}),
            'address2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}, choices=US_STATES),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'timezone': forms.Select(attrs={'class': 'form-control'}, choices=TIMEZONE_CHOICES),
            'primary_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            # Work Information
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'occupation_title': forms.TextInput(attrs={'class': 'form-control'}),
            'work_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            # Vessel Information
            'vessel_type': forms.Select(attrs={'class': 'form-control'}, choices=VESSEL_TYPE_CHOICES),
            'vessel_name': forms.TextInput(attrs={'class': 'form-control'}),
            'vessel_loa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '32.0'}),
            'vessel_beam': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '14.5'}),
            'vessel_draft': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '3.4'}),
            'vessel_power_requirements': forms.Select(attrs={'class': 'form-control'}, choices=VESSEL_POWER_CHOICES),
            'vessel_tie_preferences': forms.Select(attrs={'class': 'form-control'}, choices=VESSEL_TIE_CHOICES),
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
            'phone_number': 'Phone Number',
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
            'primary_phone': 'Primary Phone',
            # Work Information
            'company': 'Company',
            'occupation_title': 'Occupation/Title',
            'work_phone': 'Work Phone',
            # Vessel Information
            'vessel_type': 'Vessel Type',
            'vessel_name': 'Vessel Name',
            'vessel_loa': 'Vessel LOA (feet)',
            'vessel_beam': 'Vessel Beam (feet)',
            'vessel_draft': 'Vessel Draft (feet)',
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
        # Mark required fields
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['address1'].required = True
        self.fields['city'].required = True
        self.fields['state'].required = True
        self.fields['zip_code'].required = True
        self.fields['timezone'].required = True

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

