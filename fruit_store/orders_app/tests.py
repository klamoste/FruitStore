from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.conf import settings
from django.core import mail
from django.db import DatabaseError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from accounts_app.models import Profile
from orders_app.models import DeliveryZone, Order, OrderItem
from products_app.models import Category, Product


@override_settings(
    STORE_GCASH_NAME='Sofia Fruit Store',
    STORE_GCASH_NUMBER='09171234567',
    STORE_NOTIFICATION_EMAIL='ops@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
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
                'fulfillment_method': 'delivery',
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
                'fulfillment_method': 'delivery',
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
                'fulfillment_method': 'delivery',
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
                'fulfillment_method': 'delivery',
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
                'fulfillment_method': 'delivery',
                'payment_method': 'COD',
                'delivery_date': delivery_date.isoformat(),
                'delivery_window': 'morning',
                'customer_note': 'Leave at the gate.',
            },
        )

        order = Order.objects.get()

        self.assertRedirects(response, reverse('orders:order_detail', args=[order.id]))
        self.assertEqual(order.fulfillment_method, 'delivery')
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
                'fulfillment_method': 'delivery',
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

    def test_checkout_allows_store_pickup_without_shipping_fee(self):
        pickup_date = timezone.localdate() + timedelta(days=1)

        response = self.client.post(
            reverse('orders:checkout'),
            data={
                'fulfillment_method': 'pickup',
                'payment_method': 'COD',
                'delivery_date': pickup_date.isoformat(),
                'customer_note': 'I will pick this up myself.',
            },
        )

        order = Order.objects.get()

        self.assertRedirects(response, reverse('orders:order_detail', args=[order.id]))
        self.assertEqual(order.fulfillment_method, 'pickup')
        self.assertEqual(order.delivery_date, pickup_date)
        self.assertEqual(order.delivery_window, '')
        self.assertEqual(order.total_price, Decimal('200.00'))

    def test_checkout_uses_higher_zone_fee_for_farther_delivery_city(self):
        profile = Profile.objects.get(user=self.user)
        profile.city = 'Taguig'
        profile.save(update_fields=['city'])
        delivery_date = timezone.localdate() + timedelta(days=1)

        response = self.client.post(
            reverse('orders:checkout'),
            data={
                'fulfillment_method': 'delivery',
                'payment_method': 'COD',
                'delivery_date': delivery_date.isoformat(),
                'delivery_window': 'morning',
            },
        )

        order = Order.objects.get()

        self.assertRedirects(response, reverse('orders:order_detail', args=[order.id]))
        self.assertEqual(order.total_price, Decimal('280.00'))

    def test_checkout_uses_configured_delivery_zone_and_sends_notifications(self):
        DeliveryZone.objects.create(
            name='Bacuag Express',
            city='Quezon City',
            state='Metro Manila',
            fee='65.00',
            estimated_min_days=0,
            estimated_max_days=1,
            priority=1,
        )
        delivery_date = timezone.localdate() + timedelta(days=1)

        response = self.client.post(
            reverse('orders:checkout'),
            data={
                'fulfillment_method': 'delivery',
                'payment_method': 'COD',
                'delivery_date': delivery_date.isoformat(),
                'delivery_window': 'morning',
            },
        )

        order = Order.objects.get()

        self.assertRedirects(response, reverse('orders:order_detail', args=[order.id]))
        self.assertEqual(order.total_price, Decimal('265.00'))
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(order.order_code, mail.outbox[0].body)

    def test_order_history_and_detail_show_payment_and_delivery_details(self):
        order = Order.objects.create(
            user=self.user,
            total_price='250.00',
            fulfillment_method='delivery',
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

        self.assertContains(history_response, 'Fulfillment: Delivery')
        self.assertContains(history_response, 'Payment: GCash')
        self.assertContains(history_response, 'GCash Ref: GC-REF-001')
        self.assertContains(detail_response, 'Payment and Fulfillment Details')
        self.assertContains(detail_response, 'GCash Sender')
        self.assertContains(detail_response, 'Morning')
        self.assertContains(detail_response, 'Estimated Arrival')

    def test_checkout_rejects_past_delivery_date(self):
        delivery_date = timezone.localdate() - timedelta(days=1)

        response = self.client.post(
            reverse('orders:checkout'),
            data={
                'fulfillment_method': 'delivery',
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
                    'fulfillment_method': 'delivery',
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


class OrderDetailAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = User.objects.create_user(
            username='buyer2',
            password='secret123',
            first_name='Buyer',
            last_name='Two',
            email='buyer2@example.com',
        )
        Profile.objects.create(
            user=cls.customer,
            role='customer',
            address='123 Mango Street',
            contact_number='09171234567',
            city='Quezon City',
            state='Metro Manila',
        )
        cls.staff_user = User.objects.create_user(
            username='adminviewer',
            password='secret123',
            is_staff=True,
        )
        Profile.objects.create(user=cls.staff_user, role='admin')
        cls.admin_role_user = User.objects.create_user(
            username='roleadmin',
            password='secret123',
        )
        Profile.objects.create(user=cls.admin_role_user, role='admin')
        category = Category.objects.create(name='Imported', description='Imported fruit')
        product = Product.objects.create(
            name='Orange',
            description='Fresh orange',
            category=category,
            price='125.00',
            stock_quantity=20,
            unit='piece',
            is_available=True,
        )
        cls.order = Order.objects.create(
            user=cls.customer,
            total_price='175.00',
            fulfillment_method='delivery',
            payment_method='COD',
            delivery_date=timezone.localdate() + timedelta(days=1),
            delivery_window='morning',
            status='pending',
        )
        OrderItem.objects.create(
            order=cls.order,
            product=product,
            quantity=1,
            unit_price='125.00',
            subtotal='125.00',
        )

    def test_staff_can_view_customer_order_detail(self):
        self.client.login(username='adminviewer', password='secret123')

        response = self.client.get(reverse('orders:order_detail', args=[self.order.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.order.order_code)

    def test_admin_role_can_view_customer_order_detail(self):
        self.client.login(username='roleadmin', password='secret123')

        response = self.client.get(reverse('orders:order_detail', args=[self.order.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.order.order_code)

    def test_other_customer_cannot_view_someone_elses_order_detail(self):
        other_customer = User.objects.create_user(
            username='otherbuyer',
            password='secret123',
        )
        Profile.objects.create(user=other_customer, role='customer')
        self.client.login(username='otherbuyer', password='secret123')

        response = self.client.get(reverse('orders:order_detail', args=[self.order.id]))

        self.assertEqual(response.status_code, 404)


class OrderOperationsDashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff_user = User.objects.create_user(
            username='opsstaff',
            password='secret123',
            is_staff=True,
        )
        Profile.objects.create(user=cls.staff_user, role='staff')
        cls.customer = User.objects.create_user(
            username='opsbuyer',
            password='secret123',
            first_name='Ops',
            last_name='Buyer',
            email='opsbuyer@example.com',
        )
        Profile.objects.create(
            user=cls.customer,
            role='customer',
            address='Main Street',
            contact_number='09170000000',
            city='Quezon City',
            state='Metro Manila',
        )
        category = Category.objects.create(name='Seasonal', description='Seasonal')
        product = Product.objects.create(
            name='Pineapple',
            description='Fresh pineapple',
            category=category,
            price='80.00',
            stock_quantity=30,
            unit='piece',
            is_available=True,
        )
        cls.order = Order.objects.create(
            user=cls.customer,
            total_price='130.00',
            fulfillment_method='delivery',
            payment_method='COD',
            delivery_date=timezone.localdate(),
            delivery_window='morning',
            status='pending',
        )
        OrderItem.objects.create(
            order=cls.order,
            product=product,
            quantity=1,
            unit_price='80.00',
            subtotal='80.00',
        )
        cls.delivered_order = Order.objects.create(
            user=cls.customer,
            total_price='210.00',
            fulfillment_method='delivery',
            payment_method='GCASH',
            delivery_date=timezone.localdate() - timedelta(days=1),
            delivery_window='afternoon',
            status='delivered',
            assigned_courier='Rider Two',
        )
        OrderItem.objects.create(
            order=cls.delivered_order,
            product=product,
            quantity=2,
            unit_price='80.00',
            subtotal='160.00',
        )
        cls.cancelled_order = Order.objects.create(
            user=cls.customer,
            total_price='95.00',
            fulfillment_method='pickup',
            payment_method='COD',
            delivery_date=timezone.localdate(),
            status='cancelled',
        )
        OrderItem.objects.create(
            order=cls.cancelled_order,
            product=product,
            quantity=1,
            unit_price='80.00',
            subtotal='80.00',
        )

    def test_staff_can_view_order_operations_dashboard(self):
        self.client.login(username='opsstaff', password='secret123')

        response = self.client.get(reverse('orders:order_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Order Queue Dashboard')
        self.assertContains(response, 'Pending Orders')
        self.assertContains(response, 'Cancelled Orders')
        self.assertContains(response, 'Delivered Orders')
        self.assertContains(response, self.order.order_code)
        self.assertContains(response, self.delivered_order.order_code)
        self.assertContains(response, self.cancelled_order.order_code)
        content = response.content.decode()
        self.assertLess(content.index(self.cancelled_order.order_code), content.index(self.delivered_order.order_code))

    def test_staff_can_view_delivered_orders_dashboard(self):
        self.client.login(username='opsstaff', password='secret123')

        response = self.client.get(reverse('orders:delivered_orders_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delivered Orders')
        self.assertContains(response, self.delivered_order.delivery_date.strftime('%B %d, %Y'))
        self.assertContains(response, self.delivered_order.order_code)
        self.assertNotContains(response, self.order.order_code)

    def test_view_order_link_keeps_dashboard_as_back_destination(self):
        self.client.login(username='opsstaff', password='secret123')

        dashboard_response = self.client.get(reverse('orders:order_dashboard') + '?status=pending&q=opsbuyer')

        self.assertContains(
            dashboard_response,
            f'{reverse("orders:order_detail", args=[self.order.id])}?next=/orders/manage/%3Fstatus%3Dpending%26q%3Dopsbuyer',
            html=False,
        )

        detail_response = self.client.get(
            reverse('orders:order_detail', args=[self.order.id]) + '?next=/orders/manage/%3Fstatus%3Dpending%26q%3Dopsbuyer'
        )

        self.assertContains(detail_response, 'href="/orders/manage/?status=pending&amp;q=opsbuyer"', html=False)

    def test_staff_can_update_order_status_and_courier(self):
        self.client.login(username='opsstaff', password='secret123')

        response = self.client.post(
            reverse('orders:update_order_status', args=[self.order.id]),
            data={
                'status': 'shipped',
                'assigned_courier': 'Rider One',
                'internal_note': 'Packed and dispatched.',
            },
        )

        self.assertRedirects(response, reverse('orders:order_dashboard'))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'shipped')
        self.assertEqual(self.order.assigned_courier, 'Rider One')
        self.assertEqual(self.order.internal_note, 'Packed and dispatched.')

    def test_active_queue_orders_are_sorted_by_priority_high_to_low(self):
        medium_order = Order.objects.create(
            user=self.customer,
            total_price='120.00',
            fulfillment_method='delivery',
            payment_method='COD',
            delivery_date=timezone.localdate() + timedelta(days=2),
            status='pending',
        )
        low_order = Order.objects.create(
            user=self.customer,
            total_price='110.00',
            fulfillment_method='pickup',
            payment_method='COD',
            delivery_date=timezone.localdate() + timedelta(days=5),
            status='shipped',
        )

        self.client.login(username='opsstaff', password='secret123')
        response = self.client.get(reverse('orders:order_dashboard'))

        self.assertEqual(response.status_code, 200)
        pending_group = next(
            group for group in response.context['grouped_orders'] if group['key'] == 'pending'
        )
        pending_codes = [order.order_code for order in pending_group['orders']]
        self.assertEqual(pending_codes[:2], [self.order.order_code, medium_order.order_code])

        content = response.content.decode()
        self.assertLess(content.index(self.order.order_code), content.index(medium_order.order_code))
        self.assertLess(content.index(medium_order.order_code), content.index(low_order.order_code))
