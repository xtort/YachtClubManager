from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.utils import timezone as django_timezone


# Choice constants for ClubUser
SALUTATION_CHOICES = [
    ('', ''),
    ('Adm.', 'Adm.'),
    ('Assoc. Prof.', 'Assoc. Prof.'),
    ('Capt.', 'Capt.'),
    ('Col.', 'Col.'),
    ('Commodore', 'Commodore'),
    ('Decon', 'Decon'),
    ('Dr.', 'Dr.'),
    ('Father', 'Father'),
    ('Fleet Captain', 'Fleet Captain'),
    ('Gen.', 'Gen.'),
    ('Hon.', 'Hon.'),
    ('Judge', 'Judge'),
    ('Lady', 'Lady'),
    ('Maj.', 'Maj.'),
    ('Mayor', 'Mayor'),
    ('Miss', 'Miss'),
    ('Mr.', 'Mr.'),
    ('Mrs.', 'Mrs.'),
    ('Ms.', 'Ms.'),
    ('PC', 'PC'),
    ('Prof.', 'Prof.'),
    ('Rabbi', 'Rabbi'),
    ('Rear Adm.', 'Rear Adm.'),
    ('Rear Commoder', 'Rear Commoder'),
    ('Rep.', 'Rep.'),
    ('Rev.', 'Rev.'),
    ('Sen.', 'Sen.'),
    ('Sgt.', 'Sgt.'),
    ('Teen', 'Teen'),
    ('Vice-Commodore', 'Vice-Commodore'),
]

VESSEL_TYPE_CHOICES = [
    ('', ''),
    ('Motor', 'Motor'),
    ('Sailboat', 'Sailboat'),
]

VESSEL_POWER_CHOICES = [
    ('', ''),
    ('30a', '30a'),
    ('50a', '50a'),
    ('2x30a or 50a', '2x30a or 50a'),
]

VESSEL_TIE_CHOICES = [
    ('', ''),
    ('bow in starboard', 'Bow In Starboard'),
    ('bow in port', 'Bow In Port'),
    ('stern in starboard', 'Stern In Starboard'),
    ('stern in port', 'Stern In Port'),
]

# US States for dropdown
US_STATES = [
    ('', ''),
    ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'),
    ('CA', 'California'), ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'),
    ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'),
    ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'), ('KS', 'Kansas'),
    ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'),
    ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'),
    ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'),
    ('NH', 'New Hampshire'), ('NJ', 'New Jersey'), ('NM', 'New Mexico'), ('NY', 'New York'),
    ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'),
    ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'),
    ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'),
    ('VT', 'Vermont'), ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'),
    ('WI', 'Wisconsin'), ('WY', 'Wyoming'),
]

# Common countries (can be expanded)
COUNTRIES = [
    ('', ''),
    ('US', 'United States'),
    ('CA', 'Canada'),
    ('MX', 'Mexico'),
    ('GB', 'United Kingdom'),
    ('AU', 'Australia'),
    ('NZ', 'New Zealand'),
    ('FR', 'France'),
    ('DE', 'Germany'),
    ('IT', 'Italy'),
    ('ES', 'Spain'),
    ('NL', 'Netherlands'),
    ('BE', 'Belgium'),
    ('CH', 'Switzerland'),
    ('SE', 'Sweden'),
    ('NO', 'Norway'),
    ('DK', 'Denmark'),
    ('FI', 'Finland'),
    ('IE', 'Ireland'),
    ('PT', 'Portugal'),
    ('GR', 'Greece'),
    ('TR', 'Turkey'),
    ('JP', 'Japan'),
    ('CN', 'China'),
    ('IN', 'India'),
    ('BR', 'Brazil'),
    ('AR', 'Argentina'),
    ('ZA', 'South Africa'),
    ('EG', 'Egypt'),
    ('TH', 'Thailand'),
]


class Role(models.Model):
    """Role-Based Access Control roles"""
    ROLE_CHOICES = [
        ('viewer', 'View Only'),
        ('member', 'Member'),
        ('editor', 'Editor'),
        ('admin', 'Admin'),
    ]
    
    name = models.CharField(max_length=50, unique=True, choices=ROLE_CHOICES)
    description = models.TextField(blank=True)
    can_view_events = models.BooleanField(default=True)
    can_create_events = models.BooleanField(default=False)
    can_edit_events = models.BooleanField(default=False)
    can_delete_events = models.BooleanField(default=False)
    can_manage_categories = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    can_access_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()

    @classmethod
    def get_viewer_role(cls):
        """Get or create the viewer role"""
        role, _ = cls.objects.get_or_create(
            name='viewer',
            defaults={
                'description': 'Can view events and calendar only',
                'can_view_events': True,
            }
        )
        return role

    @classmethod
    def get_member_role(cls):
        """Get or create the member role"""
        role, _ = cls.objects.get_or_create(
            name='member',
            defaults={
                'description': 'Can view events and manage own profile',
                'can_view_events': True,
            }
        )
        return role

    @classmethod
    def get_editor_role(cls):
        """Get or create the editor role"""
        role, _ = cls.objects.get_or_create(
            name='editor',
            defaults={
                'description': 'Can view and create/edit/delete events',
                'can_view_events': True,
                'can_create_events': True,
                'can_edit_events': True,
                'can_delete_events': True,
                'can_manage_categories': True,
            }
        )
        return role

    @classmethod
    def get_admin_role(cls):
        """Get or create the admin role"""
        role, _ = cls.objects.get_or_create(
            name='admin',
            defaults={
                'description': 'Full access to all features',
                'can_view_events': True,
                'can_create_events': True,
                'can_edit_events': True,
                'can_delete_events': True,
                'can_manage_categories': True,
                'can_manage_users': True,
                'can_access_admin': True,
            }
        )
        return role


class ClubUserManager(BaseUserManager):
    """Custom user manager for ClubUser"""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with hashed password"""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # This handles salting and hashing automatically
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class ClubUser(AbstractBaseUser, PermissionsMixin):
    """Custom user model for Yacht Club members"""
    
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    
    # General Information
    salutation = models.CharField(max_length=20, choices=SALUTATION_CHOICES, blank=True)
    middle_initial = models.CharField(max_length=1, blank=True)
    professional_designation = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True, help_text='Year is stored but not displayed publicly')
    nickname = models.CharField(max_length=100, blank=True)
    
    # Contact information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    primary_phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    # Spouse Information
    spouse_first_name = models.CharField(max_length=150, blank=True)
    spouse_last_name = models.CharField(max_length=150, blank=True)
    
    # Primary Address
    country = models.CharField(max_length=2, choices=COUNTRIES, blank=True)
    address1 = models.CharField(max_length=255, blank=True)
    address2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, choices=US_STATES, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    timezone = models.CharField(max_length=50, blank=True, help_text='e.g., America/New_York')
    secondary_phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    # Work Information
    company = models.CharField(max_length=255, blank=True)
    occupation_title = models.CharField(max_length=255, blank=True)
    work_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    # Vessel Information
    vessel_type = models.CharField(max_length=20, choices=VESSEL_TYPE_CHOICES, blank=True)
    vessel_name = models.CharField(max_length=255, blank=True)
    vessel_moorage_location = models.CharField(max_length=255, blank=True, help_text='Moorage location')
    vessel_manufacturer = models.CharField(max_length=255, blank=True, help_text='Manufacturer/builder of boat')
    vessel_model = models.CharField(max_length=255, blank=True, help_text='Model of boat')
    vessel_loa = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='Length Overall in feet')
    vessel_beam = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='Beam in feet')
    vessel_draft = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='Draft in feet')
    vessel_cruising_speed = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Average cruising speed in knots')
    vessel_power_requirements = models.CharField(max_length=20, choices=VESSEL_POWER_CHOICES, blank=True)
    vessel_tie_preferences = models.CharField(max_length=30, choices=VESSEL_TIE_CHOICES, blank=True)
    
    # Photo uploads
    member_photo = models.ImageField(upload_to='member_photos/', blank=True, null=True)
    vessel_photo = models.ImageField(upload_to='vessel_photos/', blank=True, null=True)
    
    # Role and permissions
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    
    # Account status
    is_active = models.BooleanField(default=True, help_text='Designates whether this user can log in.')
    is_staff = models.BooleanField(default=False, help_text='Designates whether the user can log into admin site.')
    
    # Timestamps
    date_joined = models.DateTimeField(default=django_timezone.now)
    last_login = models.DateTimeField(null=True, blank=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ClubUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'Club User'
        verbose_name_plural = 'Club Users'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        """Return the full name"""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        """Return the short name"""
        return self.first_name

    def get_display_name(self):
        """Return display name with salutation if available"""
        if self.salutation:
            return f"{self.salutation} {self.get_full_name()}".strip()
        return self.get_full_name()

    def get_date_of_birth_display(self):
        """Return date of birth without year (MM/DD format)"""
        if self.date_of_birth:
            return self.date_of_birth.strftime('%m/%d')
        return None

    def has_permission(self, permission):
        """Check if user has a specific permission based on their role"""
        # Superusers have all permissions
        if self.is_superuser:
            return True
        
        if not self.role:
            return False
        
        permission_map = {
            'view_events': self.role.can_view_events,
            'create_events': self.role.can_create_events,
            'edit_events': self.role.can_edit_events,
            'delete_events': self.role.can_delete_events,
            'manage_categories': self.role.can_manage_categories,
            'manage_users': self.role.can_manage_users,
            'access_admin': self.role.can_access_admin,
        }
        
        return permission_map.get(permission, False)
