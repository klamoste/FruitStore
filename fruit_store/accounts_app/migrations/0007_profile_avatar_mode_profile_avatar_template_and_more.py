from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts_app', '0006_remove_profile_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='avatar_mode',
            field=models.CharField(choices=[('template', 'Template'), ('upload', 'Uploaded Photo')], default='template', max_length=10),
        ),
        migrations.AddField(
            model_name='profile',
            name='avatar_template',
            field=models.CharField(choices=[('leaf', 'Leaf'), ('basket', 'Basket'), ('sun', 'Sun'), ('berry', 'Berry')], default='leaf', max_length=20),
        ),
        migrations.AddField(
            model_name='profile',
            name='profile_image',
            field=models.ImageField(blank=True, null=True, upload_to='profiles/'),
        ),
    ]
