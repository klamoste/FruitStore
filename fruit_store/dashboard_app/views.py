from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from orders_app.models import Order, OrderItem
from products_app.models import Product, InventoryLog


def check_staff(user):
    """Check if user is staff or admin."""
    return user.is_staff or user.is_superuser


@login_required(login_url='accounts:login')
@user_passes_test(check_staff)
def dashboard(request):
    """Admin dashboard with sales analytics."""
    
    # Total sales
    total_orders = Order.objects.count()
    total_revenue = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_items_sold = OrderItem.objects.aggregate(Sum('quantity'))['quantity__sum'] or 0
    
    # Daily revenue (last 7 days)
    today = timezone.now().date()
    last_7_days = today - timedelta(days=7)
    daily_revenue = Order.objects.filter(
        created_at__date__gte=last_7_days
    ).extra(
        select={'day': 'DATE(created_at)'}
    ).values('day').annotate(revenue=Sum('total_price')).order_by('day')
    
    # Low stock products (less than 10 items)
    low_stock_products = Product.objects.filter(
        stock_quantity__lt=10,
        is_available=True
    ).order_by('stock_quantity')[:10]
    
    # Best selling products
    best_sellers = OrderItem.objects.values('product').annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:10]
    
    best_sellers_data = []
    for item in best_sellers:
        product = Product.objects.get(id=item['product'])
        best_sellers_data.append({
            'product': product,
            'total_sold': item['total_sold']
        })
    
    # Order status breakdown
    pending_orders = Order.objects.filter(status='pending').count()
    paid_orders = Order.objects.filter(status='paid').count()
    shipped_orders = Order.objects.filter(status='shipped').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    
    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_items_sold': total_items_sold,
        'total_products': Product.objects.count(),
        'total_users': User.objects.count(),
        'daily_revenue': list(daily_revenue),
        'low_stock_products': low_stock_products,
        'best_sellers': best_sellers_data,
        'pending_orders': pending_orders,
        'paid_orders': paid_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
    }
    
    return render(request, 'dashboard/dashboard.html', context)
