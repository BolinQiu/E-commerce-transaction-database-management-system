from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# 用户表
class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    # username = models.CharField(max_length=50, unique=True, verbose_name='用户名')
    username = models.CharField(max_length=50, unique=True, verbose_name='用户名',null=False)
    password = models.CharField(max_length=255, verbose_name='密码',null=False)
    address = models.CharField(max_length=255, verbose_name='寄件地址',null=False)
    phone = models.CharField(max_length=20, verbose_name='电话号码',null=False)
    created_at = models.DateTimeField(default=timezone.now, verbose_name='注册时间')
    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'

# 商品表
class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=100, verbose_name='商品名称',null=False)
    product_description = models.TextField(null=True, blank=True, verbose_name='商品描述')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品单价',null=False)
    stock = models.IntegerField(verbose_name='库存数量',null=False)
    created_at = models.DateTimeField(default=timezone.now, verbose_name='上架时间')

    class Meta:
        db_table = 'products'
        verbose_name = '商品'
        verbose_name_plural = '商品'

# 订单表
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', '待付款'),
        ('paid', '已付款'),
        ('shipped', '已发货'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    order_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='订单创建时间')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='订单总金额')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='订单状态')
    estimated_delivery_date = models.DateField(null=True, blank=True, verbose_name='预计送达日期')
    carrier = models.CharField(max_length=50, null=True, blank=True, verbose_name='承运人')
    shipping_address = models.CharField(max_length=255, verbose_name='收件人地址')
    shipping_phone = models.CharField(max_length=20, verbose_name='收件人电话')

    class Meta:
        db_table = 'orders'
        verbose_name = '订单'
        verbose_name_plural = '订单'

# 订单项表
class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='订单')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='商品')
    quantity = models.IntegerField(verbose_name='商品数量')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品单价')

    class Meta:
        db_table = 'order_items'
        verbose_name = '订单项'
        verbose_name_plural = '订单项'

# 物流单表
class Logistics(models.Model):
    STATUS_CHOICES = [
        ('pending', '待发货'),
        ('shipping', '运输中'),
        ('delivered', '已送达'),
    ]
    
    logistics_id = models.AutoField(primary_key=True)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, verbose_name='订单')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='物流状态')
    carrier = models.CharField(max_length=50, null=True, blank=True, verbose_name='承运人')
    tracking_number = models.CharField(max_length=100, null=True, blank=True, verbose_name='追踪号码')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='状态更新时间')

    class Meta:
        db_table = 'logistics'
        verbose_name = '物流单'
        verbose_name_plural = '物流单'

# 评价表
class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='商品')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='评分'
    )
    comment = models.TextField(null=True, blank=True, verbose_name='评论内容')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='评价时间')

    class Meta:
        db_table = 'reviews'
        verbose_name = '评价'
        verbose_name_plural = '评价'