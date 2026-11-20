from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from decimal import Decimal
from accounts.models import Restaurant, UserProfile, PasswordResetOTP, StaffPasswordRequest
from inventory.models import Category, Product
from transactions.models import StockTransaction
from expenses.models import Expense


class RestaurantAutoDeletionTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create Developer
        self.developer = User.objects.create_superuser('dev_tester', 'dev@test.com', 'devpass123')
        self.dev_profile, _ = UserProfile.objects.get_or_create(user=self.developer)
        self.dev_profile.role = 'developer'
        self.dev_profile.save()

    def test_auto_delete_restaurant_when_sole_admin_deleted(self):
        # 1. Create a restaurant
        rest = Restaurant.objects.create(name='Solitary Bistro', phone='123456')

        # 2. Create the sole admin
        admin_u = User.objects.create_user('sole_admin', 'sole@test.com', 'adminpass')
        admin_u.profile.role = 'admin'
        admin_u.profile.restaurant = rest
        admin_u.profile.save()
        rest.owner = admin_u
        rest.save()

        # 3. Create a staff member
        staff_u = User.objects.create_user('staff_member', 'staff@test.com', 'staffpass')
        staff_u.profile.role = 'staff'
        staff_u.profile.restaurant = rest
        staff_u.profile.save()

        # 4. Create category, product, transaction, and expense
        cat = Category.objects.create(restaurant=rest, name='Staples')
        prod = Product.objects.create(restaurant=rest, name='Basmati Rice', category=cat, current_stock=Decimal('50.00'), purchase_price=Decimal('100.00'))
        tx = StockTransaction.objects.create(restaurant=rest, product=prod, user=admin_u, transaction_type='IN', quantity=Decimal('50.00'), unit_price=Decimal('100.00'))
        exp = Expense.objects.create(restaurant=rest, title='Gas cylinder', amount=Decimal('2000.00'), created_by=admin_u)

        self.assertTrue(Restaurant.objects.filter(pk=rest.pk).exists())
        self.assertTrue(Product.objects.filter(pk=prod.pk).exists())
        self.assertTrue(User.objects.filter(pk=staff_u.pk).exists())

        # 5. Delete the sole admin
        admin_u.delete()

        # 6. Verify Restaurant and ALL its data are gone
        self.assertFalse(Restaurant.objects.filter(pk=rest.pk).exists(), "Restaurant should be auto-deleted when its only admin is deleted")
        self.assertFalse(Product.objects.filter(pk=prod.pk).exists(), "Products should cascade-delete with restaurant")
        self.assertFalse(Category.objects.filter(pk=cat.pk).exists(), "Categories should cascade-delete with restaurant")
        self.assertFalse(StockTransaction.objects.filter(pk=tx.pk).exists(), "Transactions should cascade-delete with restaurant")
        self.assertFalse(Expense.objects.filter(pk=exp.pk).exists(), "Expenses should cascade-delete with restaurant")
        self.assertFalse(User.objects.filter(pk=staff_u.pk).exists(), "Staff user should be cleaned up when restaurant is deleted")

    def test_restaurant_persists_when_one_of_multiple_admins_deleted(self):
        rest = Restaurant.objects.create(name='Dual Admin Diner')

        admin1 = User.objects.create_user('admin_one', 'a1@test.com', 'pass1')
        admin1.profile.role = 'admin'
        admin1.profile.restaurant = rest
        admin1.profile.save()

        admin2 = User.objects.create_user('admin_two', 'a2@test.com', 'pass2')
        admin2.profile.role = 'admin'
        admin2.profile.restaurant = rest
        admin2.profile.save()

        # Delete admin1
        admin1.delete()

        # Restaurant must still exist because admin2 remains!
        self.assertTrue(Restaurant.objects.filter(pk=rest.pk).exists())
        self.assertTrue(User.objects.filter(pk=admin2.pk).exists())

        # Now delete admin2
        admin2.delete()

        # Now restaurant must be deleted!
        self.assertFalse(Restaurant.objects.filter(pk=rest.pk).exists())

    def test_developer_delete_admin_view(self):
        self.client.login(username='dev_tester', password='devpass123')

        rest = Restaurant.objects.create(name='Target Delete Restro')
        admin_u = User.objects.create_user('target_admin', 'target@test.com', 'adminpass')
        admin_u.profile.role = 'admin'
        admin_u.profile.restaurant = rest
        admin_u.profile.save()

        # Developer posts to delete admin
        url = reverse('delete_admin', kwargs={'user_id': admin_u.id})
        response = self.client.post(url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(pk=admin_u.pk).exists())
        self.assertFalse(Restaurant.objects.filter(pk=rest.pk).exists())

    def test_developer_delete_restaurant_view(self):
        self.client.login(username='dev_tester', password='devpass123')

        rest = Restaurant.objects.create(name='Direct Delete Restro')
        admin_u = User.objects.create_user('direct_admin', 'direct@test.com', 'adminpass')
        admin_u.profile.role = 'admin'
        admin_u.profile.restaurant = rest
        admin_u.profile.save()

        staff_u = User.objects.create_user('direct_staff', 'staff@test.com', 'staffpass')
        staff_u.profile.role = 'staff'
        staff_u.profile.restaurant = rest
        staff_u.profile.save()

        url = reverse('delete_restaurant', kwargs={'restaurant_id': rest.id})
        response = self.client.post(url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Restaurant.objects.filter(pk=rest.pk).exists())
        self.assertFalse(User.objects.filter(pk=admin_u.pk).exists())
        self.assertFalse(User.objects.filter(pk=staff_u.pk).exists())

    def test_developer_edit_admin_and_password_eye_view(self):
        self.client.login(username='dev_tester', password='devpass123')

        rest = Restaurant.objects.create(name='Edit Target Restro')
        admin_u = User.objects.create_user('orig_admin', 'orig@test.com', 'oldpass123')
        admin_u.profile.role = 'admin'
        admin_u.profile.restaurant = rest
        admin_u.profile.save()

        edit_url = reverse('edit_admin', kwargs={'user_id': admin_u.id})
        response = self.client.post(edit_url, {
            'username': 'updated_admin',
            'first_name': 'Updated',
            'last_name': 'Owner',
            'email': 'updated@test.com',
            'phone': '+91 99999 88888',
            'is_active': 'true',
            'new_password': 'NewStrongPass99!',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        admin_u.refresh_from_db()
        admin_u.profile.refresh_from_db()

        self.assertEqual(admin_u.username, 'updated_admin')
        self.assertEqual(admin_u.first_name, 'Updated')
        self.assertEqual(admin_u.last_name, 'Owner')
        self.assertEqual(admin_u.email, 'updated@test.com')
        self.assertEqual(admin_u.profile.phone, '+91 99999 88888')
        self.assertTrue(admin_u.check_password('NewStrongPass99!'))
        self.assertEqual(admin_u.profile.display_password, 'NewStrongPass99!')

        html = response.content.decode()
        self.assertIn('btn-toggle-pwd-row', html)
        self.assertIn('btn-edit-admin', html)
        self.assertIn('editAdminModal', html)
        self.assertIn('badge-rest-id', html)
        self.assertIn('badge-current-user', html)
        self.assertIn('NewStrongPass99!', html)


class AuthAndForgotPasswordTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.rest = Restaurant.objects.create(name='Spice Garden', phone='+91 98765 43210')

        self.admin_user = User.objects.create_user('spice_admin', 'owner@spicegarden.com', 'oldadminpass')
        self.admin_user.profile.role = 'admin'
        self.admin_user.profile.restaurant = self.rest
        self.admin_user.profile.phone = '+91 98765 43210'
        self.admin_user.profile.save()
        self.rest.owner = self.admin_user
        self.rest.save()

        self.staff_user = User.objects.create_user('spice_staff', 'staff@spicegarden.com', 'oldstaffpass')
        self.staff_user.profile.role = 'staff'
        self.staff_user.profile.restaurant = self.rest
        self.staff_user.profile.save()

    def test_login_and_staff_login_render_theme_toggle_and_logo_badge(self):
        res_login = self.client.get(reverse('login'))
        self.assertEqual(res_login.status_code, 200)
        html = res_login.content.decode()
        self.assertIn('guestThemeToggleBtn', html)
        self.assertIn('auth-logo-badge', html)
        self.assertIn(reverse('forgot_password'), html)

        res_staff = self.client.get(reverse('staff_login'))
        self.assertEqual(res_staff.status_code, 200)
        staff_html = res_staff.content.decode()
        self.assertIn('guestThemeToggleBtn', staff_html)
        self.assertIn('auth-logo-badge', staff_html)
        self.assertIn(reverse('staff_forgot_password'), staff_html)

    def test_guest_theme_toggle_ajax(self):
        res = self.client.get(
            reverse('toggle_guest_theme') + '?mode=dark',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['theme'], 'dark')

    def test_admin_forgot_password_email_otp_flow(self):
        # Step 1: Request Email OTP
        res1 = self.client.post(reverse('forgot_password'), {
            'identifier': 'spice_admin',
        }, follow=True)
        self.assertEqual(res1.status_code, 200)
        otp = PasswordResetOTP.objects.filter(user=self.admin_user, channel='email').first()
        self.assertIsNotNone(otp)
        self.assertEqual(len(otp.otp_code), 6)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(otp.otp_code, mail.outbox[0].body)

        # Step 2: Verify OTP
        res2 = self.client.post(reverse('forgot_password_verify'), {
            'action': 'verify',
            'otp_code': otp.otp_code,
        }, follow=True)
        self.assertEqual(res2.status_code, 200)
        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

        # Step 3: Set New Password
        res3 = self.client.post(reverse('forgot_password_reset'), {
            'new_password': 'FreshAdminPass2026!',
            'confirm_password': 'FreshAdminPass2026!',
        }, follow=True)
        self.assertEqual(res3.status_code, 200)
        self.admin_user.refresh_from_db()
        self.admin_user.profile.refresh_from_db()
        self.assertTrue(self.admin_user.check_password('FreshAdminPass2026!'))
        self.assertEqual(self.admin_user.profile.display_password, 'FreshAdminPass2026!')

    def test_staff_forgot_password_emails_restaurant_admin_and_logs_request(self):
        res = self.client.post(reverse('staff_forgot_password'), {
            'username': 'spice_staff',
            'staff_note': 'Please call me with the new password',
        })
        self.assertEqual(res.status_code, 200)

        # Email sent to Restaurant Admin
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('owner@spicegarden.com', mail.outbox[0].to)
        self.assertIn('spice_staff', mail.outbox[0].body)

        # StaffPasswordRequest recorded
        req_obj = StaffPasswordRequest.objects.filter(staff_user=self.staff_user, is_resolved=False).first()
        self.assertIsNotNone(req_obj)

        # Admin sees request on Staff Management page and resetting password resolves it
        self.client.force_login(self.admin_user)
        staff_page = self.client.get(reverse('staff_management'))
        self.assertIn('Pending Staff Password Reset Requests', staff_page.content.decode())

        self.client.post(reverse('reset_staff_password', kwargs={'staff_id': self.staff_user.id}), {
            'new_password': 'NewStaffPass123',
            'confirm_new_password': 'NewStaffPass123',
        }, follow=True)
        req_obj.refresh_from_db()
        self.assertTrue(req_obj.is_resolved)


class RoleBasedRestrictionsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.rest = Restaurant.objects.create(name='Spice Villa', phone='+91 91234 56789')

        self.admin = User.objects.create_user('villa_admin', 'admin@villa.com', 'adminpass123')
        self.admin.profile.role = 'admin'
        self.admin.profile.restaurant = self.rest
        self.admin.profile.save()
        self.rest.owner = self.admin
        self.rest.save()

        self.staff = User.objects.create_user('villa_staff', 'staff@villa.com', 'staffpass123')
        self.staff.profile.role = 'staff'
        self.staff.profile.restaurant = self.rest
        self.staff.profile.save()

        self.category = Category.objects.create(restaurant=self.rest, name='Bakery')
        self.product = Product.objects.create(
            restaurant=self.rest,
            name='Croissant',
            category=self.category,
            current_stock=Decimal('20.00'),
            purchase_price=Decimal('50.00')
        )

    def test_staff_blocked_from_admin_restricted_areas(self):
        self.client.force_login(self.staff)

        restricted_urls = [
            reverse('settings'),
            reverse('expense_list'),
            reverse('expense_create'),
            reverse('report_overview'),
            reverse('export_inventory_valuation_csv'),
            reverse('product_create'),
            reverse('product_update', kwargs={'pk': self.product.id}),
            reverse('product_delete', kwargs={'pk': self.product.id}),
            reverse('category_create'),
            reverse('supplier_create'),
            reverse('stock_adjustment'),
            reverse('staff_management'),
            reverse('admin_management'),
        ]

        for url in restricted_urls:
            resp = self.client.get(url, follow=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(resp.request['PATH_INFO'], [reverse('dashboard'), reverse('login')])
            messages_list = list(resp.context['messages'])
            self.assertTrue(any("Access denied" in str(m) for m in messages_list), f"Expected access denied message for {url}")

    def test_staff_allowed_operational_tasks(self):
        self.client.force_login(self.staff)

        # Dashboard
        res_dash = self.client.get(reverse('dashboard'))
        self.assertEqual(res_dash.status_code, 200)
        self.assertNotIn('Inventory Valuation', res_dash.content.decode())

        # Product list
        res_prod = self.client.get(reverse('product_list'))
        self.assertEqual(res_prod.status_code, 200)

        # Stock-In
        res_in = self.client.get(reverse('stock_in'))
        self.assertEqual(res_in.status_code, 200)

        # Stock-Out
        res_out = self.client.get(reverse('stock_out'))
        self.assertEqual(res_out.status_code, 200)

    def test_admin_allowed_full_restaurant_access(self):
        self.client.force_login(self.admin)

        allowed_urls = [
            reverse('settings'),
            reverse('expense_list'),
            reverse('report_overview'),
            reverse('product_list'),
            reverse('staff_management'),
            reverse('stock_adjustment'),
        ]

        for url in allowed_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, f"Admin should have access to {url}")
