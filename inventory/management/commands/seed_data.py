from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decimal import Decimal

from accounts.models import UserProfile
from inventory.models import Category, Supplier, Product
from transactions.models import StockTransaction
from expenses.models import Expense


class Command(BaseCommand):
    help = "Initializes StockWise with fresh store inventory (Flour & Base categories, INR currency)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--wipe',
            action='store_true',
            help='Wipes all existing inventory data before seeding fresh entries',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Setting up fresh StockWise database..."))

        # 1. Users & Profile with INR currency default
        admin_user, created = User.objects.get_or_create(username="admin")
        if created:
            admin_user.set_password("adminpassword123")
            admin_user.email = "admin@stockwise.local"
            admin_user.first_name = "Store"
            admin_user.last_name = "Admin"
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            profile, _ = UserProfile.objects.get_or_create(user=admin_user)
            profile.role = "admin"
            profile.phone = "+91 98765 43210"
            profile.business_name = "StockWise Store & Kitchen"
            profile.currency = "INR"
            profile.theme_mode = "light"
            profile.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin / adminpassword123"))
        else:
            profile, _ = UserProfile.objects.get_or_create(user=admin_user)
            profile.currency = "INR"
            profile.save()

        # Wipe previous data if flag set or if needed
        if options.get('wipe', False):
            StockTransaction.objects.all().delete()
            Expense.objects.all().delete()
            Product.objects.all().delete()
            Supplier.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.NOTICE("Wiped existing inventory data."))

        # 2. Fresh Categories: Flour & Base
        cat_flour, _ = Category.objects.get_or_create(
            name="Flour",
            defaults={'description': "Flours, grains, and baking powders"}
        )
        cat_base, _ = Category.objects.get_or_create(
            name="Base",
            defaults={'description': "Beverage bases, tea, and coffee powders"}
        )

        # 3. Fresh Products
        # Category: Flour
        # Maida - 50kgmin - Stock0
        # Atta - 10kgmin - Stock0
        # Category: Base
        # Tea Powder - 1kgmin - Stock0
        # Coffee Powder - 1kgmin - Stock0
        fresh_items = [
            ("Maida", cat_flour, "kg", Decimal("40.00"), Decimal("0.00"), Decimal("50.00")),
            ("Atta", cat_flour, "kg", Decimal("35.00"), Decimal("0.00"), Decimal("10.00")),
            ("Tea Powder", cat_base, "kg", Decimal("250.00"), Decimal("0.00"), Decimal("1.00")),
            ("Coffee Powder", cat_base, "kg", Decimal("450.00"), Decimal("0.00"), Decimal("1.00")),
        ]

        for pname, cat, unit, price, cur_stock, min_stock in fresh_items:
            prod, _ = Product.objects.get_or_create(
                name=pname,
                defaults={
                    'category': cat,
                    'unit': unit,
                    'purchase_price': price,
                    'current_stock': cur_stock,
                    'minimum_stock': min_stock,
                }
            )
            prod.category = cat
            prod.unit = unit
            prod.current_stock = cur_stock
            prod.minimum_stock = min_stock
            prod.save()
            self.stdout.write(self.style.SUCCESS(f"Initialized {prod.name}: Min {prod.minimum_stock}{prod.unit}, Stock {prod.current_stock}{prod.unit}"))

        self.stdout.write(self.style.SUCCESS("StockWise fresh database successfully configured!"))
