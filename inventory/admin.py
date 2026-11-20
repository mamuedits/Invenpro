from django.contrib import admin
from .models import Category, Supplier, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_count', 'created_at')
    search_fields = ('name', 'description')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'created_at')
    search_fields = ('name', 'phone', 'email', 'address')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'current_stock', 'unit', 'purchase_price', 'minimum_stock', 'stock_status')
    list_filter = ('category', 'unit')
    search_fields = ('name', 'category__name')
    readonly_fields = ('created_at', 'updated_at')
