from django.contrib import admin
from django.urls import path
from django.urls import path, include
from on_sale import views

urlpatterns = [
 
    path('on_sale/', views.app_index, name='on_sale'),
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('api/products/', views.get_products, name='get_products'),
    path('api/products/search/', views.search_products, name='search_products'),
         # API路径
    path('api/orders/', views.create_order, name='create_order'),
    # 其他路径...
    path('logout/', views.logout_view, name='logout'),
    path('api/purchases/', views.get_purchases, name='get_purchases'),  # 添加此行
    path('api/profile/update/', views.update_profile, name='update_profile'),  # 添加此行
    path('api/profile/', views.get_profile, name='get_profile'),
    path('get_order_items/', views.get_order_items, name='get_order_items'),
    path('submit_review/', views.submit_review, name='submit_review'),
    path('api/reviews/', views.get_reviews, name='get_reviews'),  # 新增
]


