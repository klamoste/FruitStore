from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products_app', '0003_product_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='large_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='medium_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='small_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
