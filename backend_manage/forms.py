# backend_manage/forms.py

from django import forms

class ModifyProductForm(forms.Form):
    # product_id = forms.IntegerField(label='商品ID')
    product_description = forms.CharField(widget=forms.Textarea, required=False, label='商品描述')
    price = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label='单价')

class AddProductForm(forms.Form):
    product_name = forms.CharField(max_length=100, label='商品名称')
    product_description = forms.CharField(widget=forms.Textarea, required=False, label='商品描述')
    price = forms.DecimalField(max_digits=10, decimal_places=2, label='单价')
    stock = forms.IntegerField(label='库存数量')

class AddStockForm(forms.Form):
    product_id = forms.IntegerField(label='商品ID')
    additional_stock = forms.IntegerField(label='增加库存数量')

class AssignLogisticsForm(forms.Form):
    order_id = forms.IntegerField(label='订单ID')
    carrier = forms.CharField(max_length=50, label='承运人')
    tracking_number = forms.CharField(max_length=100, label='追踪号码')

class QueryProductForm(forms.Form):
    min_stock = forms.IntegerField(required=False, label='最小库存数量')
    max_stock = forms.IntegerField(required=False, label='最大库存数量')
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label='上架开始时间')
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label='上架结束时间')
    min_price = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label='最低价格')
    max_price = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label='最高价格')

class QueryOrderForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label='订单创建开始时间')
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label='订单创建结束时间')
    tracking_number = forms.CharField(max_length=100, required=False, label='物流追踪号码')

class QueryReviewForm(forms.Form):
    product_name = forms.CharField(max_length=100, required=True, label='商品名称')
