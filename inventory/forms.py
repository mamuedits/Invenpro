from django import forms
from decimal import Decimal
from .models import Product, Category, Supplier


class ProductForm(forms.ModelForm):
    initial_stock = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        initial=Decimal('0.00'),
        help_text="Optional starting inventory quantity for newly added products",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
    )

    class Meta:
        model = Product
        fields = ['name', 'category', 'unit', 'purchase_price', 'minimum_stock']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Fresh Chicken Breast, Basmati Rice'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        restaurant = kwargs.pop('restaurant', None)
        super().__init__(*args, **kwargs)
        if restaurant:
            self.fields['category'].queryset = Category.objects.filter(restaurant=restaurant).order_by('name')


class ProductUpdateForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'unit', 'purchase_price', 'minimum_stock']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        restaurant = kwargs.pop('restaurant', None)
        super().__init__(*args, **kwargs)
        if restaurant:
            self.fields['category'].queryset = Category.objects.filter(restaurant=restaurant).order_by('name')


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Meat & Poultry, Grains, Dairy, Beverages'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief category description...'}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supplier or Vendor Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 555 123 4567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'orders@supplier.com'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Warehouse/City address'}),
        }

