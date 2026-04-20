from django.contrib import admin

from admin_utils import DatabaseSafeAdminMixin
from .models import Order, OrderItem


@admin.register(Order)
class OrderAdmin(DatabaseSafeAdminMixin, admin.ModelAdmin):
    list_display = ['order_code', 'user', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_code', 'user__username', 'user__email']


@admin.register(OrderItem)
class OrderItemAdmin(DatabaseSafeAdminMixin, admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'subtotal']
