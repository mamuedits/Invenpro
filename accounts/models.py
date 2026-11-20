from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal


class Restaurant(models.Model):
    """
    Multi-tenant core: Each restaurant has its own allotted unique Restaurant ID,
    isolated inventory catalog, transactions, operating expenses, and staff accounts.
    """
    restaurant_id = models.CharField(max_length=20, unique=True, editable=False)
    name = models.CharField(max_length=150, verbose_name="Restaurant Name")
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_restaurants')
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True, verbose_name="Restaurant Address")
    gst_number = models.CharField(max_length=50, blank=True, verbose_name="GSTIN / Tax ID")
    currency = models.CharField(max_length=10, default='INR')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.restaurant_id})"

    def save(self, *args, **kwargs):
        if not self.restaurant_id:
            import random
            while True:
                candidate = f"RES-{random.randint(10000, 99999)}"
                if not Restaurant.objects.filter(restaurant_id=candidate).exists():
                    self.restaurant_id = candidate
                    break
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('developer', '💻 Developer / Super Admin'),
        ('admin', '👑 Restaurant Admin / Owner'),
        ('staff', '👨‍🍳 Staff / Inventory Operator'),
    ]

    CURRENCY_CHOICES = [
        ('INR', '₹ INR (Indian Rupee)'),
        ('USD', '$ USD (US Dollar)'),
        ('EUR', '€ EUR (Euro)'),
        ('GBP', '£ GBP (British Pound)'),
        ('AED', 'د.إ AED (UAE Dirham)'),
    ]

    THEME_CHOICES = [
        ('light', '☀️ Light Mode'),
        ('dark', '🌙 Dark Mode'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True, related_name='members')
    phone = models.CharField(max_length=20, blank=True)
    business_name = models.CharField(max_length=150, default='Invenpro Store', blank=True)
    display_password = models.CharField(max_length=128, blank=True, default='', verbose_name="Visible Password Reference")
    
    # Regional & Appearance Settings
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='INR')
    theme_mode = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    
    # Custom / Configurable Exchange Rates (Relative to Base INR)
    # e.g. 1 USD = 84.00 INR, 1 EUR = 91.00 INR
    usd_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('84.00'),
        verbose_name="1 USD in INR"
    )
    eur_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('91.00'),
        verbose_name="1 EUR in INR"
    )
    gbp_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('107.00'),
        verbose_name="1 GBP in INR"
    )
    aed_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('23.00'),
        verbose_name="1 AED in INR"
    )

    # Business Tax & Address Details
    gst_number = models.CharField(max_length=50, blank=True, verbose_name="GST / Tax Identification Number")
    store_address = models.TextField(blank=True, verbose_name="Store / Business Address")
    
    # Inventory Alert Preference
    default_min_stock = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('5.00'),
        verbose_name="Default Minimum Stock Alert"
    )
    enable_stock_alerts = models.BooleanField(default=True, verbose_name="Show Stock Alert Badges & Banners")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_developer(self):
        return self.role == 'developer' or self.user.is_superuser

    @property
    def is_restaurant_admin(self):
        return self.role in ['admin', 'developer'] or self.user.is_superuser

    @property
    def is_admin(self):
        return self.is_restaurant_admin

    @property
    def is_staff_member(self):
        return self.role == 'staff' and not self.is_admin

    @property
    def currency_symbol(self):
        symbol_map = {
            'INR': '₹',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'AED': 'د.إ',
        }
        return symbol_map.get(self.currency, '₹')

    def get_exchange_rate(self):
        """
        Returns how many Base INR equal 1 unit of currently active currency.
        """
        if self.currency == 'USD':
            return self.usd_rate or Decimal('84.00')
        elif self.currency == 'EUR':
            return self.eur_rate or Decimal('91.00')
        elif self.currency == 'GBP':
            return self.gbp_rate or Decimal('107.00')
        elif self.currency == 'AED':
            return self.aed_rate or Decimal('23.00')
        return Decimal('1.00')  # INR base

    def convert_from_base(self, amount_in_inr):
        """
        Converts an amount stored in Base INR to the active user currency.
        Example: 84 INR / 84.00 = 1.00 USD
        """
        if amount_in_inr is None:
            return Decimal('0.00')
        rate = self.get_exchange_rate()
        return round(Decimal(str(amount_in_inr)) / rate, 2)

    def convert_to_base(self, amount_in_selected_currency):
        """
        Converts user entered amount in active currency back to Base INR for storage.
        Example: 1.00 USD * 84.00 = 84.00 INR
        """
        if amount_in_selected_currency is None:
            return Decimal('0.00')
        rate = self.get_exchange_rate()
        return round(Decimal(str(amount_in_selected_currency)) * rate, 2)

    def format_money(self, amount_in_inr):
        """
        Formats amount with active currency symbol and converted numerical value.
        """
        val = self.convert_from_base(amount_in_inr)
        return f"{self.currency_symbol}{val:,.2f}"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        role = 'developer' if instance.is_superuser else 'staff'
        UserProfile.objects.get_or_create(user=instance, defaults={'role': role, 'currency': 'INR', 'theme_mode': 'light'})
    else:
        if not hasattr(instance, 'profile'):
            role = 'developer' if instance.is_superuser else 'staff'
            UserProfile.objects.get_or_create(user=instance, defaults={'role': role, 'currency': 'INR', 'theme_mode': 'light'})


def cleanup_orphaned_restaurants():
    """
    Auto-deletion guarantee:
    Any restaurant that has 0 registered admin accounts is permanently removed along
    with its isolated data (inventory, suppliers, categories, transactions, expenses).
    """
    try:
        for rest in list(Restaurant.objects.all()):
            admin_count = UserProfile.objects.filter(restaurant=rest, role='admin').count()
            if admin_count == 0:
                staff_users = list(
                    User.objects.filter(profile__restaurant=rest)
                    .exclude(is_superuser=True)
                    .exclude(profile__role='developer')
                    .values_list('id', flat=True)
                )
                rest.delete()
                if staff_users:
                    User.objects.filter(id__in=staff_users).delete()
    except Exception:
        pass


@receiver(pre_delete, sender=User)
def auto_delete_restaurant_on_user_delete(sender, instance, **kwargs):
    """
    Triggered when a user is deleted (e.g. via Django admin, ORM, or developer portal).
    If the user being deleted is an admin, and no other admin remains for that restaurant:
    The restaurant and all its isolated tenant data are permanently deleted immediately.
    """
    try:
        profile = getattr(instance, 'profile', None)
        if profile and profile.restaurant and profile.role == 'admin':
            rest = profile.restaurant
            # Check if any OTHER active admin exists for this restaurant
            other_admins_exist = UserProfile.objects.filter(
                restaurant=rest,
                role='admin'
            ).exclude(user=instance).exists()

            if not other_admins_exist:
                # This was the last admin. Remove all non-developer staff users and delete restaurant.
                staff_user_ids = list(
                    User.objects.filter(profile__restaurant=rest)
                    .exclude(pk=instance.pk)
                    .exclude(is_superuser=True)
                    .exclude(profile__role='developer')
                    .values_list('id', flat=True)
                )
                rest.delete()
                if staff_user_ids:
                    User.objects.filter(id__in=staff_user_ids).delete()
    except Exception:
        pass


@receiver(post_delete, sender=UserProfile)
def auto_delete_restaurant_on_userprofile_delete(sender, instance, **kwargs):
    """
    Secondary safety net if a UserProfile is deleted directly.
    """
    try:
        if instance.restaurant_id and instance.role == 'admin':
            rest = Restaurant.objects.filter(pk=instance.restaurant_id).first()
            if rest:
                remaining_admins = UserProfile.objects.filter(
                    restaurant=rest,
                    role='admin'
                ).exclude(pk=instance.pk).count()

                if remaining_admins == 0:
                    staff_user_ids = list(
                        User.objects.filter(profile__restaurant=rest)
                        .exclude(pk=instance.user_id)
                        .exclude(is_superuser=True)
                        .exclude(profile__role='developer')
                        .values_list('id', flat=True)
                    )
                    rest.delete()
                    if staff_user_ids:
                        User.objects.filter(id__in=staff_user_ids).delete()
    except Exception:
        pass


class PasswordResetOTP(models.Model):
    """
    One-Time Password (OTP) tokens for Admin and Developer password recovery via Email.
    """
    CHANNEL_CHOICES = [
        ('email', 'Email OTP'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_otps')
    otp_code = models.CharField(max_length=6)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='email')
    destination = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Email OTP for {self.user.username}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return (not self.is_used) and (not self.is_expired) and (self.attempts < 5)


class StaffPasswordRequest(models.Model):
    """
    Tracks staff forgot-password requests sent to their Restaurant Admin's email
    so the Admin can reset and share the staff member's password.
    """
    staff_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_requests')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='staff_password_requests')
    admin_email = models.EmailField(blank=True)
    staff_note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Staff Password Request: {self.staff_user.username} ({self.restaurant.name})"


