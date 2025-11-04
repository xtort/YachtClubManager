from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management.color import no_style


class Command(BaseCommand):
    help = 'Fix migration history inconsistency by updating django_migrations table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force the fix without confirmation',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            '\nThis will modify the django_migrations table to fix dependency issues.\n'
        ))
        
        if not options['force']:
            confirm = input('Do you want to continue? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Aborted.'))
                return

        with connection.cursor() as cursor:
            # Check if ManagementApp tables exist
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'ManagementApp_role'
                );
            """)
            tables_exist = cursor.fetchone()[0]

            # Check if ManagementApp.0001_initial exists in migrations table
            cursor.execute(
                "SELECT COUNT(*) FROM django_migrations WHERE app = 'ManagementApp' AND name = '0001_initial'"
            )
            mgmt_in_history = cursor.fetchone()[0] > 0

            # Check if admin.0001_initial exists
            cursor.execute(
                "SELECT COUNT(*) FROM django_migrations WHERE app = 'admin' AND name = '0001_initial'"
            )
            admin_in_history = cursor.fetchone()[0] > 0

            self.stdout.write(f'\nCurrent state:')
            self.stdout.write(f'  - ManagementApp tables exist: {tables_exist}')
            self.stdout.write(f'  - ManagementApp.0001_initial in history: {mgmt_in_history}')
            self.stdout.write(f'  - admin.0001_initial in history: {admin_in_history}')

            if tables_exist and not mgmt_in_history:
                # Tables exist but migration not recorded - mark as applied
                self.stdout.write('\nMarking ManagementApp.0001_initial as applied...')
                cursor.execute(
                    """
                    INSERT INTO django_migrations (app, name, applied)
                    VALUES ('ManagementApp', '0001_initial', NOW())
                    """
                )
                self.stdout.write(self.style.SUCCESS('✓ ManagementApp.0001_initial marked as applied'))
            elif not tables_exist:
                # Check if admin tables exist
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'django_admin_log'
                    );
                """)
                admin_tables_exist = cursor.fetchone()[0]
                
                if admin_tables_exist:
                    # Admin tables exist - we need to keep admin migrations and mark ManagementApp as applied first
                    self.stdout.write('\nAdmin tables already exist. Marking ManagementApp.0001_initial as applied...')
                    if not mgmt_in_history:
                        cursor.execute(
                            """
                            INSERT INTO django_migrations (app, name, applied)
                            VALUES ('ManagementApp', '0001_initial', NOW())
                            """
                        )
                        self.stdout.write(self.style.SUCCESS('✓ ManagementApp.0001_initial marked as applied'))
                else:
                    # Remove admin migration so we can create ManagementApp first
                    if admin_in_history:
                        self.stdout.write('\nRemoving admin.0001_initial from history...')
                        cursor.execute(
                            "DELETE FROM django_migrations WHERE app = 'admin' AND name = '0001_initial'"
                        )
                        self.stdout.write(self.style.SUCCESS('✓ admin.0001_initial removed'))
                        
                        # Also remove any other admin migrations that depend on it
                        cursor.execute(
                            "DELETE FROM django_migrations WHERE app = 'admin'"
                        )
                        self.stdout.write(self.style.SUCCESS('✓ All admin migrations removed'))

        self.stdout.write(self.style.SUCCESS(
            '\n✓ Migration history fixed!\n'
        ))
        self.stdout.write('Now run: python manage.py migrate')

