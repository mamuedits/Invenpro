"""
URL configuration for stockwise project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth shortcuts
    path('login/', account_views.login_view, name='login'),
    path('staff-login/', account_views.staff_login_view, name='staff_login'),
    path('logout/', account_views.logout_view, name='logout'),
    path('register/', account_views.register_view, name='register'),
    path('forgot-password/', account_views.forgot_password_request_view, name='forgot_password'),
    path('forgot-password/verify/', account_views.forgot_password_verify_view, name='forgot_password_verify'),
    path('forgot-password/reset/', account_views.forgot_password_reset_view, name='forgot_password_reset'),
    path('staff-forgot-password/', account_views.staff_forgot_password_view, name='staff_forgot_password'),
    path('toggle-guest-theme/', account_views.toggle_guest_theme_view, name='toggle_guest_theme'),
    path('staff/', account_views.staff_management_view, name='staff_management'),
    path('admin-management/', account_views.developer_admin_management_view, name='admin_management'),
    path('switch-restaurant/<str:restaurant_id>/', account_views.developer_switch_restaurant_view, name='developer_switch_restaurant'),
    path('profile/', account_views.profile_view, name='profile'),
    path('settings/', account_views.settings_view, name='settings'),
    path('settings/toggle-theme/', account_views.toggle_theme_quick_view, name='toggle_theme_quick'),
    path('accounts/', include('accounts.urls')),
    
    # App routes
    path('transactions/', include('transactions.urls')),
    path('expenses/', include('expenses.urls')),
    path('reports/', include('reports.urls')),
    path('', include('inventory.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
