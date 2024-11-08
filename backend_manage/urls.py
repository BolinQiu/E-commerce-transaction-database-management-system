# backend_manage/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.manage_dashboard, name='manage_dashboard'),
    
    # 陈列柜
    path('products/', views.list_products, name='list_products'),
    path('products/modify/', views.modify_product, name='modify_product'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/add_stock/', views.add_stock, name='add_stock'),
    path('products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    
    # 我的订单
    path('orders/', views.list_orders, name='list_orders'),
    path('orders/assign_logistics/', views.assign_logistics, name='assign_logistics'),
    path('orders/track/<int:order_id>/', views.track_order, name='track_order'),
    path('orders/query_by_product/<int:product_id>/', views.query_orders_by_product, name='query_orders_by_product'),
    
    # 用户评论
    path('reviews/', views.list_reviews, name='list_reviews'),
]
