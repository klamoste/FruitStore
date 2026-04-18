from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products_app', '0002_expand_product_units'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='size',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', 'No size'),
                    ('small', 'Small'),
                    ('medium', 'Medium'),
                    ('large', 'Large'),
                ],
                default='',
                max_length=10,
            ),
        ),
    ]
