from django.contrib import admin
from django.urls import path
from django.urls import path, include
from backendmanagement import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('root/', views.app_index),
]