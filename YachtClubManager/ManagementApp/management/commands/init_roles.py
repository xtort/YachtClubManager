from django.core.management.base import BaseCommand
from ManagementApp.models import Role


class Command(BaseCommand):
    help = 'Initialize default RBAC roles (Viewer, Member, Editor, Admin)'

    def handle(self, *args, **options):
        self.stdout.write('Creating default roles...')
        
        viewer_role = Role.get_viewer_role()
        self.stdout.write(self.style.SUCCESS(f'✓ Viewer role created/verified: {viewer_role.get_name_display()}'))
        
        member_role = Role.get_member_role()
        self.stdout.write(self.style.SUCCESS(f'✓ Member role created/verified: {member_role.get_name_display()}'))
        
        editor_role = Role.get_editor_role()
        self.stdout.write(self.style.SUCCESS(f'✓ Editor role created/verified: {editor_role.get_name_display()}'))
        
        admin_role = Role.get_admin_role()
        self.stdout.write(self.style.SUCCESS(f'✓ Admin role created/verified: {admin_role.get_name_display()}'))
        
        self.stdout.write(self.style.SUCCESS('\nAll default roles have been initialized successfully!'))

