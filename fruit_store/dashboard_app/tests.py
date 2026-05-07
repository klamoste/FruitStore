from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse

from accounts_app.models import Profile
from orders_app.models import Order
from products_app.models import Category, Product


class DashboardViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff_user = User.objects.create_user(
            username='adminuser',
            password='secret123',
            is_staff=True,
        )
        Profile.objects.create(user=cls.staff_user, role='admin')
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
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Mango')

    def test_dashboard_handles_database_error(self):
        self.client.login(username='adminuser', password='secret123')

        with patch('dashboard_app.views.Order.objects.count', side_effect=DatabaseError('boom')):
            response = self.client.get(reverse('dashboard:dashboard'), follow=True, secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard data is temporarily unavailable')
