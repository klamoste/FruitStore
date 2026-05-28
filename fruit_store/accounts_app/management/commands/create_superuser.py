from django.core.management.base import BaseCommand

from django.contrib.auth.models import User

from accounts_app.models import Profile

class Command(BaseCommand):
    help = 'Create or update the store owner superuser account.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            default='admin',
            help='Username for the owner account.',
        )
        parser.add_argument(
            '--email',
            default='admin@example.com',
            help='Email for the owner account.',
        )
        parser.add_argument(
            '--password',
            default='password',
            help='Password for the owner account.',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        user, created = User.objects.get_or_create(username=username, defaults={'email': email})

        if created:
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser created: {username}'))
        else:
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            if password:
                user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser updated: {username}'))

        profile, _ = Profile.objects.get_or_create(user=user, defaults={'role': 'admin'})
        if profile.role != 'admin':
            profile.role = 'admin'
            profile.save(update_fields=['role'])
