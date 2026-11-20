from django.contrib import admin
from .models import StockTransaction


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'transaction_type', 'product', 'quantity', 'unit_price', 'total_amount', 'user', 'supplier')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('product__name', 'notes', 'user__username', 'supplier__name')
    readonly_fields = ('created_at',)
