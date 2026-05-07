from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts_app.models import Profile
from products_app.models import Category, Product

from .models import Order


class CheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='checkout-user',
            password='secret123',
            first_name='Check',
            last_name='Out',
            email='checkout@example.com',
        )
        Profile.objects.create(
            user=self.user,
            role='customer',
            address='123 Test Street',
            contact_number='09123456789',
            city='Test City',
            state='TS',
        )
        category = Category.objects.create(name='Fresh Picks')
        self.product = Product.objects.create(
            name='Apple',
            description='Fresh apple',
            category=category,
            price=Decimal('100.00'),
            stock_quantity=5,
            unit='kg',
            is_available=True,
        )

    def test_gcash_checkout_marks_order_paid(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['cart'] = {
            str(self.product.id): {
                'quantity': 2,
                'price': '100.00',
            }
        }
        session.save()

        response = self.client.post(
            reverse('orders:checkout'),
            {'payment_method': 'GCASH', 'customer_note': 'Handle with care'},
        )

        self.assertRedirects(response, reverse('orders:order_detail', args=[1]))
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.status, 'paid')
        self.assertEqual(order.customer_note, 'Handle with care')
        self.assertEqual(order.total_price, Decimal('250.00'))
        self.assertTrue(order.order_code.startswith('ORD-'))
