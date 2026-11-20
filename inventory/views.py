from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, F, Q, Count
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json

from .models import Product, Category, Supplier
from .forms import ProductForm, ProductUpdateForm, CategoryForm, SupplierForm
from transactions.models import StockTransaction
from expenses.models import Expense
from accounts.decorators import admin_required
from accounts.models import Restaurant
from accounts.utils import scope_queryset, get_user_restaurant


@login_required
def dashboard_view(request):
    """
    Module 1 – Interactive Modern Dashboard:
    Computes real-time inventory metrics, financial summaries, smart alert predictions,
    and chart data with dynamic multi-currency conversion.
    """
    profile = getattr(request.user, 'profile', None)
    now = timezone.now()
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Core Inventory Stats (Scoped to Restaurant)
    products = scope_queryset(request, Product.objects.all()).select_related('category')
    total_products = products.count()
    
    # Total inventory valuation in Base INR
    total_inventory_value_base = sum((p.stock_value for p in products), Decimal('0.00'))
    total_inventory_value = profile.convert_from_base(total_inventory_value_base) if profile else total_inventory_value_base

    # Stock Status counts
    out_of_stock_qs = products.filter(current_stock__lte=Decimal('0'))
    low_stock_qs = products.filter(current_stock__gt=Decimal('0'), current_stock__lte=F('minimum_stock'))
    healthy_stock_count = total_products - (out_of_stock_qs.count() + low_stock_qs.count())

    # Financial Summary for current month (converted to active currency)
    monthly_in_tx = scope_queryset(request, StockTransaction.objects.filter(
        transaction_type='IN',
        created_at__gte=first_day_of_month
    ))
    monthly_purchases_base = monthly_in_tx.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    monthly_purchases = profile.convert_from_base(monthly_purchases_base) if profile else monthly_purchases_base

    monthly_out_tx = scope_queryset(request, StockTransaction.objects.filter(
        transaction_type='OUT',
        created_at__gte=first_day_of_month
    ))
    monthly_usage_value_base = monthly_out_tx.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    monthly_usage_value = profile.convert_from_base(monthly_usage_value_base) if profile else monthly_usage_value_base

    monthly_expenses_qs = scope_queryset(request, Expense.objects.filter(expense_date__gte=first_day_of_month.date()))
    monthly_expenses_amount_base = monthly_expenses_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    monthly_expenses_amount = profile.convert_from_base(monthly_expenses_amount_base) if profile else monthly_expenses_amount_base

    total_monthly_spend = monthly_purchases + monthly_expenses_amount

    # Recent stock transactions
    recent_transactions = scope_queryset(request, StockTransaction.objects.all()).select_related('product', 'user', 'supplier')[:8]

    # Smart Stock Alert and Consumption Analysis
    smart_alerts = []
    for prod in products:
        analysis = prod.get_consumption_analysis(days=7)
        if prod.stock_status != 'Healthy' or (analysis['days_left'] is not None and analysis['days_left'] <= 5.0):
            smart_alerts.append({
                'product': prod,
                'current_stock': prod.current_stock,
                'minimum_stock': prod.minimum_stock,
                'status': prod.stock_status,
                'unit': prod.unit,
                'avg_daily': analysis['avg_daily'],
                'days_left': analysis['days_left'],
                'urgency': analysis['urgency'],
                'urgency_label': analysis['urgency_label'],
            })
    smart_alerts.sort(key=lambda x: (x['days_left'] is not None, x['days_left'] if x['days_left'] is not None else -1))
    smart_alerts_preview = smart_alerts[:6]

    # Trend Chart Data: Past 7 days daily movement in active currency
    dates_labels = []
    in_data = []
    out_data = []
    for i in range(6, -1, -1):
        target_day = (now - timedelta(days=i)).date()
        dates_labels.append(target_day.strftime('%b %d'))
        
        day_in = scope_queryset(request, StockTransaction.objects.filter(
            transaction_type='IN',
            created_at__date=target_day
        )).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        day_out = scope_queryset(request, StockTransaction.objects.filter(
            transaction_type='OUT',
            created_at__date=target_day
        )).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

        in_conv = profile.convert_from_base(day_in) if profile else day_in
        out_conv = profile.convert_from_base(day_out) if profile else day_out
        in_data.append(float(in_conv))
        out_data.append(float(out_conv))

    # Category Breakdown for doughnut chart in active currency
    categories_data = []
    cat_qs = scope_queryset(request, Category.objects.all()).annotate(prod_count=Count('products')).filter(prod_count__gt=0)
    for c in cat_qs:
        cat_val_base = sum((p.stock_value for p in c.products.all()), Decimal('0.00'))
        cat_val = profile.convert_from_base(cat_val_base) if profile else cat_val_base
        categories_data.append({
            'name': c.name,
            'val': float(cat_val),
            'count': c.prod_count
        })

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_stock_outs_count = scope_queryset(request, StockTransaction.objects.filter(
        transaction_type='OUT',
        created_at__gte=today_start
    )).count()
    today_stock_ins_count = scope_queryset(request, StockTransaction.objects.filter(
        transaction_type='IN',
        created_at__gte=today_start
    )).count()
    is_admin_or_dev = (profile.is_admin if profile else False) or request.user.is_superuser

    context = {
        'total_products': total_products,
        'total_inventory_value': total_inventory_value,
        'out_of_stock_count': out_of_stock_qs.count(),
        'low_stock_count': low_stock_qs.count(),
        'healthy_stock_count': healthy_stock_count,
        'today_stock_outs_count': today_stock_outs_count,
        'today_stock_ins_count': today_stock_ins_count,
        'is_admin_or_dev': is_admin_or_dev,
        'monthly_purchases': monthly_purchases,
        'monthly_usage_value': monthly_usage_value,
        'monthly_expenses_amount': monthly_expenses_amount,
        'total_monthly_spend': total_monthly_spend,
        'recent_transactions': recent_transactions,
        'smart_alerts_preview': smart_alerts_preview,
        'total_alerts_count': len(smart_alerts),
        # Chart JSON
        'chart_labels_json': json.dumps(dates_labels),
        'chart_in_json': json.dumps(in_data),
        'chart_out_json': json.dumps(out_data),
        'category_labels_json': json.dumps([c['name'] for c in categories_data]),
        'category_values_json': json.dumps([c['val'] for c in categories_data]),
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def product_list_view(request):
    """
    Module 2 – Product Management: List, Search, Filter & Converted Pricing.
    """
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')

    products = scope_queryset(request, Product.objects.all()).select_related('category')

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(category__name__icontains=query)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if status_filter == 'out':
        products = products.filter(current_stock__lte=Decimal('0'))
    elif status_filter == 'low':
        products = products.filter(current_stock__gt=Decimal('0'), current_stock__lte=F('minimum_stock'))
    elif status_filter == 'healthy':
        products = products.filter(current_stock__gt=F('minimum_stock'))

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = scope_queryset(request, Category.objects.all())

    context = {
        'products': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'status_filter': status_filter,
        'total_count': products.count(),
    }
    return render(request, 'inventory/product_list.html', context)


@admin_required
def product_create_view(request):
    """
    Module 2 – Add New Product.
    Scoped to user's restaurant. Converts entered purchase price from active currency to Base INR.
    """
    profile = getattr(request.user, 'profile', None)
    restaurant = get_user_restaurant(request)
    if not restaurant and profile and profile.is_developer:
        restaurant = Restaurant.objects.first()

    if request.method == 'POST':
        form = ProductForm(request.POST, restaurant=restaurant)
        if form.is_valid():
            product = form.save(commit=False)
            product.restaurant = restaurant
            initial_stock = form.cleaned_data.get('initial_stock') or Decimal('0.00')
            
            # Convert user entered price into base currency (INR)
            raw_price = form.cleaned_data.get('purchase_price') or Decimal('0.00')
            product.purchase_price = profile.convert_to_base(raw_price) if profile else raw_price
            product.current_stock = Decimal('0.00')
            product.save()

            if initial_stock > Decimal('0.00'):
                StockTransaction.record_stock_in(
                    product=product,
                    quantity=initial_stock,
                    unit_price=product.purchase_price,
                    user=request.user,
                    notes="Initial opening inventory stock entry"
                )

            messages.success(request, f"Product '{product.name}' created successfully for {restaurant.name if restaurant else 'catalog'}!")
            return redirect('product_list')
    else:
        form = ProductForm(restaurant=restaurant)

    return render(request, 'inventory/product_form.html', {
        'form': form,
        'title': 'Add New Product',
        'is_new': True,
    })


@admin_required
def product_update_view(request, pk):
    """
    Module 2 – Edit Product Information (Scoped to restaurant).
    """
    profile = getattr(request.user, 'profile', None)
    restaurant = get_user_restaurant(request)
    if not restaurant and profile and profile.is_developer:
        restaurant = Restaurant.objects.first()
    product = get_object_or_404(scope_queryset(request, Product.objects.all()), pk=pk)

    if request.method == 'POST':
        form = ProductUpdateForm(request.POST, instance=product, restaurant=restaurant)
        if form.is_valid():
            p = form.save(commit=False)
            raw_price = form.cleaned_data.get('purchase_price') or Decimal('0.00')
            p.purchase_price = profile.convert_to_base(raw_price) if profile else raw_price
            p.save()
            messages.success(request, f"Product '{product.name}' updated successfully.")
            return redirect('product_detail', pk=product.pk)
    else:
        # Pre-fill purchase_price in active currency
        converted_price = profile.convert_from_base(product.purchase_price) if profile else product.purchase_price
        form = ProductUpdateForm(instance=product, restaurant=restaurant, initial={'purchase_price': converted_price})

    return render(request, 'inventory/product_form.html', {
        'form': form,
        'product': product,
        'title': f"Edit Product: {product.name}",
        'is_new': False,
    })


@admin_required
def product_delete_view(request, pk):
    product = get_object_or_404(scope_queryset(request, Product.objects.all()), pk=pk)
    if request.method == 'POST':
        name = product.name
        try:
            product.delete()
            messages.success(request, f"Product '{name}' deleted successfully.")
        except Exception:
            messages.error(request, f"Cannot delete product '{name}': It has linked historical records.")
        return redirect('product_list')

    return render(request, 'inventory/product_confirm_delete.html', {'product': product})


@login_required
def product_detail_view(request, pk):
    product = get_object_or_404(scope_queryset(request, Product.objects.all()).select_related('category'), pk=pk)
    transactions = product.transactions.all().select_related('user', 'supplier')[:20]
    analysis_7 = product.get_consumption_analysis(days=7)
    analysis_30 = product.get_consumption_analysis(days=30)

    context = {
        'product': product,
        'transactions': transactions,
        'analysis_7': analysis_7,
        'analysis_30': analysis_30,
    }
    return render(request, 'inventory/product_detail.html', context)


@login_required
def smart_alerts_view(request):
    products = scope_queryset(request, Product.objects.all()).select_related('category')
    analysis_list = []

    for p in products:
        stat_7 = p.get_consumption_analysis(days=7)
        stat_30 = p.get_consumption_analysis(days=30)
        days_left = stat_7.get('days_left')
        is_depleted = p.current_stock <= Decimal('0.00')
        is_low = p.current_stock <= p.minimum_stock

        if is_depleted or (days_left is not None and days_left <= 2):
            reorder_urgency = 'CRITICAL'
        elif is_low or (days_left is not None and days_left <= 5):
            reorder_urgency = 'SOON'
        else:
            reorder_urgency = 'ADEQUATE'

        analysis_list.append({
            'product': p,
            'current_stock': p.current_stock,
            'minimum_stock': p.minimum_stock,
            'unit': p.unit,
            'status': p.stock_status,
            'badge_class': p.status_badge_class,
            'stat_7': stat_7,
            'stat_30': stat_30,
            'urgency': stat_7['urgency'],
            'urgency_label': stat_7['urgency_label'],
            'days_left': days_left,
            'runway_days': days_left,
            'consumed_7d': stat_7.get('total_consumed', Decimal('0.00')),
            'daily_consumption': stat_7.get('avg_daily', Decimal('0.00')),
            'reorder_urgency': reorder_urgency,
            'is_low_stock': is_low,
            'is_out_of_stock': is_depleted,
        })

    # Sort order: Low stock and Out of Stock items strictly at the TOP
    def get_alert_priority(item):
        stock = item['current_stock']
        min_stock = item['minimum_stock']
        days = item['days_left'] if item['days_left'] is not None else 9999

        if stock <= Decimal('0.00'):
            # Out of stock / Finished (Top Priority)
            return (0, 0.0, days)
        elif stock <= min_stock:
            # Low Stock below minimum threshold (Second Priority, sorted by ratio ascending)
            ratio = float(stock / (min_stock if min_stock > Decimal('0.00') else Decimal('1.00')))
            return (1, ratio, days)
        elif days <= 5:
            # Warning runway
            return (2, days, float(stock))
        else:
            # Healthy buffer
            return (3, days, float(stock))

    analysis_list.sort(key=get_alert_priority)

    context = {
        'analysis_list': analysis_list,
        'critical_count': sum(1 for a in analysis_list if a['reorder_urgency'] == 'CRITICAL'),
        'warning_count': sum(1 for a in analysis_list if a['reorder_urgency'] == 'SOON'),
        'healthy_count': sum(1 for a in analysis_list if a['reorder_urgency'] == 'ADEQUATE'),
    }
    return render(request, 'inventory/smart_alerts.html', context)


# --- Category & Supplier Views ---

@login_required
def category_list_view(request):
    categories = scope_queryset(request, Category.objects.all()).annotate(
        prod_count=Count('products')
    ).order_by('name')
    return render(request, 'inventory/category_list.html', {'categories': categories})


@admin_required
def category_create_view(request):
    restaurant = get_user_restaurant(request)
    if not restaurant and getattr(request.user, 'profile', None) and request.user.profile.is_developer:
        restaurant = Restaurant.objects.first()
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.restaurant = restaurant
            category.save()
            messages.success(request, f"Category '{category.name}' created.")
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'inventory/category_form.html', {'form': form, 'title': 'Add Category'})


@admin_required
def category_update_view(request, pk):
    category = get_object_or_404(scope_queryset(request, Category.objects.all()), pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f"Category '{category.name}' updated.")
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'inventory/category_form.html', {'form': form, 'title': 'Edit Category'})


@admin_required
def category_delete_view(request, pk):
    category = get_object_or_404(scope_queryset(request, Category.objects.all()), pk=pk)
    if request.method == 'POST':
        if category.products.exists():
            messages.error(request, f"Cannot delete '{category.name}': Products are still assigned to it.")
            return redirect('category_list')
        category.delete()
        messages.success(request, "Category deleted successfully.")
        return redirect('category_list')
    return render(request, 'inventory/category_confirm_delete.html', {'category': category})


@login_required
def supplier_list_view(request):
    suppliers = scope_queryset(request, Supplier.objects.all()).annotate(tx_count=Count('transactions')).order_by('name')
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})


@admin_required
def supplier_create_view(request):
    restaurant = get_user_restaurant(request)
    if not restaurant and getattr(request.user, 'profile', None) and request.user.profile.is_developer:
        restaurant = Restaurant.objects.first()
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False)
            s.restaurant = restaurant
            s.save()
            messages.success(request, f"Supplier '{s.name}' added.")
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'inventory/supplier_form.html', {'form': form, 'title': 'Add Supplier'})


@admin_required
def supplier_update_view(request, pk):
    s = get_object_or_404(scope_queryset(request, Supplier.objects.all()), pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=s)
        if form.is_valid():
            form.save()
            messages.success(request, f"Supplier '{s.name}' updated.")
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=s)
    return render(request, 'inventory/supplier_form.html', {'form': form, 'title': 'Edit Supplier'})


@admin_required
def supplier_delete_view(request, pk):
    s = get_object_or_404(scope_queryset(request, Supplier.objects.all()), pk=pk)
    if request.method == 'POST':
        s.delete()
        messages.success(request, "Supplier deleted.")
        return redirect('supplier_list')
    return render(request, 'inventory/supplier_confirm_delete.html', {'supplier': s})
