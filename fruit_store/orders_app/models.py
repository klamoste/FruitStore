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
    DELIVERY_WINDOW_CHOICES = [
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_code = models.CharField(max_length=20, unique=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
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


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selected_size = models.CharField(max_length=10, blank=True, default='')
    selected_unit_label = models.CharField(max_length=40, blank=True, default='')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
