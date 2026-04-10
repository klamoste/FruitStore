from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts_app', '0002_profile_address_profile_city_profile_contact_number_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/'),
        ),
    ]
