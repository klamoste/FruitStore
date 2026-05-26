from django.contrib import admin

from admin_utils import DatabaseSafeAdminMixin
from .models import DeliveryZone, Order, OrderItem


@admin.register(Order)
class OrderAdmin(DatabaseSafeAdminMixin, admin.ModelAdmin):
    list_display = [
        'order_code',
        'user',
        'fulfillment_method',
        'payment_method',
        'delivery_date',
        'delivery_window',
        'assigned_courier',
        'total_price',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'fulfillment_method', 'payment_method', 'delivery_window', 'created_at']
    search_fields = [
        'order_code',
        'user__username',
        'user__email',
        'gcash_sender_name',
        'gcash_reference_number',
        'assigned_courier',
    ]


@admin.register(OrderItem)
class OrderItemAdmin(DatabaseSafeAdminMixin, admin.ModelAdmin):
    list_display = ['order', 'product_label', 'quantity', 'subtotal']

    @admin.display(description='Product')
    def product_label(self, obj):
        return obj.display_product_name


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(DatabaseSafeAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'city', 'state', 'fee', 'estimated_min_days', 'estimated_max_days', 'active', 'priority']
    list_filter = ['active', 'state']
    search_fields = ['name', 'city', 'state']
