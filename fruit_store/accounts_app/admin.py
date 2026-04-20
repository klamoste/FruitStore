from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from admin_utils import DatabaseSafeAdminMixin
from .models import Profile


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
