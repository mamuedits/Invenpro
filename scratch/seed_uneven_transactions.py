import os
import sys
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import django
import random
from decimal import Decimal
from datetime import datetime, date, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockwise.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Restaurant, UserProfile
from accounts.utils import seed_restaurant_starter_pack
from inventory.models import Category, Supplier, Product
from transactions.models import StockTransaction
from expenses.models import Expense


def run_seeding():
    print("=== STARTING MULTI-TENANT UNEVEN TRANSACTION SEEDING ===")

    # 1. SETUP RESTAURANT 1: Tokki Restro
    tokki = Restaurant.objects.filter(name='Tokki Restro').first()
    if not tokki:
        tokki = Restaurant.objects.create(
            name='Tokki Restro',
            restaurant_id='RES-85790',
            phone='+91 98460 11223',
            address='12th Floor, Hi-Lite Business Park, Calicut, Kerala 673014',
            gst_number='32AAACT8579P1Z2'
        )

    # Ensure Tokki admin jithesh exists
    jithesh, _ = User.objects.get_or_create(username='jithesh', defaults={'email': 'jithesh@tokkirestro.com', 'first_name': 'Jithesh', 'last_name': 'Kumar'})
    jithesh.set_password('admin123')
    jithesh.save()
    p_jithesh, _ = UserProfile.objects.get_or_create(user=jithesh)
    p_jithesh.role = 'admin'
    p_jithesh.restaurant = tokki
    p_jithesh.save()
    tokki.owner = jithesh
    tokki.save()

    # Ensure Tokki staff unais exists
    unais, _ = User.objects.get_or_create(username='unais', defaults={'email': 'unais@tokkirestro.com', 'first_name': 'Unais', 'last_name': 'P'})
    unais.set_password('staff123')
    unais.save()
    p_unais, _ = UserProfile.objects.get_or_create(user=unais)
    p_unais.role = 'staff'
    p_unais.restaurant = tokki
    p_unais.save()

    # 2. SETUP RESTAURANT 2: Rumis Mashawi
    rumi_rest = Restaurant.objects.filter(name='Rumis Mashawi').first()
    if not rumi_rest:
        rumi_rest = Restaurant.objects.create(
            name='Rumis Mashawi',
            restaurant_id='RES-61410',
            phone='+91 98471 23456',
            address='Arabian Coast Road, Beach Promenade, Kozhikode, Kerala 673001',
            gst_number='32AABCR1234F1Z5'
        )

    # Ensure Rumis admin rumi_admin exists
    rumi_admin, _ = User.objects.get_or_create(username='rumi_admin', defaults={'email': 'admin@rumismashawi.com', 'first_name': 'Rumi', 'last_name': 'Hassan'})
    rumi_admin.set_password('admin123')
    rumi_admin.save()
    p_rumi, _ = UserProfile.objects.get_or_create(user=rumi_admin)
    p_rumi.role = 'admin'
    p_rumi.restaurant = rumi_rest
    p_rumi.save()
    rumi_rest.owner = rumi_admin
    rumi_rest.save()

    # Ensure Rumis staff rumi_staff exists
    rumi_staff, _ = User.objects.get_or_create(username='rumi_staff', defaults={'email': 'staff@rumismashawi.com', 'first_name': 'Rashid', 'last_name': 'Staff'})
    rumi_staff.set_password('staff123')
    rumi_staff.save()
    p_rumi_staff, _ = UserProfile.objects.get_or_create(user=rumi_staff)
    p_rumi_staff.role = 'staff'
    p_rumi_staff.restaurant = rumi_rest
    p_rumi_staff.save()

    # Seed starter pack for both
    seed_restaurant_starter_pack(tokki, user=jithesh, with_products=True)
    seed_restaurant_starter_pack(rumi_rest, user=rumi_admin, with_products=True)

    # Clear old stock transactions and expenses to rebuild clean historical timeline Oct 15 - Nov 17
    StockTransaction.objects.filter(restaurant__in=[tokki, rumi_rest]).delete()
    Expense.objects.filter(restaurant__in=[tokki, rumi_rest]).delete()

    print("Cleaned existing transactions. Now generating uneven timeline Oct 15 - Nov 17, 2026...")

    # Helper function to generate uneven transactions
    def generate_restaurant_timeline(rest, admin_user, staff_user, profile_type):
        random.seed(42 if profile_type == 'tokki' else 99)
        products = list(Product.objects.filter(restaurant=rest))
        prod_map = {p.name: p for p in products}
        suppliers = list(Supplier.objects.filter(restaurant=rest))
        sup_map = {s.name: s for s in suppliers}

        # We will track current running stock in python dict
        running_stock = {p.id: Decimal('0.00') for p in products}

        # Date range Oct 15 to Nov 17 (34 days)
        start_date = date(2026, 10, 15)
        end_date = date(2026, 11, 17)
        total_days = (end_date - start_date).days + 1

        tx_list = []

        if profile_type == 'tokki':
            # Profile: Tokki Restro (Restocks Mon & Thu, heavy weekend Fri-Sun rush)
            # High consumption items: Basmati Rice, Sunflower Oil, Chicken masala, Garam Masala,
            # Coke, Diet Coke, Juice Glass, Biriyani Plate, Container 650g, Star Aniece
            restock_days = [0, 4, 7, 11, 14, 18, 21, 25, 28, 32] # Uneven days from start_date
        else:
            # Profile: Rumis Mashawi (Restocks Tue & Sat, heavy Thu night & Sun rush)
            # High consumption items: Kayama Rice, Maida, Palm Oil, Dalda, Meat masala,
            # Cardamom, Cloves, Cinnamon, Sprite, Fanta, Coconut, Carry Bag 13-16, Packing cover 8-10
            restock_days = [1, 5, 8, 12, 15, 19, 22, 26, 29, 33]

        # PHASE 1: Initial Major Stock-In on Day 0 or Day 1
        initial_day = 0 if profile_type == 'tokki' else 1
        init_dt = datetime.combine(start_date + timedelta(days=initial_day), datetime.min.time()) + timedelta(hours=8, minutes=30)
        
        for p in products:
            # Determine initial delivery quantity based on item nature
            if 'Rice' in p.name:
                qty = Decimal(random.choice(['80.00', '100.00', '120.00']))
            elif p.category.name == 'Cooking Oils & Fats':
                qty = Decimal(random.choice(['40.00', '50.00', '60.00']))
            elif p.category.name == 'Whole Spices':
                qty = Decimal(random.choice(['4.00', '6.00', '8.00']))
            elif p.category.name == 'Beverages & Drinks':
                qty = Decimal(random.choice(['72.00', '96.00', '120.00']))
            elif p.category.name == 'Packaging & Disposables':
                qty = Decimal(random.choice(['50.00', '60.00', '70.00']))
            elif p.category.name == 'Crockery & Tableware':
                qty = Decimal(random.choice(['48.00', '60.00', '72.00']))
            else:
                qty = Decimal(random.choice(['20.00', '30.00', '40.00']))

            running_stock[p.id] += qty
            sup = suppliers[p.id % len(suppliers)] if suppliers else None
            tx = StockTransaction.objects.create(
                restaurant=rest,
                product=p,
                supplier=sup,
                user=admin_user,
                transaction_type='IN',
                quantity=qty,
                unit_price=p.purchase_price,
                total_amount=qty * p.purchase_price,
                notes=f"Initial vendor delivery batch #{1000 + p.id} - Received in full"
            )
            StockTransaction.objects.filter(pk=tx.pk).update(created_at=timezone.make_aware(init_dt))

        # PHASE 2: Day-by-Day Historical Progression (Oct 16 to Nov 17)
        for day_offset in range(initial_day + 1, total_days):
            curr_date = start_date + timedelta(days=day_offset)
            is_weekend = curr_date.weekday() in [4, 5, 6] # Fri, Sat, Sun

            # Check if this day is a Restocking Day (Stock IN)
            if day_offset in restock_days:
                # Restock a subset of items (uneven deliveries)
                in_dt = datetime.combine(curr_date, datetime.min.time()) + timedelta(hours=9, minutes=random.randint(15, 50))
                # Pick 8-16 random products that need restocking
                restock_candidates = [p for p in products if running_stock[p.id] < Decimal('150.00')]
                selected_restock = random.sample(restock_candidates, min(len(restock_candidates), random.randint(10, 16)))
                
                for p in selected_restock:
                    if 'Rice' in p.name:
                        add_qty = Decimal(random.choice(['40.00', '50.00', '75.00']))
                    elif p.category.name == 'Cooking Oils & Fats':
                        add_qty = Decimal(random.choice(['20.00', '30.00', '40.00']))
                    elif p.category.name == 'Whole Spices':
                        add_qty = Decimal(random.choice(['2.00', '3.50', '5.00']))
                    elif p.category.name == 'Beverages & Drinks':
                        add_qty = Decimal(random.choice(['48.00', '72.00']))
                    elif p.category.name == 'Packaging & Disposables':
                        add_qty = Decimal(random.choice(['25.00', '35.00', '50.00']))
                    else:
                        add_qty = Decimal(random.choice(['10.00', '15.00', '25.00']))

                    running_stock[p.id] += add_qty
                    sup = suppliers[p.id % len(suppliers)] if suppliers else None
                    tx = StockTransaction.objects.create(
                        restaurant=rest,
                        product=p,
                        supplier=sup,
                        user=admin_user if random.random() > 0.3 else staff_user,
                        transaction_type='IN',
                        quantity=add_qty,
                        unit_price=p.purchase_price,
                        total_amount=add_qty * p.purchase_price,
                        notes=f"Replenishment shipment PO-{random.randint(4000, 9999)} - Quality passed"
                    )
                    StockTransaction.objects.filter(pk=tx.pk).update(created_at=timezone.make_aware(in_dt))

            # Stock OUT (Daily kitchen and counter consumption)
            # Pick 12-22 items used today
            out_candidates = [p for p in products if running_stock[p.id] > Decimal('5.00')]
            if out_candidates:
                num_items_out = random.randint(14, min(24, len(out_candidates)))
                selected_out = random.sample(out_candidates, num_items_out)
                
                for p in selected_out:
                    max_allowed = running_stock[p.id] - Decimal('1.00')
                    if max_allowed <= Decimal('0.50'):
                        continue

                    # Uneven consumption multiplier for weekend vs weekday
                    mult = Decimal('2.2') if is_weekend else Decimal('1.0')

                    if 'Rice' in p.name:
                        base_out = Decimal(random.choice(['6.00', '8.50', '12.00', '15.00']))
                    elif p.category.name == 'Cooking Oils & Fats':
                        base_out = Decimal(random.choice(['3.00', '4.50', '6.00']))
                    elif p.category.name == 'Whole Spices':
                        base_out = Decimal(random.choice(['0.20', '0.40', '0.60']))
                    elif p.category.name == 'Beverages & Drinks':
                        base_out = Decimal(random.choice(['8.00', '12.00', '18.00', '24.00']))
                    elif p.category.name == 'Packaging & Disposables':
                        base_out = Decimal(random.choice(['5.00', '8.00', '12.00']))
                    elif p.category.name == 'Crockery & Tableware':
                        # Crockery doesn't consume daily unless broken/replaced
                        base_out = Decimal('0.00') if random.random() > 0.1 else Decimal('2.00')
                    else:
                        base_out = Decimal(random.choice(['1.50', '2.50', '4.00']))

                    actual_out = round(base_out * mult, 2)
                    if actual_out > max_allowed:
                        actual_out = round(max_allowed * Decimal('0.7'), 2)

                    if actual_out > Decimal('0.00'):
                        running_stock[p.id] -= actual_out
                        out_hour = random.choice([13, 14, 20, 21, 22]) # Lunch or Dinner rush
                        out_minute = random.randint(10, 55)
                        out_dt = datetime.combine(curr_date, datetime.min.time()) + timedelta(hours=out_hour, minutes=out_minute)

                        reasons = [
                            "Daily kitchen cooking & service batch",
                            "Dinner rush & catering counter usage",
                            "Weekend dine-in banquet preparation",
                            "Takeaway packaging & delivery dispatch",
                            "Kitchen usage verified by Head Chef",
                            "Beverage counter daily sales reconciliation"
                        ]
                        tx = StockTransaction.objects.create(
                            restaurant=rest,
                            product=p,
                            supplier=None,
                            user=staff_user if random.random() > 0.4 else admin_user,
                            transaction_type='OUT',
                            quantity=actual_out,
                            unit_price=p.purchase_price,
                            total_amount=actual_out * p.purchase_price,
                            notes=random.choice(reasons)
                        )
                        StockTransaction.objects.filter(pk=tx.pk).update(created_at=timezone.make_aware(out_dt))

        # Reconcile Product.current_stock to exactly match running_stock
        for p in products:
            final_stock = running_stock[p.id]
            p.current_stock = max(Decimal('0.00'), final_stock)
            p.save()

        # Seed 6-8 Operating Expenses across the date range
        expense_templates = [
            ('Commercial LPG Gas Cylinders (4x 19kg)', 'utilities', Decimal('8400.00'), 'Kitchen cooking gas replenishment'),
            ('Electricity & Central AC Utility Bill', 'utilities', Decimal('18500.00'), 'Monthly power bill for dining and kitchen'),
            ('Kitchen Staff Weekly Wages', 'salaries', Decimal('24000.00'), 'Cooks and kitchen helper weekly wage disbursal'),
            ('Exhaust Hood & Deep Fryer Maintenance', 'maintenance', Decimal('4500.00'), 'Routine kitchen chimney service and filter clean'),
            ('Local Food Festival & Social Ads Promotion', 'marketing', Decimal('6200.00'), 'Instagram & billboard sponsorship for new menu'),
            ('Sanitation Supplies & Dishwashing Liquid', 'supplies', Decimal('3100.00'), 'Floor cleaners, sanitizer drums and degreasers'),
            ('Municipal Food Safety Trade License Fee', 'licensing', Decimal('5000.00'), 'Annual health inspection & permit renewal fee'),
        ]
        for idx, (title, cat, amt, desc) in enumerate(expense_templates):
            exp_date = start_date + timedelta(days=idx * 4 + 2)
            if exp_date <= end_date:
                Expense.objects.create(
                    restaurant=rest,
                    title=f"{title} - {rest.name[:6]}",
                    category=cat,
                    amount=amt + Decimal(random.randint(100, 800)),
                    description=desc,
                    expense_date=exp_date,
                    created_by=admin_user
                )

        total_tx = StockTransaction.objects.filter(restaurant=rest).count()
        total_in = StockTransaction.objects.filter(restaurant=rest, transaction_type='IN').count()
        total_out = StockTransaction.objects.filter(restaurant=rest, transaction_type='OUT').count()
        print(f"Generated for {rest.name}: {total_tx} transactions ({total_in} IN, {total_out} OUT). Products: {len(products)}")

    # Run for Tokki Restro
    generate_restaurant_timeline(tokki, jithesh, unais, 'tokki')

    # Run for Rumis Mashawi
    generate_restaurant_timeline(rumi_rest, rumi_admin, rumi_staff, 'rumis')

    print("=== SEEDING COMPLETED SUCCESSFULLY ===")

if __name__ == '__main__':
    run_seeding()
