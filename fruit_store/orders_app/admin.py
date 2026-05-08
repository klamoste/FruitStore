from django.contrib import admin

from admin_utils import DatabaseSafeAdminMixin
from .models import Order, OrderItem


@admin.register(Order)
class OrderAdmin(DatabaseSafeAdminMixin, admin.ModelAdmin):
    list_display = [
        'order_code',
        'user',
        'payment_method',
        'delivery_date',
        'delivery_window',
        'total_price',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'payment_method', 'delivery_window', 'created_at']
    search_fields = [
        'order_code',
        'user__username',
        'user__email',
        'gcash_sender_name',
        'gcash_reference_number',
    ]


@admin.register(OrderItem)
class OrderItemAdmin(DatabaseSafeAdminMixin, admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'subtotal']
