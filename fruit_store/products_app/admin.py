from django.contrib import admin

from admin_utils import DatabaseSafeAdminMixin
from .models import Category, Product, InventoryLog


@admin.register(Category)
class CategoryAdmin(DatabaseSafeAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(Product)
class ProductAdmin(DatabaseSafeAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock_quantity', 'display_unit', 'is_available']
    list_filter = ['category', 'is_available']
    search_fields = ['name', 'description']
    exclude = ['size', 'small_price', 'medium_price', 'large_price']

    @admin.display(description='Unit')
    def display_unit(self, obj):
        return obj.unit_label


@admin.register(InventoryLog)
class InventoryLogAdmin(DatabaseSafeAdminMixin, admin.ModelAdmin):
    list_display = ['product', 'change', 'reason', 'timestamp']
    list_filter = ['reason', 'timestamp']
