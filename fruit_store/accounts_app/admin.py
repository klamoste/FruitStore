from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db import DatabaseError
from django.template.response import TemplateResponse

from .models import Profile


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


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    fk_name = 'user'


class CustomUserAdmin(DatabaseSafeAdminMixin, UserAdmin):
    inlines = [ProfileInline]
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_superuser',
        'date_joined',
        'last_login',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(Profile)
class ProfileAdmin(DatabaseSafeAdminMixin, admin.ModelAdmin):
    list_display = ('user', 'role', 'contact_number', 'city', 'state')
    list_filter = ('role', 'city', 'state')
    search_fields = (
        'user__username',
        'user__email',
        'contact_number',
        'city',
        'state',
    )


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
