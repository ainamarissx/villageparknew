# Generated by Django 5.0 on 2024-10-12 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("queuingsystem", "0021_order_orderhistory"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="queue_number",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
