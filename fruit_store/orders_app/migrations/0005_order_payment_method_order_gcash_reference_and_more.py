from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders_app', '0004_order_requested_delivery_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='gcash_reference',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='order',
            name='gcash_sender_name',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('COD', 'Cash on Delivery'), ('GCASH', 'GCash')], default='COD', max_length=10),
        ),
    ]
