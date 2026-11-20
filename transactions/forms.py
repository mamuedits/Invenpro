from django import forms
from decimal import Decimal
from inventory.models import Product, Supplier


class StockInForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select select2-enable', 'id': 'id_product_in'})
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all().order_by('name'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Quantity purchased'})
    )
    unit_price = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        required=False,
        min_value=Decimal('0.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Price per unit'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'PO #, Delivery Challan or supplier note...'})
    )

    def __init__(self, *args, **kwargs):
        restaurant = kwargs.pop('restaurant', None)
        super().__init__(*args, **kwargs)
        if restaurant:
            self.fields['product'].queryset = Product.objects.filter(restaurant=restaurant).order_by('name')
            self.fields['supplier'].queryset = Supplier.objects.filter(restaurant=restaurant).order_by('name')


class StockOutForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select select2-enable', 'id': 'id_product_out'})
    )
    quantity = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Quantity consumed/sold'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'e.g. Daily kitchen consumption, Table order, Event catering...'})
    )

    def __init__(self, *args, **kwargs):
        restaurant = kwargs.pop('restaurant', None)
        super().__init__(*args, **kwargs)
        if restaurant:
            self.fields['product'].queryset = Product.objects.filter(restaurant=restaurant).order_by('name')


class StockAdjustmentForm(forms.Form):
    ADJUSTMENT_REASON_CHOICES = [
        ('Physical Count Correction', '📋 Physical Stock Count Discrepancy'),
        ('Kitchen Spillage / Waste', '🍳 Kitchen Spillage / Waste'),
        ('Spoilage / Expired', '🥬 Spoilage / Expired Ingredients'),
        ('Breakage / Damage', '💥 Container Breakage / Damage'),
        ('Theft / Missing Stock', '🔒 Theft / Missing Stock'),
        ('Initial Audit Correction', '📊 Initial Audit / Opening Rebalance'),
        ('Other Discrepancy', '📝 Other Discrepancy (Specify in Notes)'),
    ]

    product = forms.ModelChoiceField(
        queryset=Product.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_product_adj'})
    )
    target_quantity = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Actual counted physical stock'})
    )
    reason = forms.ChoiceField(
        choices=ADJUSTMENT_REASON_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_adj_reason'})
    )
    notes = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Mandatory audit reason / discrepancy explanation...'})
    )

    def __init__(self, *args, **kwargs):
        restaurant = kwargs.pop('restaurant', None)
        super().__init__(*args, **kwargs)
        if restaurant:
            self.fields['product'].queryset = Product.objects.filter(restaurant=restaurant).order_by('name')

