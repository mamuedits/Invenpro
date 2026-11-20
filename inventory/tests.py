from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

from inventory.models import Category, Supplier, Product
from transactions.models import StockTransaction


class InventoryModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Dairy", description="Dairy products")
        self.supplier = Supplier.objects.create(name="Dairy Farm", phone="123456", email="dairy@test.com")
        self.product = Product.objects.create(
            name="Cheddar Cheese",
            category=self.category,
            unit="kg",
            purchase_price=Decimal("10.00"),
            current_stock=Decimal("15.00"),
            minimum_stock=Decimal("5.00")
        )

    def test_stock_valuation(self):
        # 15 kg * $10.00 = $150.00
        self.assertEqual(self.product.stock_value, Decimal("150.00"))

    def test_stock_status_healthy(self):
        self.assertEqual(self.product.stock_status, "Healthy")

    def test_stock_status_low(self):
        self.product.current_stock = Decimal("5.00")
        self.product.save()
        self.assertEqual(self.product.stock_status, "Low Stock")

    def test_stock_status_out_of_stock(self):
        self.product.current_stock = Decimal("0.00")
        self.product.save()
        self.assertEqual(self.product.stock_status, "Out of Stock")


class StockTransactionAtomicTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testoperator", password="password123")
        self.category = Category.objects.create(name="Poultry")
        self.supplier = Supplier.objects.create(name="Fresh Poultry")
        self.product = Product.objects.create(
            name="Chicken",
            category=self.category,
            unit="kg",
            purchase_price=Decimal("5.00"),
            current_stock=Decimal("10.00"),
            minimum_stock=Decimal("8.00")
        )

    def test_stock_in_atomic_increase(self):
        # Formula: New Stock = Current Stock + Purchased Quantity (10 + 20 = 30)
        tx = StockTransaction.record_stock_in(
            product=self.product,
            quantity=Decimal("20.00"),
            unit_price=Decimal("5.50"),
            user=self.user,
            supplier=self.supplier,
            notes="Weekly batch"
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("30.00"))
        self.assertEqual(self.product.purchase_price, Decimal("5.50"))
        self.assertEqual(tx.total_amount, Decimal("110.00"))

    def test_stock_out_atomic_deduction(self):
        # Formula: New Stock = Current Stock - Consumed Quantity (10 - 4 = 6)
        tx = StockTransaction.record_stock_out(
            product=self.product,
            quantity=Decimal("4.00"),
            user=self.user,
            notes="Kitchen lunch prep"
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("6.00"))
        self.assertEqual(tx.total_amount, Decimal("20.00"))

    def test_prevent_excess_stock_out(self):
        # Prevent Stock OUT when requested > current stock
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            StockTransaction.record_stock_out(
                product=self.product,
                quantity=Decimal("15.00"),  # Current stock is only 10.00
                user=self.user
            )
        self.product.refresh_from_db()
        # Ensure stock remained unchanged
        self.assertEqual(self.product.current_stock, Decimal("10.00"))

    def test_stock_adjustment(self):
        # Physical audit corrected stock from 10.00 to 12.50
        StockTransaction.record_adjustment(
            product=self.product,
            target_quantity=Decimal("12.50"),
            user=self.user,
            notes="Audit recount"
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("12.50"))


class SmartConsumptionAnalysisTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="chef", password="password123")
        self.cat = Category.objects.create(name="Meat")
        # Chicken with 10 kg current stock
        self.chicken = Product.objects.create(
            name="Chicken",
            category=self.cat,
            unit="kg",
            purchase_price=Decimal("6.00"),
            current_stock=Decimal("10.00"),
            minimum_stock=Decimal("10.00")
        )

        # Prompt scenario:
        # Chicken consumption in the last 7 days: 35 kg.
        # Average daily consumption: 5 kg.
        # Current stock: 10 kg.
        # Estimated remaining stock: 2 days.
        now = timezone.now()
        for i in range(7):
            StockTransaction.objects.create(
                product=self.chicken,
                user=self.user,
                transaction_type='OUT',
                quantity=Decimal("5.00"),
                unit_price=Decimal("6.00"),
                total_amount=Decimal("30.00"),
                created_at=now - timedelta(days=i, hours=2)
            )

    def test_burn_rate_and_remaining_days(self):
        analysis = self.chicken.get_consumption_analysis(days=7)
        self.assertEqual(analysis['total_consumed'], Decimal("35.00"))
        self.assertEqual(analysis['avg_daily'], Decimal("5.00"))
        # 10 kg / 5 kg/day = 2.0 days
        self.assertEqual(analysis['days_left'], 2.0)
        self.assertEqual(analysis['urgency'], 'critical')


class ViewEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(username="adminuser", password="adminpassword", email="admin@test.com")
        self.client.login(username="adminuser", password="adminpassword")

        self.cat = Category.objects.create(name="Dry Goods")
        self.product = Product.objects.create(
            name="Rice",
            category=self.cat,
            unit="kg",
            purchase_price=Decimal("2.00"),
            current_stock=Decimal("50.00"),
            minimum_stock=Decimal("10.00")
        )

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invenpro")
        self.assertContains(response, "Operational Dashboard")

    def test_product_list_view(self):
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rice")

    def test_smart_alerts_view(self):
        response = self.client.get(reverse('smart_alerts'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Smart Stock Alert & Consumption Analysis System")

    def test_reports_view(self):
        response = self.client.get(reverse('report_overview'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reports & Business Analytics")

    def test_export_csv_endpoints(self):
        resp_in = self.client.get(reverse('export_stock_in_csv'))
        self.assertEqual(resp_in.status_code, 200)
        self.assertEqual(resp_in['Content-Type'], 'text/csv')

        resp_val = self.client.get(reverse('export_inventory_valuation_csv'))
        self.assertEqual(resp_val.status_code, 200)
        self.assertEqual(resp_val['Content-Type'], 'text/csv')
