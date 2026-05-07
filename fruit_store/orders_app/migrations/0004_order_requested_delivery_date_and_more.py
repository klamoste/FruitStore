import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders_app', '0003_orderitem_size_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='requested_delivery_date',
            field=models.DateField(default=datetime.date(2026, 5, 7)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='requested_delivery_time',
            field=models.TimeField(default=datetime.time(9, 0)),
            preserve_default=False,
        ),
    ]
