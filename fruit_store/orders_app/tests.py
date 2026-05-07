from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts_app.models import Profile
from products_app.models import Category, InventoryLog, Product

from .models import Order, OrderItem


class CheckoutFlowTests(TestCase):
    def setUp(self):
        self.password = 'pass12345'
        self.user = User.objects.create_user(
            username='checkout-user',
            password=self.password,
            email='checkout@example.com',
            first_name='Checkout',
            last_name='User',
        )
        Profile.objects.create(
            user=self.user,
            role='customer',
            address='123 Test Street',
            contact_number='09123456789',
            city='Test City',
            state='TS',
        )
        self.category = Category.objects.create(name='Fresh Fruits', description='Fresh fruit')
        self.product = Product.objects.create(
            name='Apple Pack',
            description='Test product',
            category=self.category,
            price=Decimal('10.00'),
            stock_quantity=10,
            unit='piece',
            is_available=True,
        )

    def login_and_add_to_cart(self, product=None, quantity=1, extra_post_data=None):
        product = product or self.product
        self.client.login(username=self.user.username, password=self.password)
        payload = {'quantity': quantity}
        if extra_post_data:
            payload.update(extra_post_data)
        return self.client.post(reverse('products:add_to_cart', args=[product.id]), payload)

    def test_cod_checkout_creates_order_and_updates_stock(self):
        self.login_and_add_to_cart(quantity=2)

        response = self.client.post(
            reverse('orders:checkout'),
            {
                'payment_method': Order.PAYMENT_METHOD_COD,
                'requested_delivery_date': (timezone.localdate() + timedelta(days=1)).isoformat(),
                'requested_delivery_time': Order.DELIVERY_PERIOD_MORNING,
                'customer_note': 'Handle with care',
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('orders:order_detail', args=[1]))
        order = Order.objects.get(user=self.user)
        self.product.refresh_from_db()

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.total_price, Decimal('70.00'))
        self.assertEqual(self.product.stock_quantity, 8)
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)
        self.assertEqual(InventoryLog.objects.filter(product=self.product, reason='sale').count(), 1)
        self.assertEqual(self.client.session.get('cart'), {})

    def test_gcash_checkout_marks_order_paid(self):
        self.login_and_add_to_cart(quantity=2)

        response = self.client.post(
            reverse('orders:checkout'),
            {
                'payment_method': Order.PAYMENT_METHOD_GCASH,
                'gcash_sender_name': 'Checkout User',
                'gcash_reference': '12345678',
                'requested_delivery_date': (timezone.localdate() + timedelta(days=1)).isoformat(),
                'requested_delivery_time': Order.DELIVERY_PERIOD_MORNING,
                'customer_note': 'Handle with care',
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('orders:order_detail', args=[1]))
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.status, 'paid')
        self.assertEqual(order.payment_method, Order.PAYMENT_METHOD_GCASH)
        self.assertEqual(order.gcash_reference, '12345678')
        self.assertEqual(order.customer_note, 'Handle with care')
        self.assertEqual(order.total_price, Decimal('70.00'))
        self.assertTrue(order.order_code.startswith('ORD-'))

    def test_gcash_checkout_requires_sender_name_and_reference(self):
        self.login_and_add_to_cart(quantity=1)

        response = self.client.post(
            reverse('orders:checkout'),
            {
                'payment_method': Order.PAYMENT_METHOD_GCASH,
                'gcash_sender_name': '',
                'gcash_reference': '',
                'requested_delivery_date': (timezone.localdate() + timedelta(days=1)).isoformat(),
                'requested_delivery_time': Order.DELIVERY_PERIOD_AFTERNOON,
                'customer_note': '',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter the GCash sender name used for this payment.')
        self.assertContains(response, 'Enter the GCash reference number before placing the order.')
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_rejects_insufficient_stock_after_item_is_in_cart(self):
        self.login_and_add_to_cart(quantity=3)
        self.product.stock_quantity = 1
        self.product.save(update_fields=['stock_quantity', 'updated_at'])

        response = self.client.post(
            reverse('orders:checkout'),
            {
                'payment_method': Order.PAYMENT_METHOD_COD,
                'requested_delivery_date': (timezone.localdate() + timedelta(days=1)).isoformat(),
                'requested_delivery_time': Order.DELIVERY_PERIOD_MORNING,
                'customer_note': '',
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('orders:cart'))
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(self.client.session.get('cart')[f'{self.product.id}:default']['quantity'], 3)
        messages = list(response.context['messages'])
        self.assertTrue(any('Apple Pack only has 1 left in stock.' in str(message) for message in messages))

    def test_cup_products_offer_sizes_and_store_selected_size_on_order(self):
        cup_product = Product.objects.create(
            name='Orange Juice',
            description='Fresh juice',
            category=self.category,
            price=Decimal('3.99'),
            stock_quantity=10,
            unit='cup',
            small_price=Decimal('3.99'),
            medium_price=Decimal('5.99'),
            large_price=Decimal('7.99'),
            is_available=True,
        )

        self.assertEqual(
            cup_product.available_cup_sizes,
            [
                {'value': 'small', 'label': 'Small Cup', 'price': Decimal('3.99'), 'unit_label': 'Cup'},
                {'value': 'medium', 'label': 'Medium Cup', 'price': Decimal('5.99'), 'unit_label': 'Cup'},
                {'value': 'large', 'label': 'Large Cup', 'price': Decimal('7.99'), 'unit_label': 'Cup'},
            ],
        )

        self.login_and_add_to_cart(
            product=cup_product,
            quantity=2,
            extra_post_data={'selected_size': 'medium'},
        )
        self.client.post(
            reverse('orders:checkout'),
            {
                'payment_method': Order.PAYMENT_METHOD_COD,
                'requested_delivery_date': (timezone.localdate() + timedelta(days=1)).isoformat(),
                'requested_delivery_time': Order.DELIVERY_PERIOD_MORNING,
                'customer_note': '',
            },
        )

        order_item = OrderItem.objects.get(order__user=self.user, product=cup_product)
        self.assertEqual(order_item.selected_size, 'medium')
        self.assertEqual(order_item.selected_unit_label, 'Medium Cup')
        self.assertEqual(order_item.unit_price, Decimal('5.99'))
