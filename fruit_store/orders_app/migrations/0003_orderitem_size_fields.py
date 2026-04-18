from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders_app', '0002_order_order_code_order_customer_note_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='selected_size',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='selected_unit_label',
            field=models.CharField(blank=True, default='', max_length=40),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='unit_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
