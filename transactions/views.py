from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db.models import Q
from decimal import Decimal

from .models import StockTransaction
from .forms import StockInForm, StockOutForm, StockAdjustmentForm
from inventory.models import Product
from accounts.decorators import admin_required
from accounts.utils import scope_queryset, get_user_restaurant


@login_required
def transaction_list_view(request):
    """
    Module 3 – Stock Movement Audit History.
    Full ledger of Stock-In, Stock-Out and Adjustments with filters.
    """
    tx_type = request.GET.get('type', '')
    product_id = request.GET.get('product', '')
    search = request.GET.get('q', '').strip()

    transactions = scope_queryset(request, StockTransaction.objects.all()).select_related('product', 'supplier', 'user')

    if tx_type:
        transactions = transactions.filter(transaction_type=tx_type)
    if product_id:
        transactions = transactions.filter(product_id=product_id)
    if search:
        transactions = transactions.filter(
            Q(product__name__icontains=search) |
            Q(notes__icontains=search) |
            Q(user__username__icontains=search)
        )

    paginator = Paginator(transactions, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    products = scope_queryset(request, Product.objects.all()).order_by('name')

    context = {
        'transactions': page_obj,
        'products': products,
        'selected_type': tx_type,
        'selected_product': product_id,
        'search': search,
    }
    return render(request, 'transactions/transaction_list.html', context)


@login_required
def stock_in_view(request):
    """
    Module 3 – Stock-In (Purchases):
    Adds incoming inventory, updates unit price, and records purchase cost atomically.
    Converts input pricing to Base INR. Scoped to user's restaurant.
    """
    profile = getattr(request.user, 'profile', None)
    restaurant = get_user_restaurant(request)
    initial_product = request.GET.get('product')

    if request.method == 'POST':
        form = StockInForm(request.POST, restaurant=restaurant)
        if form.is_valid():
            product = form.cleaned_data['product']
            supplier = form.cleaned_data['supplier']
            quantity = form.cleaned_data['quantity']
            raw_unit_price = form.cleaned_data['unit_price']
            notes = form.cleaned_data['notes']

            if raw_unit_price is None or raw_unit_price <= Decimal('0'):
                unit_price_base = product.purchase_price
            else:
                unit_price_base = profile.convert_to_base(raw_unit_price) if profile else raw_unit_price

            try:
                StockTransaction.record_stock_in(
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price_base,
                    user=request.user,
                    supplier=supplier,
                    notes=notes
                )
                messages.success(
                    request,
                    f"Stock-In recorded! Added {quantity} {product.unit} to {product.name}. "
                    f"New stock: {product.current_stock} {product.unit}."
                )
                return redirect('transaction_list')
            except ValidationError as e:
                messages.error(request, str(e.message if hasattr(e, 'message') else e))
            except Exception as e:
                messages.error(request, f"Error processing stock-in: {str(e)}")
    else:
        initial_data = {}
        if initial_product:
            try:
                prod = scope_queryset(request, Product.objects.all()).get(pk=initial_product)
                initial_data['product'] = prod
                initial_data['unit_price'] = profile.convert_from_base(prod.purchase_price) if profile else prod.purchase_price
            except Product.DoesNotExist:
                pass
        form = StockInForm(restaurant=restaurant, initial=initial_data)

    products_list = [
        {
            'id': p.id,
            'name': p.name,
            'unit': p.unit,
            'purchase_price': float(profile.convert_from_base(p.purchase_price) if profile else p.purchase_price),
            'minimum_stock': float(p.minimum_stock),
            'current_stock': float(p.current_stock)
        }
        for p in scope_queryset(request, Product.objects.all()).order_by('name')
    ]

    return render(request, 'transactions/stock_in.html', {
        'form': form,
        'products': products_list,
    })


@login_required
def stock_out_view(request):
    """
    Module 3 – Stock-Out (Consumption / Usage / Sales):
    Deducts stock atomically.
    Enforces validation rule: prevents negative stock! Scoped to user's restaurant.
    """
    profile = getattr(request.user, 'profile', None)
    restaurant = get_user_restaurant(request)
    initial_product = request.GET.get('product')

    if request.method == 'POST':
        form = StockOutForm(request.POST, restaurant=restaurant)
        if form.is_valid():
            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity']
            notes = form.cleaned_data['notes']

            try:
                StockTransaction.record_stock_out(
                    product=product,
                    quantity=quantity,
                    user=request.user,
                    notes=notes
                )
                product.refresh_from_db()

                # Dedicated low stock / finished notifications
                if product.current_stock <= Decimal('0.00'):
                    messages.error(
                        request,
                        f"🚨 STOCK FINISHED: '{product.name}' is now completely DEPLETED (0.00 {product.unit} remaining)! Immediate replenishment required."
                    )
                elif product.current_stock <= product.minimum_stock:
                    messages.warning(
                        request,
                        f"⚠️ LOW STOCK ALERT: '{product.name}' is now LOW on stock! Remaining: {product.current_stock} {product.unit} (Minimum threshold: {product.minimum_stock} {product.unit}). Please restock soon."
                    )
                else:
                    messages.success(
                        request,
                        f"Stock-Out recorded! Deducted {quantity} {product.unit} from {product.name}. Remaining stock: {product.current_stock} {product.unit}."
                    )
                return redirect('transaction_list')
            except ValidationError as e:
                msg = e.messages[0] if hasattr(e, 'messages') else str(e)
                messages.error(request, msg)
            except Exception as e:
                messages.error(request, f"Error processing stock-out: {str(e)}")
    else:
        initial_data = {}
        if initial_product:
            try:
                prod = scope_queryset(request, Product.objects.all()).get(pk=initial_product)
                initial_data['product'] = prod
            except Product.DoesNotExist:
                pass
        form = StockOutForm(restaurant=restaurant, initial=initial_data)

    products_list = [
        {
            'id': p.id,
            'name': p.name,
            'unit': p.unit,
            'purchase_price': float(profile.convert_from_base(p.purchase_price) if profile else p.purchase_price),
            'minimum_stock': float(p.minimum_stock),
            'current_stock': float(p.current_stock)
        }
        for p in scope_queryset(request, Product.objects.all()).order_by('name')
    ]

    return render(request, 'transactions/stock_out.html', {
        'form': form,
        'products': products_list,
    })


@admin_required
def stock_adjustment_view(request):
    profile = getattr(request.user, 'profile', None)
    restaurant = get_user_restaurant(request)
    initial_product = request.GET.get('product')

    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST, restaurant=restaurant)
        if form.is_valid():
            product = form.cleaned_data['product']
            target_quantity = form.cleaned_data['target_quantity']
            reason = form.cleaned_data.get('reason', 'Physical Count Correction')
            raw_notes = form.cleaned_data.get('notes', '').strip()
            full_notes = f"[{reason}] {raw_notes}" if raw_notes else f"[{reason}]"

            try:
                StockTransaction.record_adjustment(
                    product=product,
                    target_quantity=target_quantity,
                    user=request.user,
                    notes=full_notes
                )
                product.refresh_from_db()
                if product.current_stock <= Decimal('0.00'):
                    messages.error(
                        request,
                        f"🚨 STOCK FINISHED: '{product.name}' is now completely DEPLETED (0.00 {product.unit} remaining)! Immediate replenishment required."
                    )
                elif product.current_stock <= product.minimum_stock:
                    messages.warning(
                        request,
                        f"⚠️ LOW STOCK ALERT: '{product.name}' is now LOW on stock! Remaining: {product.current_stock} {product.unit} (Minimum threshold: {product.minimum_stock} {product.unit}). Please restock soon."
                    )
                else:
                    messages.success(
                        request,
                        f"Stock adjusted for {product.name}. Current stock updated to {target_quantity} {product.unit}."
                    )
                return redirect('transaction_list')
            except Exception as e:
                messages.error(request, f"Adjustment failed: {str(e)}")
    else:
        initial_data = {}
        if initial_product:
            try:
                prod = scope_queryset(request, Product.objects.all()).get(pk=initial_product)
                initial_data['product'] = prod
                initial_data['target_quantity'] = prod.current_stock
            except Product.DoesNotExist:
                pass
        form = StockAdjustmentForm(restaurant=restaurant, initial=initial_data)

    products_list = [
        {
            'id': p.id,
            'name': p.name,
            'unit': p.unit,
            'purchase_price': float(profile.convert_from_base(p.purchase_price) if profile else p.purchase_price),
            'minimum_stock': float(p.minimum_stock),
            'current_stock': float(p.current_stock)
        }
        for p in scope_queryset(request, Product.objects.all()).order_by('name')
    ]

    return render(request, 'transactions/stock_adjustment.html', {
        'form': form,
        'products': products_list,
    })
