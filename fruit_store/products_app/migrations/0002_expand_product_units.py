from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='unit',
            field=models.CharField(
                choices=[
                    ('kg', 'Kilogram'),
                    ('piece', 'Piece'),
                    ('bundle', 'Bundle'),
                    ('bottle', 'Bottle'),
                    ('cup', 'Cup'),
                    ('liter', 'Liter'),
                ],
                max_length=10,
            ),
        ),
    ]
