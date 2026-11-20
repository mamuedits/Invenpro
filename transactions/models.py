from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from inventory.models import Product, Supplier


class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('IN', 'Stock-In (Purchase)'),
        ('OUT', 'Stock-Out (Usage / Consumption)'),
        ('ADJUSTMENT', 'Stock Adjustment (Audit / Correction)'),
    ]

    restaurant = models.ForeignKey('accounts.Restaurant', on_delete=models.CASCADE, null=True, blank=True, related_name='transactions')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transactions')
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='transactions',
        help_text="Supplier for purchase/stock-in"
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True, help_text="Notes, invoice number, or reason for stock movement")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.product.name} ({self.quantity} {self.product.unit})"

    def clean(self):
        if self.quantity is not None and self.quantity <= Decimal('0'):
            raise ValidationError({'quantity': "Quantity must be greater than zero."})

    def save(self, *args, **kwargs):
        # Auto-calculate total amount
        if self.quantity and self.unit_price is not None:
            self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    @classmethod
    @transaction.atomic
    def record_stock_in(cls, product, quantity, unit_price, user, supplier=None, notes=""):
        """
        Atomically records a Stock-In transaction and updates product stock and price.
        Formula: New Stock = Current Stock + Quantity
        """
        if quantity <= Decimal('0'):
            raise ValidationError("Quantity must be greater than zero.")
        
        # Lock product row for update
        prod = Product.objects.select_for_update().get(pk=product.pk)
        prod.current_stock += quantity
        if unit_price > Decimal('0'):
            prod.purchase_price = unit_price
        prod.save()

        tx = cls.objects.create(
            restaurant=prod.restaurant,
            product=prod,
            supplier=supplier,
            user=user,
            transaction_type='IN',
            quantity=quantity,
            unit_price=unit_price,
            total_amount=quantity * unit_price,
            notes=notes
        )
        return tx

    @classmethod
    @transaction.atomic
    def record_stock_out(cls, product, quantity, user, notes="", unit_price=None):
        """
        Atomically records a Stock-Out transaction and updates product stock.
        Validation: Prevents stock from dropping below zero.
        Formula: New Stock = Current Stock - Quantity
        """
        if quantity <= Decimal('0'):
            raise ValidationError("Quantity must be greater than zero.")
        
        prod = Product.objects.select_for_update().get(pk=product.pk)
        if quantity > prod.current_stock:
            raise ValidationError(
                f"Insufficient stock! Requested: {quantity} {prod.unit}, but only {prod.current_stock} {prod.unit} available."
            )

        prod.current_stock -= quantity
        prod.save()

        # If unit_price not specified, evaluate using current product purchase price
        price = unit_price if unit_price is not None else prod.purchase_price

        tx = cls.objects.create(
            restaurant=prod.restaurant,
            product=prod,
            supplier=None,
            user=user,
            transaction_type='OUT',
            quantity=quantity,
            unit_price=price,
            total_amount=quantity * price,
            notes=notes
        )
        return tx

    @classmethod
    @transaction.atomic
    def record_adjustment(cls, product, target_quantity, user, notes=""):
        """
        Atomically adjusts product stock to target_quantity based on physical audit.
        """
        prod = Product.objects.select_for_update().get(pk=product.pk)
        old_stock = prod.current_stock
        delta = target_quantity - old_stock
        
        prod.current_stock = target_quantity
        prod.save()

        tx = cls.objects.create(
            restaurant=prod.restaurant,
            product=prod,
            user=user,
            transaction_type='ADJUSTMENT',
            quantity=abs(delta),
            unit_price=prod.purchase_price,
            total_amount=abs(delta) * prod.purchase_price,
            notes=f"Audit Adjustment from {old_stock} to {target_quantity} {prod.unit}. Note: {notes}"
        )
        return tx
