from django.contrib import admin
from .models import PasswordResetOTP, Restaurant, StaffPasswordRequest, UserProfile


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('restaurant_id', 'name', 'owner', 'phone', 'currency', 'created_at')
    search_fields = ('restaurant_id', 'name', 'phone', 'owner__username')
    readonly_fields = ('restaurant_id', 'created_at', 'updated_at')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'restaurant', 'phone', 'business_name', 'created_at')
    list_filter = ('role', 'theme_mode', 'currency')
    search_fields = ('user__username', 'user__email', 'phone', 'business_name')


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'channel', 'destination', 'is_used', 'attempts', 'expires_at', 'created_at')
    list_filter = ('channel', 'is_used')
    search_fields = ('user__username', 'destination')


@admin.register(StaffPasswordRequest)
class StaffPasswordRequestAdmin(admin.ModelAdmin):
    list_display = ('staff_user', 'restaurant', 'admin_email', 'is_resolved', 'created_at')
    list_filter = ('is_resolved',)
    search_fields = ('staff_user__username', 'restaurant__name', 'admin_email')
