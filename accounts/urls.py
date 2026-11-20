from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('staff-login/', views.staff_login_view, name='staff_login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_request_view, name='forgot_password'),
    path('forgot-password/verify/', views.forgot_password_verify_view, name='forgot_password_verify'),
    path('forgot-password/reset/', views.forgot_password_reset_view, name='forgot_password_reset'),
    path('staff-forgot-password/', views.staff_forgot_password_view, name='staff_forgot_password'),
    path('toggle-guest-theme/', views.toggle_guest_theme_view, name='toggle_guest_theme'),
    path('profile/', views.profile_view, name='profile'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/toggle-theme/', views.toggle_theme_quick_view, name='toggle_theme_quick'),
    path('staff/', views.staff_management_view, name='staff_management'),
    path('staff/<int:staff_id>/reset-password/', views.reset_staff_password_view, name='reset_staff_password'),
    path('staff/<int:staff_id>/delete/', views.delete_staff_view, name='delete_staff'),
    path('admin-management/', views.developer_admin_management_view, name='admin_management'),
    path('admin-management/<int:user_id>/edit/', views.developer_edit_admin_view, name='edit_admin'),
    path('admin-management/<int:user_id>/promote/', views.promote_to_developer_view, name='promote_to_developer'),
    path('admin-management/<int:user_id>/delete/', views.developer_delete_admin_view, name='delete_admin'),
    path('admin-management/restaurant/<int:restaurant_id>/delete/', views.developer_delete_restaurant_view, name='delete_restaurant'),
    path('switch-restaurant/<str:restaurant_id>/', views.developer_switch_restaurant_view, name='developer_switch_restaurant'),
    path('users/', views.user_management_view, name='user_management'),
    path('users/<int:user_id>/toggle-role/', views.toggle_user_role_view, name='toggle_user_role'),
]
