from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('utilities', '⚡ Utilities (Electricity, Gas, Water)'),
        ('rent', '🏢 Rent & Facility Lease'),
        ('salaries', '👥 Salaries & Staff Wages'),
        ('maintenance', '🔧 Equipment & Maintenance'),
        ('marketing', '📢 Marketing & Advertising'),
        ('supplies', '📦 Packaging & Operating Supplies'),
        ('licensing', '📜 Licenses, Permits & Software'),
        ('miscellaneous', '🏷️ Miscellaneous'),
    ]

    restaurant = models.ForeignKey('accounts.Restaurant', on_delete=models.CASCADE, null=True, blank=True, related_name='expenses')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='miscellaneous')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    description = models.TextField(blank=True)
    expense_date = models.DateField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        return f"{self.title} - ${self.amount} ({self.get_category_display()})"
