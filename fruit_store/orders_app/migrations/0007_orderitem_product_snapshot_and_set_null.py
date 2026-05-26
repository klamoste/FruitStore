from django.db import migrations, models
import django.db.models.deletion


def copy_product_snapshots(apps, schema_editor):
    OrderItem = apps.get_model('orders_app', 'OrderItem')

    for item in OrderItem.objects.select_related('product', 'product__category'):
        product = item.product
        if product is None:
            continue
        item.product_name = product.name
        item.product_category_name = product.category.name if product.category_id else ''
        item.product_unit = product.unit
        item.save(update_fields=['product_name', 'product_category_name', 'product_unit'])


class Migration(migrations.Migration):

    dependencies = [
        ('orders_app', '0006_deliveryzone_order_assigned_courier_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='product_category_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='product_name',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='product_unit',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products_app.product'),
        ),
        migrations.RunPython(copy_product_snapshots, migrations.RunPython.noop),
    ]
