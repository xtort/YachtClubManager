from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ManagementApp.models import Role
from getpass import getpass

ClubUser = get_user_model()


class Command(BaseCommand):
    help = 'Create a new club user with email authentication'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='User email address')
        parser.add_argument('--first-name', type=str, help='First name')
        parser.add_argument('--last-name', type=str, help='Last name')
        parser.add_argument('--phone', type=str, help='Phone number (optional)')
        parser.add_argument('--role', type=str, choices=['viewer', 'member', 'editor', 'admin'], help='User role')
        parser.add_argument('--no-input', action='store_true', help='Use command-line arguments only')

    def handle(self, *args, **options):
        email = options.get('email')
        first_name = options.get('first_name')
        last_name = options.get('last_name')
        phone = options.get('phone')
        role_name = options.get('role')
        no_input = options.get('no_input')

        # Interactive mode
        if not no_input:
            if not email:
                email = input('Email address: ')
            
            if ClubUser.objects.filter(email=email).exists():
                self.stdout.write(self.style.ERROR(f'User with email {email} already exists!'))
                return

            if not first_name:
                first_name = input('First name: ')
            
            if not last_name:
                last_name = input('Last name: ')
            
            if not phone:
                phone = input('Phone number (optional, press Enter to skip): ') or None
            
            if not role_name:
                self.stdout.write('\nAvailable roles:')
                self.stdout.write('  1. viewer - View Only')
                self.stdout.write('  2. member - Member (can manage own profile)')
                self.stdout.write('  3. editor - Editor')
                self.stdout.write('  4. admin - Admin')
                role_choice = input('\nSelect role (1-4): ')
                role_map = {'1': 'viewer', '2': 'member', '3': 'editor', '4': 'admin'}
                role_name = role_map.get(role_choice, 'viewer')
            
            password = getpass('Password: ')
            password_confirm = getpass('Password (again): ')
            
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('Passwords do not match!'))
                return

        else:
            # Non-interactive mode requires all fields
            if not all([email, first_name, last_name, role_name]):
                self.stdout.write(self.style.ERROR(
                    'In non-interactive mode, you must provide: --email, --first-name, --last-name, --role'
                ))
                return
            password = getpass('Password: ')

        # Get or create the role
        if role_name == 'viewer':
            role = Role.get_viewer_role()
        elif role_name == 'member':
            role = Role.get_member_role()
        elif role_name == 'editor':
            role = Role.get_editor_role()
        elif role_name == 'admin':
            role = Role.get_admin_role()
        else:
            self.stdout.write(self.style.ERROR(f'Invalid role: {role_name}'))
            return

        # Create the user
        try:
            user = ClubUser.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone or '',
                role=role,
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Successfully created user: {user.get_full_name()} ({user.email})'
            ))
            self.stdout.write(f'  Role: {role.get_name_display()}')
            self.stdout.write(f'  Active: {user.is_active}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error creating user: {str(e)}'))

