# Generated by Django 5.1.1 on 2024-11-08 11:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("on_sale", "0005_remove_user_groups_remove_user_is_superuser_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="logistics",
            name="status",
            field=models.CharField(
                choices=[("pending", "待发货"), ("delivered", "已送达")],
                max_length=20,
                verbose_name="物流状态",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[("pending", "待发货"), ("delivered", "已送达")],
                max_length=20,
                verbose_name="订单状态",
            ),
        ),
    ]
