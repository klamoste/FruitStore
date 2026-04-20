from django.conf import settings
from django.contrib import messages
from django.db import DatabaseError
from django.template.response import TemplateResponse


class DatabaseSafeAdminMixin:
    @property
    def admin_error_message(self):
        if settings.VERCEL_ENV and not settings.DATABASE_URL_CONFIGURED:
            return (
                'The admin dashboard is temporarily unavailable because Vercel does not '
                'have a production database configured. Set DATABASE_URL to a hosted '
                'PostgreSQL database and redeploy.'
            )
        return (
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
