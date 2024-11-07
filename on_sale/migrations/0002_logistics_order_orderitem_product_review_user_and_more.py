# Generated by Django 5.1.2 on 2024-11-07 23:52

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('on_sale', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Logistics',
            fields=[
                ('logistics_id', models.AutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', '待发货'), ('shipping', '运输中'), ('delivered', '已送达')], max_length=20, verbose_name='物流状态')),
                ('carrier', models.CharField(blank=True, max_length=50, null=True, verbose_name='承运人')),
                ('tracking_number', models.CharField(blank=True, max_length=100, null=True, verbose_name='追踪号码')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='状态更新时间')),
            ],
            options={
                'verbose_name': '物流单',
                'verbose_name_plural': '物流单',
                'db_table': 'logistics',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('order_id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='订单创建时间')),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='订单总金额')),
                ('status', models.CharField(choices=[('pending', '待付款'), ('paid', '已付款'), ('shipped', '已发货'), ('completed', '已完成'), ('cancelled', '已取消')], max_length=20, verbose_name='订单状态')),
                ('estimated_delivery_date', models.DateField(blank=True, null=True, verbose_name='预计送达日期')),
                ('carrier', models.CharField(blank=True, max_length=50, null=True, verbose_name='承运人')),
                ('shipping_address', models.CharField(max_length=255, verbose_name='收件人地址')),
                ('shipping_phone', models.CharField(max_length=20, verbose_name='收件人电话')),
            ],
            options={
                'verbose_name': '订单',
                'verbose_name_plural': '订单',
                'db_table': 'orders',
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('order_item_id', models.AutoField(primary_key=True, serialize=False)),
                ('quantity', models.IntegerField(verbose_name='商品数量')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='商品单价')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='on_sale.order', verbose_name='订单')),
            ],
            options={
                'verbose_name': '订单项',
                'verbose_name_plural': '订单项',
                'db_table': 'order_items',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('product_id', models.AutoField(primary_key=True, serialize=False)),
                ('product_name', models.CharField(max_length=100, verbose_name='商品名称')),
                ('product_description', models.TextField(blank=True, null=True, verbose_name='商品描述')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='商品单价')),
                ('stock', models.IntegerField(verbose_name='库存数量')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='上架时间')),
            ],
            options={
                'verbose_name': '商品',
                'verbose_name_plural': '商品',
                'db_table': 'products',
            },
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('review_id', models.AutoField(primary_key=True, serialize=False)),
                ('rating', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='评分')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='评论内容')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='评价时间')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='on_sale.product', verbose_name='商品')),
            ],
            options={
                'verbose_name': '评价',
                'verbose_name_plural': '评价',
                'db_table': 'reviews',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('user_id', models.AutoField(primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=50, verbose_name='用户名')),
                ('password', models.CharField(max_length=255, verbose_name='密码')),
                ('address', models.CharField(max_length=255, verbose_name='寄件地址')),
                ('phone', models.CharField(max_length=20, verbose_name='电话号码')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='注册时间')),
            ],
            options={
                'verbose_name': '用户',
                'verbose_name_plural': '用户',
                'db_table': 'users',
            },
        ),
        migrations.DeleteModel(
            name='Student',
        ),
        migrations.AddField(
            model_name='logistics',
            name='order',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='on_sale.order', verbose_name='订单'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='on_sale.product', verbose_name='商品'),
        ),
        migrations.AddField(
            model_name='review',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='on_sale.user', verbose_name='用户'),
        ),
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='on_sale.user', verbose_name='用户'),
        ),
    ]
