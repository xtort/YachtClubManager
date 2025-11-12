from django import forms
from django.forms import inlineformset_factory
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import Event, EventContact, EventRegistrationFee, EventRegistration, EventGuest
from django.contrib.auth import get_user_model
from ManagementApp.models import MemberType

ClubUser = get_user_model()


class EventContactForm(forms.ModelForm):
    """Form for individual event contact"""
    
    member_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control member-autocomplete',
            'placeholder': 'Start typing to search members...',
            'autocomplete': 'off'
        }),
        label='Search Member'
    )
    
    class Meta:
        model = EventContact
        fields = ['member', 'is_primary', 'responsibilities']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-control member-select', 'style': 'display: none;'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'responsibilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'member': 'Member',
            'is_primary': 'Primary Contact',
            'responsibilities': 'Responsibilities',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for member dropdown
        self.fields['member'].queryset = ClubUser.objects.filter(is_active=True).order_by('last_name', 'first_name')
        
        # If editing existing contact, set the search field value
        if self.instance and self.instance.pk and self.instance.member:
            self.fields['member_search'].initial = self.instance.member.get_full_name()
            self.fields['member'].initial = self.instance.member.pk


EventContactFormSet = inlineformset_factory(
    Event,
    EventContact,
    form=EventContactForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class EventForm(forms.ModelForm):
    """Form for creating and editing events"""
    
    formatted_description = forms.CharField(
        widget=CKEditor5Widget(config_name='extends'),
        required=False,
        help_text='Full formatted description with rich text editor'
    )

    class Meta:
        model = Event
        fields = ['title', 'short_description', 'category', 'start_datetime', 'end_datetime', 'formatted_description', 'registration_status', 'registration_open_datetime', 'registrant_list_visibility', 'allowed_member_types']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Event Title'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'start_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'registration_status': forms.Select(attrs={'class': 'form-control'}),
            'registration_open_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'registrant_list_visibility': forms.Select(attrs={'class': 'form-control'}),
            'allowed_member_types': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': 'Event Title',
            'short_description': 'Short Description',
            'category': 'Category',
            'start_datetime': 'Start Date & Time',
            'end_datetime': 'End Date & Time',
            'formatted_description': 'Formatted Description',
            'registration_status': 'Registration Status',
            'registration_open_datetime': 'Registration Open Date/Time',
            'registrant_list_visibility': 'Registrant List Visibility',
            'allowed_member_types': 'Allowed Member Types',
        }
        help_texts = {
            'allowed_member_types': 'Select which member types can register for this event. Leave empty to allow all types.',
        }

    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')

        if start_datetime and end_datetime:
            if end_datetime <= start_datetime:
                raise forms.ValidationError('End date and time must be after start date and time.')

        return cleaned_data


class EventRegistrationFeeForm(forms.ModelForm):
    """Form for event registration fees"""
    
    class Meta:
        model = EventRegistrationFee
        fields = ['member_type', 'fee_amount']
        widgets = {
            'member_type': forms.HiddenInput(),  # Hidden since it's determined by allowed_member_types selection
            'fee_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
        labels = {
            'member_type': 'Member Type',
            'fee_amount': 'Fee Amount ($)',
        }
    
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        # Only show active member types (for validation, even though it's hidden)
        queryset = MemberType.objects.filter(is_active=True).order_by('display_order', 'name')
        
        # If editing an existing event, prioritize showing allowed member types
        if self.event and self.event.allowed_member_types.exists():
            # Show allowed types first, then others
            allowed_pks = list(self.event.allowed_member_types.values_list('pk', flat=True))
            queryset = MemberType.objects.filter(is_active=True).order_by('display_order', 'name')
            # Reorder to show allowed types first
            from django.db.models import Case, When, IntegerField
            queryset = queryset.annotate(
                priority=Case(
                    When(pk__in=allowed_pks, then=0),
                    default=1,
                    output_field=IntegerField()
                )
            ).order_by('priority', 'display_order', 'name')
        
        self.fields['member_type'].queryset = queryset


# Custom formset to pass event instance to forms
class BaseEventRegistrationFeeFormSet(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pass event instance to each form
        if self.instance and self.instance.pk:
            for form in self.forms:
                form.event = self.instance

# Create the formset factory
EventRegistrationFeeFormSet = inlineformset_factory(
    Event,
    EventRegistrationFee,
    form=EventRegistrationFeeForm,
    formset=BaseEventRegistrationFeeFormSet,
    extra=0,  # No empty forms - fees are created dynamically when member types are selected
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class EventGuestForm(forms.ModelForm):
    """Form for adding a guest to an event registration"""
    
    class Meta:
        model = EventGuest
        fields = ['name', 'email', 'phone_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guest Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'guest@example.com'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
        }
        labels = {
            'name': 'Guest Name',
            'email': 'Email',
            'phone_number': 'Phone Number',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional - they'll be validated in clean() if any are filled
        self.fields['name'].required = False
        self.fields['email'].required = False
        self.fields['phone_number'].required = False
    
    def has_changed(self):
        """Override to mark empty forms as unchanged"""
        # For formsets, check if this specific form has any data
        if not hasattr(self, 'data') or not self.data:
            return False
        
        # Get the form prefix
        prefix = self.prefix if hasattr(self, 'prefix') else ''
        if prefix:
            # Check if any field has data for this form
            name_key = f'{prefix}-name'
            email_key = f'{prefix}-email'
            phone_key = f'{prefix}-phone_number'
            
            name = self.data.get(name_key, '').strip() if self.data.get(name_key) else ''
            email = self.data.get(email_key, '').strip() if self.data.get(email_key) else ''
            phone = self.data.get(phone_key, '').strip() if self.data.get(phone_key) else ''
            return bool(name or email or phone)
        
        # Fallback: check if any field has data
        return super().has_changed()
    
    def clean(self):
        cleaned_data = super().clean()
        # Skip validation if this form is being deleted
        if self.cleaned_data.get('DELETE'):
            return cleaned_data
        
        name = cleaned_data.get('name', '').strip() if cleaned_data.get('name') else ''
        email = cleaned_data.get('email', '').strip() if cleaned_data.get('email') else ''
        phone_number = cleaned_data.get('phone_number', '').strip() if cleaned_data.get('phone_number') else ''
        
        # If all fields are empty, this is an empty form - allow it
        if not name and not email and not phone_number:
            return cleaned_data
        
        # If any field is filled, name is required
        if email or phone_number:
            if not name:
                raise forms.ValidationError('Guest name is required if email or phone number is provided.')
        
        return cleaned_data


class BaseEventGuestFormSet(forms.BaseFormSet):
    """Custom formset to handle empty forms correctly"""
    def clean(self):
        """Validate forms - empty forms are allowed"""
        if any(self.errors):
            return
        
        # Individual form validation will handle required fields
        # Empty forms are allowed (no validation needed)
        pass

EventGuestFormSet = forms.formset_factory(
    EventGuestForm,
    formset=BaseEventGuestFormSet,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class EventRegistrationForm(forms.ModelForm):
    """Form for registering for an event with optional dependents and guests"""
    
    additional_members = forms.ModelMultipleChoiceField(
        queryset=ClubUser.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Include Child Members',
        help_text='Select any child members (dependents) to include in this registration'
    )
    
    class Meta:
        model = EventRegistration
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes or special requests...'}),
        }
        labels = {
            'notes': 'Notes',
        }
    
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and self.event:
            # Get user's dependent members
            dependents = self.user.dependent_members.filter(is_active=True)
            
            # Filter dependents by allowed member types for this event
            if self.event.allowed_member_types.exists():
                allowed_types = self.event.allowed_member_types.filter(is_active=True)
                # Use a more explicit filter to check if any of the dependent's member types are in allowed types
                allowed_type_pks = list(allowed_types.values_list('pk', flat=True))
                if allowed_type_pks:
                    # Filter dependents whose member_types intersect with allowed types
                    # This checks if the dependent has at least one member type that matches
                    dependents = dependents.filter(member_types__pk__in=allowed_type_pks).distinct()
            else:
                # If no restrictions, all dependents are allowed
                pass
            
            # Evaluate the queryset to a list to ensure it's properly set
            queryset = dependents.order_by('relationship_type', 'last_name', 'first_name')
            self.fields['additional_members'].queryset = queryset
            
            # Update label to show available child members
            queryset_count = queryset.count()
            if queryset_count > 0:
                self.fields['additional_members'].help_text = f'Select any child members to include. {queryset_count} child member(s) available for this event.'
            else:
                # Provide more detailed help text
                total_dependents = self.user.dependent_members.filter(is_active=True).count()
                if total_dependents > 0:
                    # Check if dependents have member types at all
                    dependents_with_types = self.user.dependent_members.filter(
                        is_active=True,
                        member_types__isnull=False
                    ).distinct().count()
                    if dependents_with_types == 0:
                        self.fields['additional_members'].help_text = f'You have {total_dependents} child member(s), but none have member types assigned. Please assign member types to your child members.'
                    else:
                        self.fields['additional_members'].help_text = f'You have {total_dependents} child member(s), but none have member types that are allowed for this event. Please ensure your child members have member types that match the event\'s allowed member types.'
                else:
                    self.fields['additional_members'].help_text = 'No child members available for this event.'
    
    def clean(self):
        cleaned_data = super().clean()
        additional_members = cleaned_data.get('additional_members', [])
        
        if self.event and self.user:
            # Validate that selected dependents have allowed member types
            allowed_types = self.event.get_allowed_member_types()
            for member in additional_members:
                member_types = member.member_types.filter(is_active=True)
                if not any(mt in allowed_types for mt in member_types):
                    raise forms.ValidationError(
                        f'{member.get_full_name()} does not have a member type allowed for this event.'
                    )
        
        return cleaned_data

