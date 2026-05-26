from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import DatabaseError
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts_app.models import Profile
from orders_app.models import Order, OrderItem
from products_app.models import Category, Product


class DashboardViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_user(
            username='adminuser',
            password='secret123',
            is_staff=True,
        )
        Profile.objects.create(user=cls.admin_user, role='admin')
        cls.staff_user = User.objects.create_user(
            username='staffuser',
            password='secret123',
            is_staff=True,
        )
        Profile.objects.create(user=cls.staff_user, role='staff')
        customer = User.objects.create_user(username='customer', password='secret123')
        Profile.objects.create(user=customer, role='customer')
        category = Category.objects.create(name='Seasonal', description='Seasonal fruit')
        product = Product.objects.create(
            name='Mango',
            description='Sweet mango',
            category=category,
            price='8.00',
            stock_quantity=5,
            unit='piece',
            is_available=True,
        )
        Order.objects.create(user=customer, total_price='58.00', status='pending')
        cls.product = product

    def test_dashboard_renders_for_staff(self):
        self.client.login(username='adminuser', password='secret123')

        response = self.client.get(reverse('dashboard:dashboard'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Owner Control Center')
        self.assertContains(response, 'Mango')
        self.assertContains(response, 'Inventory Watch')
        self.assertContains(response, 'Account Directory')

    def test_dashboard_rejects_staff_without_admin_role(self):
        self.client.login(username='staffuser', password='secret123')

        response = self.client.get(reverse('dashboard:dashboard'), secure=True)

        self.assertEqual(response.status_code, 302)

    def test_dashboard_handles_database_error(self):
        self.client.login(username='adminuser', password='secret123')

        with patch('dashboard_app.views.Order.objects.count', side_effect=DatabaseError('boom')):
            response = self.client.get(reverse('dashboard:dashboard'), follow=True, secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total Revenue')
        self.assertContains(response, 'No orders yet')

    def test_dashboard_rejects_non_admin_users(self):
        customer = User.objects.get(username='customer')
        self.client.force_login(customer)

        response = self.client.get(reverse('dashboard:dashboard'), secure=True)

        self.assertEqual(response.status_code, 302)

    def test_admin_tool_pages_render_for_admin(self):
        self.client.login(username='adminuser', password='secret123')

        admin_page = self.client.get(reverse('dashboard:admin_tool_page'), secure=True)
        products_page = self.client.get(reverse('dashboard:products_tool_page'), secure=True)
        users_page = self.client.get(reverse('dashboard:users_tool_page'), secure=True)
        storefront_page = self.client.get(reverse('dashboard:storefront_tool_page'), secure=True)

        self.assertEqual(admin_page.status_code, 200)
        self.assertContains(admin_page, 'Admin Access')
        self.assertEqual(products_page.status_code, 200)
        self.assertContains(products_page, 'Product Management')
        self.assertEqual(users_page.status_code, 200)
        self.assertContains(users_page, 'User Management')
        self.assertContains(users_page, 'Create Customer Account')
        create_customer_page = self.client.get(reverse('dashboard:create_customer_tool_page'), secure=True)
        self.assertEqual(create_customer_page.status_code, 200)
        self.assertContains(create_customer_page, 'Create Customer')
        self.assertEqual(storefront_page.status_code, 200)
        self.assertContains(storefront_page, 'Storefront Preview')

    def test_create_customer_tool_page_creates_customer_account(self):
        self.client.login(username='adminuser', password='secret123')

        response = self.client.post(
            reverse('dashboard:create_customer_tool_page'),
            data={
                'username': 'newcustomer',
                'email': 'newcustomer@example.com',
                'first_name': 'New',
                'last_name': 'Customer',
                'password1': 'SecretPass123',
                'password2': 'SecretPass123',
                'contact_number': '09123456789',
                'address': '123 Orchard Lane',
                'city': 'Davao',
                'state': 'Davao del Sur',
            },
            secure=True,
        )

        self.assertEqual(response.status_code, 302)
        created_user = User.objects.get(username='newcustomer')
        self.assertEqual(created_user.email, 'newcustomer@example.com')
        self.assertFalse(created_user.is_staff)
        self.assertEqual(created_user.profile.role, 'customer')
        self.assertEqual(created_user.profile.city, 'Davao')

    def test_users_tool_page_deletes_customer_without_orders(self):
        self.client.login(username='adminuser', password='secret123')
        removable = User.objects.create_user(username='removable', password='secret123')
        Profile.objects.create(user=removable, role='customer')

        response = self.client.post(
            reverse('dashboard:users_tool_page'),
            data={'remove_customer_id': removable.id},
            secure=True,
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(id=removable.id).exists())

    def test_users_tool_page_deactivates_customer_with_orders(self):
        self.client.login(username='adminuser', password='secret123')
        customer = User.objects.get(username='customer')

        response = self.client.post(
            reverse('dashboard:users_tool_page'),
            data={'remove_customer_id': customer.id},
            secure=True,
        )

        self.assertEqual(response.status_code, 302)
        customer.refresh_from_db()
        self.assertFalse(customer.is_active)
        self.assertTrue(Order.objects.filter(user=customer).exists())

    def test_products_tool_page_creates_product(self):
        self.client.login(username='adminuser', password='secret123')
        category = Category.objects.get(name='Seasonal')

        response = self.client.post(
            reverse('dashboard:products_tool_page'),
            data={
                'name': 'Papaya',
                'description': 'Sweet papaya',
                'category': category.id,
                'price': '45.00',
                'stock_quantity': 14,
                'unit': 'piece',
                'is_available': 'on',
            },
            secure=True,
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Product.objects.filter(name='Papaya').exists())

    def test_products_tool_page_updates_product(self):
        self.client.login(username='adminuser', password='secret123')
        product = Product.objects.get(name='Mango')

        response = self.client.post(
            reverse('dashboard:products_tool_page'),
            data={
                'product_id': product.id,
                'name': 'Golden Mango',
                'description': 'Sweet mango',
                'category': product.category_id,
                'price': '9.50',
                'stock_quantity': 7,
                'unit': 'piece',
                'is_available': 'on',
            },
            secure=True,
        )

        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.name, 'Golden Mango')
        self.assertEqual(str(product.price), '9.50')

    def test_products_tool_page_toggles_product_visibility(self):
        self.client.login(username='adminuser', password='secret123')
        product = Product.objects.get(name='Mango')
        self.assertTrue(product.is_available)

        response = self.client.post(
            reverse('dashboard:products_tool_page'),
            data={'toggle_product_id': product.id},
            secure=True,
        )

        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertFalse(product.is_available)

    def test_products_tool_page_deletes_product_without_order_history(self):
        self.client.login(username='adminuser', password='secret123')
        product = Product.objects.create(
            name='Papaya',
            description='Fresh papaya',
            category=Category.objects.get(name='Seasonal'),
            price='12.00',
            stock_quantity=9,
            unit='piece',
            is_available=True,
        )

        response = self.client.post(
            reverse('dashboard:products_tool_page'),
            data={'delete_product_id': product.id},
            secure=True,
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(id=product.id).exists())

    def test_products_tool_page_deletes_product_with_order_history(self):
        self.client.login(username='adminuser', password='secret123')
        customer = User.objects.get(username='customer')
        product = Product.objects.get(name='Mango')
        order = Order.objects.create(user=customer, total_price='25.00', status='pending')
        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            product_category_name=product.category.name,
            product_unit=product.unit,
            quantity=1,
            unit_price='8.00',
            subtotal='8.00',
        )

        response = self.client.post(
            reverse('dashboard:products_tool_page'),
            data={'delete_product_id': product.id},
            secure=True,
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(id=product.id).exists())
        order_item.refresh_from_db()
        self.assertIsNone(order_item.product)
        self.assertEqual(order_item.product_name, 'Mango')

    def test_revenue_trend_uses_delivered_orders_by_completion_date(self):
        customer = User.objects.get(username='customer')
        recent_time = timezone.now()
        Order.objects.filter(status='pending').update(updated_at=recent_time)
        delivered_order = Order.objects.create(
            user=customer,
            total_price='40.00',
            status='delivered',
        )
        Order.objects.filter(id=delivered_order.id).update(updated_at=recent_time)

        last_7_days = recent_time.date() - timedelta(days=6)
        raw_daily_revenue = list(
            Order.objects.filter(status='delivered', updated_at__date__gte=last_7_days)
            .annotate(day=TruncDate('updated_at'))
            .values('day')
            .annotate(
                revenue=Coalesce(
                    Sum('total_price'),
                    Value(0),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
            .order_by('day')
        )

        self.assertEqual(sum(float(entry['revenue']) for entry in raw_daily_revenue), 40.0)
