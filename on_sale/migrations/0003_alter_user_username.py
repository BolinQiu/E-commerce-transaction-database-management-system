# Generated by Django 5.1.1 on 2024-11-08 00:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("on_sale", "0002_logistics_order_orderitem_product_review_user_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="username",
            field=models.CharField(max_length=50, unique=True, verbose_name="用户名"),
        ),
    ]
