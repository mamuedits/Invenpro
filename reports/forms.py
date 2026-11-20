from django import forms
from inventory.models import Category, Product


class ReportFilterForm(forms.Form):
    PRESET_CHOICES = [
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('last_7_days', 'Last 7 Days'),
        ('last_30_days', 'Last 30 Days'),
        ('this_year', 'This Year'),
        ('custom', 'Custom Date Range'),
    ]

    preset = forms.ChoiceField(
        choices=PRESET_CHOICES,
        required=False,
        initial='this_month',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'preset_selector'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all().order_by('name'),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.all().order_by('name'),
        required=False,
        empty_label="All Products",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

