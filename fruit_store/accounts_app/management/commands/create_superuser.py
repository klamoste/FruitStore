from django.core.management.base import BaseCommand

from django.contrib.auth.models import User

from accounts_app.models import Profile

class Command(BaseCommand):

    def handle(self, *args, **options):

        if not User.objects.filter(username='admin').exists():

            user = User.objects.create_superuser('admin', 'admin@example.com', 'password')

            Profile.objects.create(user=user, role='admin')

            self.stdout.write('Superuser created')

        else:

            self.stdout.write('Superuser already exists')