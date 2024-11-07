from django.contrib import admin
from django.urls import path
from django.urls import path, include
from user_account import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.app_index),
]