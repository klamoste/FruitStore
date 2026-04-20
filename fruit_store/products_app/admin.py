from django.contrib import admin, messages
from django.db import DatabaseError
from django.template.response import TemplateResponse

from .models import Category, Product, InventoryLog


class DatabaseSafeAdminMixin:
    admin_error_message = (
        'The admin dashboard is temporarily unavailable because the live database '
        'cannot be reached in this environment.'
    )

    def render_database_unavailable(self, request):
        self.message_user(request, self.admin_error_message, level=messages.WARNING)
        context = {
            **self.admin_site.each_context(request),
            'title': 'Database unavailable',
            'subtitle': None,
            'opts': self.model._meta,
            'has_permission': True,
            'is_popup': False,
            'message': self.admin_error_message,
        }
        return TemplateResponse(request, 'admin/database_unavailable.html', context, status=503)

    def changelist_view(self, request, extra_context=None):
        try:
            return super().changelist_view(request, extra_context=extra_context)
        except DatabaseError:
            return self.render_database_unavailable(request)

    def add_view(self, request, form_url='', extra_context=None):
        try:
            return super().add_view(request, form_url=form_url, extra_context=extra_context)
        except DatabaseError:
            return self.render_database_unavailable(request)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        try:
            return super().change_view(request, object_id, form_url=form_url, extra_context=extra_context)
        except DatabaseError:
            return self.render_database_unavailable(request)

    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super().delete_view(request, object_id, extra_context=extra_context)
        except DatabaseError:
            return self.render_database_unavailable(request)

    def history_view(self, request, object_id, extra_context=None):
        try:
            return super().history_view(request, object_id, extra_context=extra_context)
        except DatabaseError:
            return self.render_database_unavailable(request)


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
