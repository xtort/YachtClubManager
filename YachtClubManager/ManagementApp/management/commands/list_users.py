from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

ClubUser = get_user_model()


class Command(BaseCommand):
    help = 'List all users in the database'

    def handle(self, *args, **options):
        users = ClubUser.objects.all().order_by('email')
        
        if not users.exists():
            self.stdout.write(self.style.WARNING('No users found in the database.'))
            return
        
        self.stdout.write(f'\nFound {users.count()} user(s):\n')
        
        for user in users:
            status = []
            if user.is_superuser:
                status.append('Superuser')
            if user.is_staff:
                status.append('Staff')
            if user.is_active:
                status.append('Active')
            else:
                status.append('Inactive')
            
            role_str = f"Role: {user.role.get_name_display()}" if user.role else "No role assigned"
            status_str = " | ".join(status)
            
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  Name: {user.get_full_name()}')
            self.stdout.write(f'  {role_str}')
            self.stdout.write(f'  Status: {status_str}')
            self.stdout.write(f'  Password set: {"Yes" if user.password else "No"}')
            self.stdout.write(f'  Last login: {user.last_login or "Never"}')
            self.stdout.write('')

