from django.urls import path
from . import views

urlpatterns = [
    path('', views.expense_list_view, name='expense_list'),
    path('add/', views.expense_create_view, name='expense_create'),
    path('<int:pk>/edit/', views.expense_update_view, name='expense_update'),
    path('<int:pk>/delete/', views.expense_delete_view, name='expense_delete'),
]

