from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal

from .models import Expense
from .forms import ExpenseForm
from transactions.models import StockTransaction
from accounts.decorators import admin_required
from accounts.models import Restaurant
from accounts.utils import scope_queryset, get_user_restaurant


@admin_required
def expense_list_view(request):
    """
    Module 4 – Expense Management:
    Manages operating expenditures (Rent, Utilities, Wages, Repairs).
    Converts amounts to active currency for display. Scoped to user's restaurant.
    """
    profile = getattr(request.user, 'profile', None)
    category = request.GET.get('category', '')
    search = request.GET.get('q', '').strip()

    expenses = scope_queryset(request, Expense.objects.all()).select_related('created_by')

    if category:
        expenses = expenses.filter(category=category)
    if search:
        expenses = expenses.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    # Monthly figures in Base INR
    now = timezone.now()
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    this_month_expenses_base = scope_queryset(request, Expense.objects.filter(
        expense_date__gte=first_of_month.date()
    )).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    this_month_purchases_base = scope_queryset(request, StockTransaction.objects.filter(
        transaction_type='IN',
        created_at__gte=first_of_month
    )).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    # Convert to user's active currency
    this_month_expenses = profile.convert_from_base(this_month_expenses_base) if profile else this_month_expenses_base
    this_month_purchases = profile.convert_from_base(this_month_purchases_base) if profile else this_month_purchases_base
    total_combined_month = this_month_expenses + this_month_purchases

    all_time_expenses_base = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    all_time_expenses = profile.convert_from_base(all_time_expenses_base) if profile else all_time_expenses_base

    paginator = Paginator(expenses, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'expenses': page_obj,
        'category_choices': Expense.CATEGORY_CHOICES,
        'selected_category': category,
        'search': search,
        'this_month_expenses': this_month_expenses,
        'this_month_purchases': this_month_purchases,
        'total_combined_month': total_combined_month,
        'all_time_expenses': all_time_expenses,
    }
    return render(request, 'expenses/expense_list.html', context)


@admin_required
def expense_create_view(request):
    profile = getattr(request.user, 'profile', None)
    restaurant = get_user_restaurant(request)
    if not restaurant and profile and profile.is_developer:
        restaurant = Restaurant.objects.first()

    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.restaurant = restaurant
            # Convert user entered amount from active currency to Base INR
            raw_amt = form.cleaned_data['amount']
            expense.amount = profile.convert_to_base(raw_amt) if profile else raw_amt
            expense.save()
            messages.success(request, f"Expense '{expense.title}' recorded for {restaurant.name if restaurant else 'business'}.")
            return redirect('expense_list')
    else:
        form = ExpenseForm()

    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'title': 'Record New Expense',
    })


@admin_required
def expense_update_view(request, pk):
    profile = getattr(request.user, 'profile', None)
    expense = get_object_or_404(scope_queryset(request, Expense.objects.all()), pk=pk)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            exp = form.save(commit=False)
            raw_amt = form.cleaned_data['amount']
            exp.amount = profile.convert_to_base(raw_amt) if profile else raw_amt
            exp.save()
            messages.success(request, f"Expense '{expense.title}' updated.")
            return redirect('expense_list')
    else:
        conv_amt = profile.convert_from_base(expense.amount) if profile else expense.amount
        form = ExpenseForm(instance=expense, initial={'amount': conv_amt})

    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'expense': expense,
        'title': f"Edit Expense: {expense.title}",
    })


@admin_required
def expense_delete_view(request, pk):
    expense = get_object_or_404(scope_queryset(request, Expense.objects.all()), pk=pk)
    if request.method == 'POST':
        title = expense.title
        expense.delete()
        messages.success(request, f"Expense '{title}' deleted.")
        return redirect('expense_list')
    return render(request, 'expenses/expense_confirm_delete.html', {'expense': expense})
