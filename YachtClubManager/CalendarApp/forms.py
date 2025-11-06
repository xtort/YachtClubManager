from django import forms
from django.forms import inlineformset_factory
from ckeditor.widgets import CKEditorWidget
from .models import Event, EventCategory, EventContact
from django.contrib.auth import get_user_model

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
        widget=CKEditorWidget(),
        required=False,
        help_text='Full formatted description with rich text editor'
    )

    class Meta:
        model = Event
        fields = ['title', 'short_description', 'category', 'start_datetime', 'end_datetime', 'formatted_description', 'registration_status', 'registration_open_datetime', 'registrant_list_visibility']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Event Title'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'start_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'registration_status': forms.Select(attrs={'class': 'form-control'}),
            # This is the date that the event will automatically open for registration. If left blank, the event will have to be manually opened for registration.
            'registration_open_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'registrant_list_visibility': forms.Select(attrs={'class': 'form-control'}),
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
        }

    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')

        if start_datetime and end_datetime:
            if end_datetime <= start_datetime:
                raise forms.ValidationError('End date and time must be after start date and time.')

        return cleaned_data

