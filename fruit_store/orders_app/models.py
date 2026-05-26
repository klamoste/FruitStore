import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from products_app.models import Product


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('GCASH', 'GCash'),
    ]
    FULFILLMENT_METHOD_CHOICES = [
        ('delivery', 'Delivery'),
        ('pickup', 'Store Pickup'),
    ]
    DELIVERY_WINDOW_CHOICES = [
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_code = models.CharField(max_length=20, unique=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    fulfillment_method = models.CharField(
        max_length=20,
        choices=FULFILLMENT_METHOD_CHOICES,
        default='delivery',
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        default='COD',
    )
    delivery_date = models.DateField(null=True, blank=True)
    delivery_window = models.CharField(
        max_length=20,
        choices=DELIVERY_WINDOW_CHOICES,
        blank=True,
        default='',
    )
    gcash_sender_name = models.CharField(max_length=120, blank=True)
    gcash_reference_number = models.CharField(max_length=60, blank=True)
    customer_note = models.TextField(blank=True)
    assigned_courier = models.CharField(max_length=120, blank=True)
    internal_note = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_code:
            self.order_code = f"ORD-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    @property
    def can_cancel(self):
        cancellable_statuses = {'pending', 'paid'}
        return (
            self.status in cancellable_statuses
            and timezone.now() <= self.created_at + timedelta(hours=3)
        )

    @property
    def cancel_deadline(self):
        return self.created_at + timedelta(hours=3)

    def __str__(self):
        return f"Order {self.order_code} by {self.user.username}"

    @property
    def queue_priority(self):
        score = 0
        if self.status == 'pending':
            score += 40
        elif self.status == 'paid':
            score += 30
        elif self.status == 'shipped':
            score += 20

        if self.payment_method == 'GCASH':
            score += 10

        if self.delivery_date:
            days_until_delivery = (self.delivery_date - timezone.localdate()).days
            if days_until_delivery <= 0:
                score += 30
            elif days_until_delivery == 1:
                score += 20
            elif days_until_delivery == 2:
                score += 10

        return score


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200, blank=True, default='')
    product_category_name = models.CharField(max_length=100, blank=True, default='')
    product_unit = models.CharField(max_length=10, blank=True, default='')
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selected_size = models.CharField(max_length=10, blank=True, default='')
    selected_unit_label = models.CharField(max_length=40, blank=True, default='')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def display_product_name(self):
        return self.product_name or (self.product.name if self.product else 'Deleted product')

    @property
    def display_category_name(self):
        if self.product_category_name:
            return self.product_category_name
        if self.product and self.product.category_id:
            return self.product.category.name
        return 'Archived category'

    @property
    def display_unit_name(self):
        if self.product:
            return self.product.unit_label
        if self.product_unit == 'cup':
            return 'Cup'
        return dict(Product.UNIT_CHOICES).get(self.product_unit, self.product_unit.title() if self.product_unit else 'Unit')

    def __str__(self):
        return f"{self.display_product_name} x {self.quantity}"


class DeliveryZone(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_min_days = models.PositiveSmallIntegerField(default=1)
    estimated_max_days = models.PositiveSmallIntegerField(default=2)
    active = models.BooleanField(default=True)
    priority = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ['priority', 'name']

    def __str__(self):
        target = self.city or self.state or 'General'
        return f"{self.name} ({target})"
