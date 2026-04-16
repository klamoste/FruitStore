from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import DatabaseError
from django.db.models import Count, DecimalField, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.shortcuts import render
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from orders_app.models import Order, OrderItem
from products_app.models import Product
from accounts_app.models import Profile


def check_staff(user):
    """Check if user is staff or admin."""
    return user.is_staff or user.is_superuser


@login_required(login_url='accounts:login')
@user_passes_test(check_staff)
def dashboard(request):
    """Admin dashboard with sales analytics."""
    try:
        total_orders = Order.objects.count()
        total_revenue = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
        total_items_sold = OrderItem.objects.aggregate(Sum('quantity'))['quantity__sum'] or 0

        today = timezone.now().date()
        last_7_days = today - timedelta(days=7)
        daily_revenue = list(
            Order.objects.filter(created_at__date__gte=last_7_days)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(revenue=Sum('total_price'))
            .order_by('day')
        )
        
        low_stock_products = Product.objects.filter(
            stock_quantity__lt=10,
            is_available=True
        ).order_by('stock_quantity')[:10]

        best_sellers = list(
            OrderItem.objects.select_related('product')
            .values('product', 'product__name')
            .annotate(total_sold=Sum('quantity'))
            .order_by('-total_sold')[:10]
        )

        recent_orders = (
            Order.objects.select_related('user')
            .order_by('-created_at')[:10]
        )

        pending_orders = Order.objects.filter(status='pending').count()
        paid_orders = Order.objects.filter(status='paid').count()
        shipped_orders = Order.objects.filter(status='shipped').count()
        delivered_orders = Order.objects.filter(status='delivered').count()
        total_products = Product.objects.count()
        total_users = User.objects.count()

        profile_map = {
            profile.user_id: profile
            for profile in Profile.objects.select_related('user')
        }
        users = []
        for account in User.objects.annotate(
            order_count=Count('order', distinct=True),
            total_spent=Coalesce(
                Sum('order__total_price'),
                Value(0),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            ),
        ).order_by('username'):
            profile = profile_map.get(account.id)
            users.append({
                'username': account.username,
                'full_name': f'{account.first_name} {account.last_name}'.strip() or '-',
                'email': account.email or '-',
                'role': profile.get_role_display() if profile else 'No profile',
                'contact_number': profile.contact_number if profile and profile.contact_number else '-',
                'address': profile.address if profile and profile.address else '-',
                'city': profile.city if profile and profile.city else '',
                'state': profile.state if profile and profile.state else '',
                'order_count': account.order_count,
                'total_spent': account.total_spent,
                'is_staff': account.is_staff,
                'is_superuser': account.is_superuser,
                'date_joined': account.date_joined,
                'last_login': account.last_login,
            })
    except DatabaseError:
        messages.error(
            request,
            'Dashboard data is temporarily unavailable while the production database is being configured.'
        )
        total_orders = 0
        total_revenue = 0
        total_items_sold = 0
        daily_revenue = []
        low_stock_products = []
        best_sellers = []
        recent_orders = []
        pending_orders = 0
        paid_orders = 0
        shipped_orders = 0
        delivered_orders = 0
        total_products = 0
        total_users = 0
        users = []

    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_items_sold': total_items_sold,
        'total_products': total_products,
        'total_users': total_users,
        'daily_revenue': daily_revenue,
        'low_stock_products': low_stock_products,
        'best_sellers': best_sellers,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'paid_orders': paid_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'users': users,
    }

    return render(request, 'dashboard/dashboard.html', context)
