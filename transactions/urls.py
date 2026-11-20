from django.urls import path
from . import views

urlpatterns = [
    path('', views.transaction_list_view, name='transaction_list'),
    path('in/', views.stock_in_view, name='stock_in'),
    path('out/', views.stock_out_view, name='stock_out'),
    path('adjust/', views.stock_adjustment_view, name='stock_adjustment'),
]

