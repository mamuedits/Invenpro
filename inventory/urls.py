from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    
    # Products
    path('products/', views.product_list_view, name='product_list'),
    path('products/add/', views.product_create_view, name='product_create'),
    path('products/<int:pk>/', views.product_detail_view, name='product_detail'),
    path('products/<int:pk>/edit/', views.product_update_view, name='product_update'),
    path('products/<int:pk>/delete/', views.product_delete_view, name='product_delete'),
    
    # Smart Alerts
    path('smart-alerts/', views.smart_alerts_view, name='smart_alerts'),

    # Categories
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/add/', views.category_create_view, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_update_view, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete_view, name='category_delete'),

    # Suppliers
    path('suppliers/', views.supplier_list_view, name='supplier_list'),
    path('suppliers/add/', views.supplier_create_view, name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.supplier_update_view, name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete_view, name='supplier_delete'),
]

