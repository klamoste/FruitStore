import uuid

from django.db import migrations, models


def populate_order_codes(apps, schema_editor):
    Order = apps.get_model('orders_app', 'Order')
    for order in Order.objects.filter(order_code__isnull=True):
        code = f"ORD-{uuid.uuid4().hex[:10].upper()}"
        while Order.objects.filter(order_code=code).exists():
            code = f"ORD-{uuid.uuid4().hex[:10].upper()}"
        order.order_code = code
        order.save(update_fields=['order_code'])


class Migration(migrations.Migration):

    dependencies = [
        ('orders_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='customer_note',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='order_code',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('paid', 'Paid'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='pending', max_length=10),
        ),
        migrations.RunPython(populate_order_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='order',
            name='order_code',
            field=models.CharField(blank=True, max_length=20, unique=True),
        ),
    ]
