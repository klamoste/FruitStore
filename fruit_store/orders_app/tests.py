from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.conf import settings
from django.db import DatabaseError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from accounts_app.models import Profile
from orders_app.models import Order, OrderItem
from products_app.models import Category, Product


@override_settings(STORE_GCASH_NAME='Sofia Fruit Store', STORE_GCASH_NUMBER='09171234567')
class CheckoutFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='buyer',
            password='secret123',
            first_name='Sofia',
            last_name='Buyer',
            email='buyer@example.com',
        )
        Profile.objects.create(
            user=cls.user,
            role='customer',
            address='123 Mango Street',
            contact_number='09171234567',
            city='Quezon City',
            state='Metro Manila',
        )
        category = Category.objects.create(name='Fresh Fruit', description='Daily picks')
        cls.product = Product.objects.create(
            name='Mango',
            description='Sweet mangoes',
            category=category,
            price='100.00',
            stock_quantity=10,
            unit='piece',
            is_available=True,
        )

    def setUp(self):
        self.client.login(username='buyer', password='secret123')
        session = self.client.session
        session['cart'] = {
            str(self.product.id): {
                'product_id': str(self.product.id),
                'quantity': 2,
                'price': '100.00',
                'unit_label': 'Piece',
            }
        }
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

    def test_checkout_requires_gcash_details_for_gcash_payment(self):
        delivery_date = timezone.localdate() + timedelta(days=1)

        response = self.client.post(
            reverse('orders:checkout'),
            data={
                'payment_method': 'GCASH',
                'delivery_date': delivery_date.isoformat(),
                'delivery_window': 'morning',
                'customer_note': 'Please bring ripe fruit.',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter the sender name used for the GCash payment.')
        self.assertContains(response, 'Enter the GCash reference number.')
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_rejects_non_letter_gcash_sender_name(self):
        delivery_date = timezone.localdate() + timedelta(days=1)

        response = self.client.post(
            reverse('orders:checkout'),
            data={
                'payment_method': 'GCASH',
                'delivery_date': delivery_date.isoformat(),
                'delivery_window': 'morning',
                'gcash_sender_name': 'Sofia123',
                'gcash_reference_number': '1234567890',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'GCash sender name can use letters, spaces, periods, apostrophes, and hyphens.')
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_rejects_invalid_gcash_reference_number(self):
        delivery_date = timezone.localdate() + timedelta(days=1)

        response = self.client.post(
            reverse('orders:checkout'),
            data={
                'payment_method': 'GCASH',
                'delivery_date': delivery_date.isoformat(),
                'delivery_window': 'morning',
                'gcash_sender_name': 'Sofia Buyer',
                'gcash_reference_number': 'GC/12345',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'GCash reference number can use letters, numbers, and hyphens only.')
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_accepts_common_gcash_sender_name_and_reference_formats(self):
        delivery_date = timezone.localdate() + timedelta(days=1)

        response = self.client.post(
            reverse('orders:checkout'),
            data={
                'payment_method': 'GCASH',
                'delivery_date': delivery_date.isoformat(),
                'delivery_window': 'morning',
                'gcash_sender_name': "Sofia B. Buyer-Santos",
                'gcash_reference_number': 'GC-12345-AB',
            },
        )

        order = Order.objects.get()

        self.assertRedirects(response, reverse('orders:order_detail', args=[order.id]))
        self.assertEqual(order.gcash_sender_name, "Sofia B. Buyer-Santos")
        self.assertEqual(order.gcash_reference_number, 'GC-12345-AB')

    def test_checkout_shows_configured_gcash_account_details(self):
        response = self.client.get(reverse('orders:checkout'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sofia Fruit Store')
        self.assertContains(response, '09171234567')

    def test_checkout_persists_cod_delivery_fields(self):
        delivery_date = timezone.localdate() + timedelta(days=1)

        response = self.client.post(
            reverse('orders:checkout'),
            data={
                'payment_method': 'COD',
                'delivery_date': delivery_date.isoformat(),
                'delivery_window': 'morning',
                'customer_note': 'Leave at the gate.',
            },
        )

        order = Order.objects.get()

        self.assertRedirects(response, reverse('orders:order_detail', args=[order.id]))
        self.assertEqual(order.payment_method, 'COD')
        self.assertEqual(order.delivery_date, delivery_date)
        self.assertEqual(order.delivery_window, 'morning')
        self.assertEqual(order.customer_note, 'Leave at the gate.')
        self.assertEqual(order.total_price, Decimal('250.00'))

    def test_checkout_persists_delivery_and_gcash_fields(self):
        delivery_date = timezone.localdate() + timedelta(days=2)

        response = self.client.post(
            reverse('orders:checkout'),
            data={
                'payment_method': 'GCASH',
                'delivery_date': delivery_date.isoformat(),
                'delivery_window': 'afternoon',
                'gcash_sender_name': 'Sofia Buyer',
                'gcash_reference_number': '123456789',
                'customer_note': 'Please call before delivery.',
            },
        )

        order = Order.objects.get()

        self.assertRedirects(response, reverse('orders:order_detail', args=[order.id]))
        self.assertEqual(order.payment_method, 'GCASH')
        self.assertEqual(order.delivery_date, delivery_date)
        self.assertEqual(order.delivery_window, 'afternoon')
        self.assertEqual(order.gcash_sender_name, 'Sofia Buyer')
        self.assertEqual(order.gcash_reference_number, '123456789')
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.total_price, Decimal('250.00'))
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)

    def test_order_history_and_detail_show_payment_and_delivery_details(self):
        order = Order.objects.create(
            user=self.user,
            total_price='250.00',
            payment_method='GCASH',
            delivery_date=timezone.localdate() + timedelta(days=1),
            delivery_window='morning',
            gcash_sender_name='Sofia Buyer',
            gcash_reference_number='GC-REF-001',
            customer_note='Leave at the front desk.',
            status='pending',
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price='100.00',
            subtotal='200.00',
        )

        history_response = self.client.get(reverse('orders:order_history'))
        detail_response = self.client.get(reverse('orders:order_detail', args=[order.id]))

        self.assertContains(history_response, 'Payment: GCash')
        self.assertContains(history_response, 'GCash Ref: GC-REF-001')
        self.assertContains(detail_response, 'Payment and Delivery Details')
        self.assertContains(detail_response, 'GCash Sender')
        self.assertContains(detail_response, 'Morning')

    def test_checkout_rejects_past_delivery_date(self):
        delivery_date = timezone.localdate() - timedelta(days=1)

        response = self.client.post(
            reverse('orders:checkout'),
            data={
                'payment_method': 'COD',
                'delivery_date': delivery_date.isoformat(),
                'delivery_window': 'morning',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please review these fields before placing your order:')
        self.assertContains(response, 'Delivery date: Please choose a delivery date that is today or later.')
        self.assertContains(response, 'Please choose a delivery date that is today or later.')
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_rolls_back_if_order_item_write_fails(self):
        delivery_date = timezone.localdate() + timedelta(days=1)

        with patch(
            'orders_app.views.OrderItem.objects.create',
            side_effect=DatabaseError('simulated write failure'),
        ):
            response = self.client.post(
                reverse('orders:checkout'),
                data={
                    'payment_method': 'COD',
                    'delivery_date': delivery_date.isoformat(),
                    'delivery_window': 'morning',
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'We could not place your order because the database is temporarily unavailable.')
        self.assertEqual(Order.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)
