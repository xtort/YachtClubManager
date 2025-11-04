from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Mark admin migrations as applied without running them (use when tables already exist)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            '\nThis will mark all admin migrations as applied.\n'
            'Use this if admin tables already exist in your database.\n'
        ))
        
        with connection.cursor() as cursor:
            # Check if admin tables exist
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'django_admin_log'
                );
            """)
            admin_tables_exist = cursor.fetchone()[0]
            
            if not admin_tables_exist:
                self.stdout.write(self.style.ERROR(
                    'Admin tables do not exist. Run: python manage.py migrate'
                ))
                return
            
            # Get all admin migration files
            from django.db.migrations.loader import MigrationLoader
            loader = MigrationLoader(connection)
            admin_migrations = [
                (app, name) for app, name in loader.disk_migrations.keys()
                if app == 'admin'
            ]
            
            # Mark them as applied
            applied_count = 0
            for app, name in sorted(admin_migrations):
                cursor.execute(
                    "SELECT COUNT(*) FROM django_migrations WHERE app = %s AND name = %s",
                    [app, name]
                )
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        """
                        INSERT INTO django_migrations (app, name, applied)
                        VALUES (%s, %s, NOW())
                        """,
                        [app, name]
                    )
                    applied_count += 1
                    self.stdout.write(f'  ✓ Marked {app}.{name} as applied')
            
            if applied_count > 0:
                self.stdout.write(self.style.SUCCESS(
                    f'\n✓ Marked {applied_count} admin migration(s) as applied'
                ))
            else:
                self.stdout.write('\nAll admin migrations are already marked as applied.')
            
        self.stdout.write('\nNow run: python manage.py migrate')

