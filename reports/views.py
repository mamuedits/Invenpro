from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import csv
import json

from inventory.models import Product
from transactions.models import StockTransaction
from expenses.models import Expense
from .forms import ReportFilterForm
from accounts.utils import scope_queryset
from accounts.decorators import admin_required


def get_date_range_from_filter(request):
    preset = request.GET.get('preset', 'this_month')
    start_str = request.GET.get('start_date')
    end_str = request.GET.get('end_date')
    now = timezone.now()

    if preset == 'custom' and start_str and end_str:
        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
            return start_date, end_date, preset
        except ValueError:
            pass

    if preset == 'today':
        start_date = now.date()
        end_date = now.date()
    elif preset == 'last_7_days':
        start_date = (now - timedelta(days=7)).date()
        end_date = now.date()
    elif preset == 'last_30_days':
        start_date = (now - timedelta(days=30)).date()
        end_date = now.date()
    elif preset == 'last_month':
        first_of_this_month = now.date().replace(day=1)
        last_of_prev_month = first_of_this_month - timedelta(days=1)
        start_date = last_of_prev_month.replace(day=1)
        end_date = last_of_prev_month
    elif preset == 'this_year':
        start_date = now.date().replace(month=1, day=1)
        end_date = now.date()
    else:  # this_month
        start_date = now.date().replace(day=1)
        end_date = now.date()

    return start_date, end_date, preset


@admin_required
def report_overview_view(request):
    """
    Module 5 – Reports & Analytics Hub:
    Comprehensive analytics, date-range filtering, monthly stock-in/out,
    financial valuation, product usage, and dynamic currency conversion.
    """
    profile = getattr(request.user, 'profile', None)
    start_date, end_date, preset = get_date_range_from_filter(request)
    category_id = request.GET.get('category')
    product_id = request.GET.get('product')

    form = ReportFilterForm(initial={
        'preset': preset,
        'start_date': start_date,
        'end_date': end_date,
        'category': category_id,
        'product': product_id,
    })

    in_tx = scope_queryset(request, StockTransaction.objects.filter(
        transaction_type='IN',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ))
    out_tx = scope_queryset(request, StockTransaction.objects.filter(
        transaction_type='OUT',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ))
    expenses_qs = scope_queryset(request, Expense.objects.filter(
        expense_date__gte=start_date,
        expense_date__lte=end_date
    ))

    if category_id:
        in_tx = in_tx.filter(product__category_id=category_id)
        out_tx = out_tx.filter(product__category_id=category_id)
    if product_id:
        in_tx = in_tx.filter(product_id=product_id)
        out_tx = out_tx.filter(product_id=product_id)

    # Base Aggregates
    total_in_quantity = in_tx.aggregate(q=Sum('quantity'))['q'] or Decimal('0.00')
    total_in_amount_base = in_tx.aggregate(a=Sum('total_amount'))['a'] or Decimal('0.00')
    total_in_count = in_tx.count()

    total_out_quantity = out_tx.aggregate(q=Sum('quantity'))['q'] or Decimal('0.00')
    total_out_valuation_base = out_tx.aggregate(a=Sum('total_amount'))['a'] or Decimal('0.00')
    total_out_count = out_tx.count()

    total_operational_expenses_base = expenses_qs.aggregate(e=Sum('amount'))['e'] or Decimal('0.00')
    total_business_cash_outflow_base = total_in_amount_base + total_operational_expenses_base

    all_products = scope_queryset(request, Product.objects.all()).select_related('category')
    current_inventory_valuation_base = sum((p.stock_value for p in all_products), Decimal('0.00'))

    # Currency Conversion
    total_in_amount = profile.convert_from_base(total_in_amount_base) if profile else total_in_amount_base
    total_out_valuation = profile.convert_from_base(total_out_valuation_base) if profile else total_out_valuation_base
    total_operational_expenses = profile.convert_from_base(total_operational_expenses_base) if profile else total_operational_expenses_base
    total_business_cash_outflow = profile.convert_from_base(total_business_cash_outflow_base) if profile else total_business_cash_outflow_base
    current_inventory_valuation = profile.convert_from_base(current_inventory_valuation_base) if profile else current_inventory_valuation_base

    # Top consumed products (Stock-Out) in this period
    top_consumed = (
        out_tx.values('product__name', 'product__unit')
        .annotate(total_qty=Sum('quantity'), total_val=Sum('total_amount'))
        .order_by('-total_val')[:10]
    )

    # Product-wise usage matrix
    product_usage_report = []
    for prod in all_products:
        prod_in = in_tx.filter(product=prod).aggregate(q=Sum('quantity'), a=Sum('total_amount'))
        prod_out = out_tx.filter(product=prod).aggregate(q=Sum('quantity'), a=Sum('total_amount'))
        
        in_q = prod_in['q'] or Decimal('0.00')
        in_a_base = prod_in['a'] or Decimal('0.00')
        out_q = prod_out['q'] or Decimal('0.00')
        out_a_base = prod_out['a'] or Decimal('0.00')

        if in_q > 0 or out_q > 0 or prod.current_stock > 0:
            product_usage_report.append({
                'product': prod,
                'in_qty': in_q,
                'in_amount': in_a_base,
                'out_qty': out_q,
                'out_amount': out_a_base,
                'current_stock': prod.current_stock,
                'stock_value': prod.stock_value,
                'status': prod.stock_status,
                'badge_class': prod.status_badge_class,
            })

    # Top consumed chart data (converted to active currency)
    chart_top_labels = [item['product__name'] for item in top_consumed[:7]]
    chart_top_values = [
        float(profile.convert_from_base(item['total_val']) if profile else item['total_val'])
        for item in top_consumed[:7]
    ]

    # Expense categories breakdown (converted to active currency)
    expense_by_cat = (
        expenses_qs.values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    cat_display_map = dict(Expense.CATEGORY_CHOICES)
    exp_labels = [cat_display_map.get(e['category'], e['category']) for e in expense_by_cat]
    exp_values = [
        float(profile.convert_from_base(e['total']) if profile else e['total'])
        for e in expense_by_cat
    ]

    context = {
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'preset': preset,
        'total_in_quantity': total_in_quantity,
        'total_in_amount': total_in_amount,
        'total_in_count': total_in_count,
        'total_out_quantity': total_out_quantity,
        'total_out_valuation': total_out_valuation,
        'total_out_count': total_out_count,
        'total_operational_expenses': total_operational_expenses,
        'total_business_cash_outflow': total_business_cash_outflow,
        'current_inventory_valuation': current_inventory_valuation,
        'top_consumed': top_consumed,
        'product_usage_report': product_usage_report,
        'in_transactions': in_tx.select_related('product', 'supplier', 'user')[:20],
        'out_transactions': out_tx.select_related('product', 'user')[:20],
        # Charts
        'chart_top_labels_json': json.dumps(chart_top_labels),
        'chart_top_values_json': json.dumps(chart_top_values),
        'exp_labels_json': json.dumps(exp_labels),
        'exp_values_json': json.dumps(exp_values),
    }
    return render(request, 'reports/report_overview.html', context)


@admin_required
def export_stock_in_csv(request):
    profile = getattr(request.user, 'profile', None)
    sym = profile.currency_symbol if profile else '₹'
    start_date, end_date, _ = get_date_range_from_filter(request)
    in_tx = scope_queryset(request, StockTransaction.objects.filter(
        transaction_type='IN',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )).select_related('product', 'supplier', 'user').order_by('-created_at')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Invenpro_Purchases_{start_date}_to_{end_date}.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Date & Time', 'Product', 'Category', 'Quantity', 'Unit', f'Unit Price ({sym})', f'Total Amount ({sym})', 'Supplier', 'Recorded By', 'Notes'])

    for tx in in_tx:
        unit_p = profile.convert_from_base(tx.unit_price) if profile else tx.unit_price
        total_a = profile.convert_from_base(tx.total_amount) if profile else tx.total_amount
        writer.writerow([
            tx.id,
            tx.created_at.strftime('%Y-%m-%d %H:%M'),
            tx.product.name,
            tx.product.category.name if tx.product.category else 'N/A',
            tx.quantity,
            tx.product.unit,
            unit_p,
            total_a,
            tx.supplier.name if tx.supplier else 'None',
            tx.user.username,
            tx.notes,
        ])

    return response


@admin_required
def export_stock_out_csv(request):
    profile = getattr(request.user, 'profile', None)
    sym = profile.currency_symbol if profile else '₹'
    start_date, end_date, _ = get_date_range_from_filter(request)
    out_tx = scope_queryset(request, StockTransaction.objects.filter(
        transaction_type='OUT',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )).select_related('product', 'user').order_by('-created_at')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Invenpro_Usage_{start_date}_to_{end_date}.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Date & Time', 'Product', 'Category', 'Quantity Consumed', 'Unit', f'Valuation Unit Price ({sym})', f'Total Usage Value ({sym})', 'Recorded By', 'Notes'])

    for tx in out_tx:
        unit_p = profile.convert_from_base(tx.unit_price) if profile else tx.unit_price
        total_a = profile.convert_from_base(tx.total_amount) if profile else tx.total_amount
        writer.writerow([
            tx.id,
            tx.created_at.strftime('%Y-%m-%d %H:%M'),
            tx.product.name,
            tx.product.category.name if tx.product.category else 'N/A',
            tx.quantity,
            tx.product.unit,
            unit_p,
            total_a,
            tx.user.username,
            tx.notes,
        ])

    return response


@admin_required
def export_inventory_valuation_csv(request):
    profile = getattr(request.user, 'profile', None)
    sym = profile.currency_symbol if profile else '₹'
    products = scope_queryset(request, Product.objects.all()).select_related('category').order_by('name')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Invenpro_Inventory_Valuation_{timezone.now().date()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Product ID', 'Product Name', 'Category', 'Current Stock', 'Unit', f'Purchase Price ({sym})', f'Inventory Value ({sym})', 'Min Stock Threshold', 'Stock Status'])

    for p in products:
        unit_p = profile.convert_from_base(p.purchase_price) if profile else p.purchase_price
        val = profile.convert_from_base(p.stock_value) if profile else p.stock_value
        writer.writerow([
            p.id,
            p.name,
            p.category.name if p.category else 'N/A',
            p.current_stock,
            p.unit,
            unit_p,
            val,
            p.minimum_stock,
            p.stock_status,
        ])

    return response


@admin_required
def export_expenses_csv(request):
    profile = getattr(request.user, 'profile', None)
    sym = profile.currency_symbol if profile else '₹'
    start_date, end_date, _ = get_date_range_from_filter(request)
    expenses = scope_queryset(request, Expense.objects.filter(
        expense_date__gte=start_date,
        expense_date__lte=end_date
    )).select_related('created_by').order_by('-expense_date')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Invenpro_Expenses_{start_date}_to_{end_date}.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Date', 'Expense Title', 'Category', f'Amount ({sym})', 'Recorded By', 'Description'])

    for exp in expenses:
        amt = profile.convert_from_base(exp.amount) if profile else exp.amount
        writer.writerow([
            exp.id,
            exp.expense_date.strftime('%Y-%m-%d'),
            exp.title,
            exp.get_category_display(),
            amt,
            exp.created_by.username,
            exp.description,
        ])

    return response
