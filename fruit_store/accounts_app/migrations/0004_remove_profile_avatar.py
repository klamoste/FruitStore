from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts_app', '0003_profile_avatar'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='avatar',
        ),
    ]
