from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_overview_view, name='report_overview'),
    path('export/stock-in-csv/', views.export_stock_in_csv, name='export_stock_in_csv'),
    path('export/stock-out-csv/', views.export_stock_out_csv, name='export_stock_out_csv'),
    path('export/inventory-valuation-csv/', views.export_inventory_valuation_csv, name='export_inventory_valuation_csv'),
    path('export/expenses-csv/', views.export_expenses_csv, name='export_expenses_csv'),
]

