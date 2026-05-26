from django.db import migrations, models


def seed_delivery_zones(apps, schema_editor):
    DeliveryZone = apps.get_model('orders_app', 'DeliveryZone')
    defaults = [
        {
            'name': 'Nearby Zone',
            'city': 'Quezon City',
            'state': 'Metro Manila',
            'fee': '50.00',
            'estimated_min_days': 0,
            'estimated_max_days': 1,
            'priority': 10,
        },
        {
            'name': 'Metro Zone',
            'city': 'Taguig',
            'state': 'Metro Manila',
            'fee': '80.00',
            'estimated_min_days': 1,
            'estimated_max_days': 2,
            'priority': 20,
        },
        {
            'name': 'Extended Zone',
            'city': 'Antipolo',
            'state': 'Rizal',
            'fee': '120.00',
            'estimated_min_days': 2,
            'estimated_max_days': 3,
            'priority': 30,
        },
        {
            'name': 'Provincial Zone',
            'city': '',
            'state': 'Surigao del Norte',
            'fee': '180.00',
            'estimated_min_days': 2,
            'estimated_max_days': 4,
            'priority': 90,
        },
    ]

    for item in defaults:
        DeliveryZone.objects.get_or_create(
            name=item['name'],
            city=item['city'],
            state=item['state'],
            defaults=item,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('orders_app', '0005_order_fulfillment_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='assigned_courier',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='order',
            name='internal_note',
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name='DeliveryZone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('state', models.CharField(blank=True, max_length=100)),
                ('fee', models.DecimalField(decimal_places=2, max_digits=10)),
                ('estimated_min_days', models.PositiveSmallIntegerField(default=1)),
                ('estimated_max_days', models.PositiveSmallIntegerField(default=2)),
                ('active', models.BooleanField(default=True)),
                ('priority', models.PositiveSmallIntegerField(default=100)),
            ],
            options={
                'ordering': ['priority', 'name'],
            },
        ),
        migrations.RunPython(seed_delivery_zones, migrations.RunPython.noop),
    ]
