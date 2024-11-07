from django.db import models
from django.utils import timezone

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='用户名'
    )
    password = models.CharField(
        max_length=255,
        verbose_name='密码'
    )
    address = models.CharField(
        max_length=255,
        verbose_name='寄件地址'
    )
    phone = models.CharField(
        max_length=20,
        verbose_name='电话号码'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='注册时间'
    )

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return self.username
    

