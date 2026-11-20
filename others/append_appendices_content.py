"""
append_appendices_content.py
Appends comprehensive Appendix details to report_content.py.
"""

appendix_data = '''

# ==============================================================================
# DETAILED APPENDIX CONTENT
# ==============================================================================

APPENDIX_B_CODE = [
    {
        "filename": "accounts/models.py (Multi-Tenant & Security Entities)",
        "language": "python",
        "code": """from django.db import models
from django.contrib.auth.models import User

class Restaurant(models.Model):
    name = models.CharField(max_length=150)
    restaurant_id = models.CharField(max_length=20, unique=True, editable=False)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.restaurant_id})"

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Restaurant Admin'),
        ('staff', 'Kitchen Staff'),
        ('developer', 'System Developer'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    phone = models.CharField(max_length=20, blank=True, null=True)
    display_password = models.CharField(max_length=128, blank=True, null=True)
    currency = models.CharField(max_length=10, default='INR')
    usd_rate = models.DecimalField(max_digits=10, decimal_places=4, default=84.00)
    eur_rate = models.DecimalField(max_digits=10, decimal_places=4, default=91.00)
    gbp_rate = models.DecimalField(max_digits=10, decimal_places=4, default=107.00)
    aed_rate = models.DecimalField(max_digits=10, decimal_places=4, default=23.00)
"""
    },
    {
        "filename": "accounts/decorators.py (Role-Based Access Control)",
        "language": "python",
        "code": """from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    \"\"\"Restricts view exclusively to Restaurant Admins and Developers.\"\"\"
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ['admin', 'developer']:
            messages.error(request, "Permission denied: Administrative access required.")
            return redirect('inventory:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def developer_required(view_func):
    \"\"\"Restricts view exclusively to Global System Developers.\"\"\"
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role != 'developer':
            messages.error(request, "Access restricted: Developer privileges required.")
            return redirect('inventory:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
"""
    },
    {
        "filename": "inventory/models.py (Intelligent Burn-Rate & Valuation Engine)",
        "language": "python",
        "code": """from django.db import models
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

class Product(models.Model):
    restaurant = models.ForeignKey('accounts.Restaurant', on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=150)
    unit = models.CharField(max_length=50) # kg, liter, piece, etc.
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    min_stock_level = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)

    def stock_status(self):
        if self.current_stock <= 0:
            return 'out_of_stock'
        elif self.current_stock <= self.min_stock_level:
            return 'low'
        return 'healthy'

    def stock_valuation(self):
        return round(self.current_stock * self.purchase_price, 2)

    def calculate_burn_rate_and_runway(self):
        \"\"\"Calculates trailing 7-day burn rate and days of remaining stock.\"\"\"
        seven_days_ago = timezone.now() - timedelta(days=7)
        consumed = self.stocktransaction_set.filter(
            transaction_type='out',
            created_at__gte=seven_days_ago
        ).aggregate(total=models.Sum('quantity'))['total'] or Decimal('0.00')

        daily_burn_rate = round(consumed / Decimal('7.0'), 2)
        if daily_burn_rate > Decimal('0.00'):
            runway_days = round(self.current_stock / daily_burn_rate, 1)
        else:
            runway_days = float('inf')

        return {
            'consumed_7d': consumed,
            'daily_burn_rate': daily_burn_rate,
            'runway_days': runway_days,
            'is_critical': (runway_days != float('inf') and runway_days <= 2.0),
        }
"""
    },
    {
        "filename": "transactions/views.py (Atomic Stock-Out with Zero-Negative Guard)",
        "language": "python",
        "code": """from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from .models import StockTransaction
from inventory.models import Product

def stock_out_view(request):
    restaurant = request.user.userprofile.restaurant
    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity = Decimal(request.POST.get('quantity', '0'))
        reason = request.POST.get('reason_notes', 'Kitchen Prep')

        with transaction.atomic():
            product = Product.objects.select_for_update().get(id=product_id, restaurant=restaurant)
            if quantity > product.current_stock:
                messages.error(request, f"Error: Cannot deduct {quantity} {product.unit}. Only {product.current_stock} available.")
                return redirect('transactions:stock_out')

            product.current_stock -= quantity
            product.save(update_fields=['current_stock'])

            StockTransaction.objects.create(
                restaurant=restaurant,
                product=product,
                user=request.user,
                transaction_type='out',
                quantity=quantity,
                unit_price=product.purchase_price,
                total_value=round(quantity * product.purchase_price, 2),
                notes=reason
            )
            messages.success(request, f"Deducted {quantity} {product.unit} of {product.name} successfully.")
            return redirect('transactions:stock_out')
    return render(request, 'transactions/stock_out.html')
"""
    }
]

DATA_DICTIONARY_TABLES = [
    {
        "table_name": "accounts_restaurant",
        "title": "Table C.1: Data Dictionary: accounts_restaurant Entity Schema",
        "headers": ["Field Name", "Data Type", "Length/Precision", "Null / Blank", "Default", "Constraints / Description"],
        "rows": [
            ["id", "AutoField / INTEGER", "Primary Key", "NOT NULL", "Auto Incremented", "Unique surrogate identifier for each restaurant tenant"],
            ["name", "VARCHAR", "150 characters", "NOT NULL", "None", "Legal or commercial business name of the restaurant"],
            ["restaurant_id", "VARCHAR", "20 characters", "NOT NULL", "Generated (RES-XXXXX)", "Unique tenant identifier code used for system scoping"],
            ["address", "TEXT", "Unlimited", "NULL / BLANK", "NULL", "Physical postal address of the restaurant premises"],
            ["phone", "VARCHAR", "20 characters", "NULL / BLANK", "NULL", "Primary contact telephone / mobile number"],
            ["created_at", "DATETIME", "Timestamp", "NOT NULL", "CURRENT_TIMESTAMP", "Date and time when the restaurant was registered in Invenpro"]
        ]
    },
    {
        "table_name": "accounts_userprofile",
        "title": "Table C.2: Data Dictionary: accounts_userprofile Entity Schema",
        "headers": ["Field Name", "Data Type", "Length/Precision", "Null / Blank", "Default", "Constraints / Description"],
        "rows": [
            ["id", "AutoField / INTEGER", "Primary Key", "NOT NULL", "Auto Incremented", "Surrogate primary key for user profile record"],
            ["user_id", "INTEGER", "Foreign Key (auth_user)", "NOT NULL", "None", "One-to-One association with Django auth_user entity"],
            ["restaurant_id", "INTEGER", "Foreign Key (Restaurant)", "NULL / BLANK", "NULL", "Multi-tenant tenant workspace linkage"],
            ["role", "VARCHAR", "20 characters", "NOT NULL", "'staff'", "RBAC role: 'admin', 'staff', or 'developer'"],
            ["phone", "VARCHAR", "20 characters", "NULL / BLANK", "NULL", "User's contact phone number"],
            ["display_password", "VARCHAR", "128 characters", "NULL / BLANK", "NULL", "Assigned password accessible to developer for admin recovery"],
            ["currency", "VARCHAR", "10 characters", "NOT NULL", "'INR'", "Active display currency code ('INR', 'USD', 'EUR', etc.)"],
            ["usd_rate", "DECIMAL", "(10, 4)", "NOT NULL", "84.0000", "Custom forex multiplier: 1 USD in INR"],
            ["eur_rate", "DECIMAL", "(10, 4)", "NOT NULL", "91.0000", "Custom forex multiplier: 1 EUR in INR"],
            ["gbp_rate", "DECIMAL", "(10, 4)", "NOT NULL", "107.0000", "Custom forex multiplier: 1 GBP in INR"],
            ["aed_rate", "DECIMAL", "(10, 4)", "NOT NULL", "23.0000", "Custom forex multiplier: 1 AED in INR"]
        ]
    },
    {
        "table_name": "inventory_product",
        "title": "Table C.3: Data Dictionary: inventory_product Entity Schema",
        "headers": ["Field Name", "Data Type", "Length/Precision", "Null / Blank", "Default", "Constraints / Description"],
        "rows": [
            ["id", "AutoField / INTEGER", "Primary Key", "NOT NULL", "Auto Incremented", "Primary key for catalog item"],
            ["restaurant_id", "INTEGER", "Foreign Key (Restaurant)", "NOT NULL", "None", "Scoping key binding product to specific restaurant"],
            ["category_id", "INTEGER", "Foreign Key (Category)", "NOT NULL", "None", "Department classification link"],
            ["name", "VARCHAR", "150 characters", "NOT NULL", "None", "Common culinary item name (e.g., Basmati Rice)"],
            ["unit", "VARCHAR", "50 characters", "NOT NULL", "None", "Physical unit of measurement ('kg', 'liter', 'piece')"],
            ["purchase_price", "DECIMAL", "(10, 2)", "NOT NULL", "0.00", "Cost price paid per unit in base INR currency"],
            ["current_stock", "DECIMAL", "(10, 2)", "NOT NULL", "0.00", "Current on-hand physical stock quantity"],
            ["min_stock_level", "DECIMAL", "(10, 2)", "NOT NULL", "5.00", "Minimum threshold buffer triggering low stock alerts"],
            ["created_at", "DATETIME", "Timestamp", "NOT NULL", "CURRENT_TIMESTAMP", "Timestamp of initial catalog registration"]
        ]
    },
    {
        "table_name": "transactions_stocktransaction",
        "title": "Table C.4: Data Dictionary: transactions_stocktransaction Entity Schema",
        "headers": ["Field Name", "Data Type", "Length/Precision", "Null / Blank", "Default", "Constraints / Description"],
        "rows": [
            ["id", "AutoField / INTEGER", "Primary Key", "NOT NULL", "Auto Incremented", "Surrogate primary key for ledger movement entry"],
            ["restaurant_id", "INTEGER", "Foreign Key (Restaurant)", "NOT NULL", "None", "Tenant scoping association"],
            ["product_id", "INTEGER", "Foreign Key (Product)", "NOT NULL", "None", "Referenced catalog product item"],
            ["user_id", "INTEGER", "Foreign Key (auth_user)", "NOT NULL", "None", "Audit tracking of employee who executed transaction"],
            ["supplier_id", "INTEGER", "Foreign Key (Supplier)", "NULL / BLANK", "NULL", "Linked vendor for Stock-In purchase receipts"],
            ["transaction_type", "VARCHAR", "10 characters", "NOT NULL", "None", "Movement classifier: 'in', 'out', or 'adjust'"],
            ["quantity", "DECIMAL", "(10, 2)", "NOT NULL", "None", "Physical quantity moved during transaction"],
            ["unit_price", "DECIMAL", "(10, 2)", "NOT NULL", "0.00", "Effective purchase cost per unit at time of transaction"],
            ["total_value", "DECIMAL", "(12, 2)", "NOT NULL", "0.00", "Computed monetary value (Quantity × Unit Price)"],
            ["notes", "TEXT", "Unlimited", "NULL / BLANK", "NULL", "Kitchen purpose, station order, or discrepancy audit reason"],
            ["created_at", "DATETIME", "Timestamp", "NOT NULL", "CURRENT_TIMESTAMP", "Immutable timestamp when transaction was committed"]
        ]
    }
]

APPENDIX_D_TEXT = (
    "1. Prerequisites:\\n"
    "   • Python 3.12 or above installed and configured in system PATH.\\n"
    "   • Git version control CLI tool.\\n"
    "   • Active Google Account with an App Password generated for SMTP email relay.\\n\\n"
    "2. Clone and Setup Environment:\\n"
    "   git clone https://github.com/muhammed-pp/invenpro-restaurant-inventory.git\\n"
    "   cd invenpro-restaurant-inventory\\n"
    "   python -m venv venv\\n"
    "   venv\\\\Scripts\\\\activate  # On Windows\\n"
    "   pip install -r requirements.txt\\n\\n"
    "3. Environment Variable Configuration (.env):\\n"
    "   Create a .env file in the project root directory with the following variables:\\n"
    "   SECRET_KEY=django-insecure-invenpro-production-secret-key-123456\\n"
    "   DEBUG=True\\n"
    "   ALLOWED_HOSTS=127.0.0.1,localhost\\n"
    "   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend\\n"
    "   EMAIL_HOST=smtp.gmail.com\\n"
    "   EMAIL_PORT=587\\n"
    "   EMAIL_USE_TLS=True\\n"
    "   EMAIL_HOST_USER=mamuedits@gmail.com\\n"
    "   EMAIL_HOST_PASSWORD=tgzl szmi huuy ygvz\\n\\n"
    "4. Database Migrations and Superuser Setup:\\n"
    "   python manage.py makemigrations accounts inventory transactions expenses reports\\n"
    "   python manage.py migrate\\n"
    "   python manage.py createsuperuser\\n\\n"
    "5. Launching the Local Development Server:\\n"
    "   python manage.py runserver 127.0.0.1:8000\\n"
    "   Open browser at: http://127.0.0.1:8000/accounts/login/"
)

APPENDIX_E_TEXT = (
    "1. Administrator Operations Guide:\\n"
    "   • Logging In: Navigate to /accounts/login/ and choose 'Admin / Developer' portal tab.\\n"
    "   • Store & Currency Setup: Go to /accounts/settings/ to configure dark/light theme, select display currency, and calibrate forex rates.\\n"
    "   • Catalog Management: Navigate to /products/ to register items, define units, set purchase costs, and assign minimum alert thresholds.\\n"
    "   • Stock-In Procurement: Navigate to /transactions/in/ when vendor deliveries arrive to record inbound batches and recognize invoice totals.\\n"
    "   • Financial Auditing: Access /reports/ to review total consumption costs, analyze top consumed ingredients, view expense doughnuts, and download CSV data.\\n\\n"
    "2. Kitchen Staff Operations Guide:\\n"
    "   • Shift Login: Select 'Staff Portal' at login, entering username and staff password.\\n"
    "   • Stock-Out Logging: Navigate to /transactions/out/. Select product, use Fast Presets (+1, +2, +5, +10) to select quantity, choose usage shortcut ('Kitchen Prep', 'Service Rush'), and confirm.\\n"
    "   • Monitoring Inventory Health: View the top dashboard health badges to watch for low-stock items before cooking rushes.\\n"
    "   • Password Assistance: Click 'Forgot Password?' on staff login to alert the administrator, who will reset credentials via the admin roster."
)
'''

with open(r"c:\LPU\7th sem\INT253\Pythonproject\report_content.py", "a", encoding="utf-8") as f:
    f.write(appendix_data)

print("Appendices appended successfully.")
