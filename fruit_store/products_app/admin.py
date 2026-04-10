from django.contrib import admin

from .models import Category, Product, InventoryLog


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock_quantity', 'unit', 'is_available']
    list_filter = ['category', 'is_available']
    search_fields = ['name', 'description']


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ['product', 'change', 'reason', 'timestamp']
    list_filter = ['reason', 'timestamp']