from django.db import models
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class Category(models.Model):
    restaurant = models.ForeignKey('accounts.Restaurant', on_delete=models.CASCADE, null=True, blank=True, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        unique_together = ('restaurant', 'name')

    def __str__(self):
        return self.name

    @property
    def product_count(self):
        return self.products.count()


class Supplier(models.Model):
    restaurant = models.ForeignKey('accounts.Restaurant', on_delete=models.CASCADE, null=True, blank=True, related_name='suppliers')
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram (kg)'),
        ('litre', 'Litre (L)'),
        ('pcs', 'Pieces (pcs)'),
        ('gm', 'Gram (g)'),
        ('box', 'Box'),
        ('pkt', 'Packet (pkt)'),
        ('can', 'Can'),
        ('bottle', 'Bottle'),
    ]

    restaurant = models.ForeignKey('accounts.Restaurant', on_delete=models.CASCADE, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='kg')
    purchase_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Default purchase price per unit in $"
    )
    current_stock = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Real-time stock quantity available"
    )
    minimum_stock = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('5.00'),
        help_text="Threshold below which Low-Stock alert is triggered"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit})"

    @property
    def stock_value(self):
        """Current financial valuation of stock on hand."""
        return self.current_stock * self.purchase_price

    @property
    def stock_status(self):
        """Smart status indicator."""
        if self.current_stock <= Decimal('0'):
            return 'Out of Stock'
        elif self.current_stock <= self.minimum_stock:
            return 'Low Stock'
        return 'Healthy'

    @property
    def status_badge_class(self):
        status = self.stock_status
        if status == 'Out of Stock':
            return 'bg-danger'
        elif status == 'Low Stock':
            return 'bg-warning text-dark'
        return 'bg-success'

    def get_consumption_analysis(self, days=7):
        """
        Smart Stock Alert & Consumption Analysis System:
        Calculates recent consumption, average daily burn rate, and days until depletion.
        """
        from transactions.models import StockTransaction
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Total consumption in window
        out_transactions = StockTransaction.objects.filter(
            product=self,
            transaction_type='OUT',
            created_at__gte=cutoff_date
        )
        total_consumed = sum((tx.quantity for tx in out_transactions), Decimal('0.00'))
        
        avg_daily = total_consumed / Decimal(str(days))
        
        if avg_daily > Decimal('0.00'):
            days_left = float(self.current_stock / avg_daily)
            days_left_rounded = round(days_left, 1)
        else:
            days_left = None
            days_left_rounded = None

        # Determine urgency
        if self.current_stock <= Decimal('0'):
            urgency = 'critical'
            urgency_label = 'Depleted (Order Immediately)'
        elif days_left is not None and days_left <= 2.0:
            urgency = 'critical'
            urgency_label = f'Critical (~{days_left_rounded} days left)'
        elif self.current_stock <= self.minimum_stock or (days_left is not None and days_left <= 5.0):
            urgency = 'warning'
            urgency_label = f'Warning (~{days_left_rounded} days left)' if days_left else 'Low Stock'
        else:
            urgency = 'healthy'
            urgency_label = 'Healthy'

        return {
            'days_window': days,
            'total_consumed': total_consumed,
            'avg_daily': round(avg_daily, 2),
            'days_left': days_left_rounded,
            'urgency': urgency,
            'urgency_label': urgency_label
        }
