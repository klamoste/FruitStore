from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import DatabaseError
from django.db.models import CharField, Count, DecimalField, Max, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from orders_app.models import Order, OrderItem
from products_app.models import Product
from accounts_app.models import Profile
from products_app.models import Category
from products_app.forms import ProductForm
from .forms import CustomerCreationForm


def check_admin(user):
    """Allow only admin accounts to access the owner dashboard."""
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return Profile.objects.filter(user=user, role='admin').exists()


@login_required(login_url='accounts:login')
@user_passes_test(check_admin)
def dashboard(request):
    """Admin dashboard with sales analytics."""
    try:
        today = timezone.now().date()
        last_7_days = today - timedelta(days=6)
        active_orders = Order.objects.exclude(status='cancelled')
        delivered_orders_qs = Order.objects.filter(status='delivered')

        total_orders = Order.objects.count()
        total_revenue = active_orders.aggregate(
            total=Coalesce(
                Sum('total_price'),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )['total']
        total_items_sold = OrderItem.objects.filter(order__status__in=['paid', 'shipped', 'delivered']).aggregate(
            total=Coalesce(Sum('quantity'), Value(0))
        )['total']
        avg_order_value = round((total_revenue / total_orders), 2) if total_orders else 0

        raw_daily_revenue = list(
            delivered_orders_qs.filter(updated_at__date__gte=last_7_days)
            .annotate(day=TruncDate('updated_at'))
            .values('day')
            .annotate(
                revenue=Coalesce(
                    Sum('total_price'),
                    Value(0),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
            .order_by('day')
        )
        revenue_lookup = {entry['day']: float(entry['revenue']) for entry in raw_daily_revenue}
        peak_revenue = max(revenue_lookup.values(), default=0)
        daily_revenue = []
        for day_offset in range(7):
            day = last_7_days + timedelta(days=day_offset)
            revenue = revenue_lookup.get(day, 0)
            daily_revenue.append({
                'day': day,
                'label': day.strftime('%a'),
                'revenue': revenue,
                'height': max(10, round((revenue / peak_revenue) * 100)) if peak_revenue else 10,
            })
        chart_points = []
        total_points = len(daily_revenue)
        for index, entry in enumerate(daily_revenue):
            x_position = 50 if total_points == 1 else round((index / (total_points - 1)) * 100, 2)
            y_position = round(100 - entry['height'], 2)
            entry['x_position'] = x_position
            entry['y_position'] = y_position
            chart_points.append(f'{x_position},{y_position}')
        revenue_chart_path = ' '.join(chart_points)
        revenue_chart_area = f"0,100 {revenue_chart_path} 100,100" if chart_points else ''

        low_stock_products = Product.objects.filter(
            stock_quantity__lt=10,
            is_available=True
        ).order_by('stock_quantity')[:10]
        out_of_stock_count = Product.objects.filter(stock_quantity__lte=0).count()
        low_stock_count = Product.objects.filter(stock_quantity__gt=0, stock_quantity__lt=10).count()

        best_sellers = list(
            OrderItem.objects.annotate(
                best_seller_name=Coalesce('product_name', 'product__name', Value('Deleted product'), output_field=CharField()),
            )
            .values('best_seller_name')
            .annotate(
                total_sold=Coalesce(Sum('quantity'), Value(0)),
                revenue=Coalesce(
                    Sum('subtotal'),
                    Value(0),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
            )
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
        cancelled_orders = Order.objects.filter(status='cancelled').count()
        total_products = Product.objects.count()
        total_users = User.objects.count()
        active_customers = User.objects.filter(order__isnull=False).distinct().count()
        new_users_30_days = User.objects.filter(date_joined__date__gte=today - timedelta(days=29)).count()
        delivered_today = delivered_orders_qs.filter(updated_at__date=today).count()
        orders_today = Order.objects.filter(created_at__date=today).count()
        revenue_today = active_orders.filter(created_at__date=today).aggregate(
            total=Coalesce(
                Sum('total_price'),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )['total']
        latest_order_at = Order.objects.aggregate(last=Max('created_at'))['last']

        payment_breakdown = [
            {
                'label': method_label,
                'count': Order.objects.filter(payment_method=method_key).count(),
            }
            for method_key, method_label in Order.PAYMENT_METHOD_CHOICES
        ]
        fulfillment_breakdown = [
            {
                'label': method_label,
                'count': Order.objects.filter(fulfillment_method=method_key).count(),
            }
            for method_key, method_label in Order.FULFILLMENT_METHOD_CHOICES
        ]
        status_cards = [
            {'label': 'Pending', 'count': pending_orders, 'tone': 'amber'},
            {'label': 'Paid', 'count': paid_orders, 'tone': 'blue'},
            {'label': 'Shipped', 'count': shipped_orders, 'tone': 'slate'},
            {'label': 'Delivered', 'count': delivered_orders, 'tone': 'green'},
            {'label': 'Cancelled', 'count': cancelled_orders, 'tone': 'red'},
        ]

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
        top_customers = sorted(
            [user for user in users if user['order_count'] > 0],
            key=lambda user: (-user['total_spent'], -user['order_count'], user['username'].lower()),
        )[:6]
    except DatabaseError:
        messages.error(
            request,
            'Dashboard data is temporarily unavailable because the database connection failed.'
        )
        total_orders = 0
        total_revenue = 0
        total_items_sold = 0
        daily_revenue = []
        revenue_chart_path = ''
        revenue_chart_area = ''
        low_stock_products = []
        best_sellers = []
        recent_orders = []
        pending_orders = 0
        paid_orders = 0
        shipped_orders = 0
        delivered_orders = 0
        cancelled_orders = 0
        total_products = 0
        total_users = 0
        avg_order_value = 0
        out_of_stock_count = 0
        low_stock_count = 0
        active_customers = 0
        new_users_30_days = 0
        delivered_today = 0
        orders_today = 0
        revenue_today = 0
        latest_order_at = None
        payment_breakdown = []
        fulfillment_breakdown = []
        status_cards = []
        users = []
        top_customers = []

    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_items_sold': total_items_sold,
        'avg_order_value': avg_order_value,
        'total_products': total_products,
        'total_users': total_users,
        'daily_revenue': daily_revenue,
        'revenue_chart_path': revenue_chart_path,
        'revenue_chart_area': revenue_chart_area,
        'low_stock_products': low_stock_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'best_sellers': best_sellers,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'paid_orders': paid_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'active_customers': active_customers,
        'new_users_30_days': new_users_30_days,
        'delivered_today': delivered_today,
        'orders_today': orders_today,
        'revenue_today': revenue_today,
        'latest_order_at': latest_order_at,
        'payment_breakdown': payment_breakdown,
        'fulfillment_breakdown': fulfillment_breakdown,
        'status_cards': status_cards,
        'top_customers': top_customers,
        'users': users,
    }

    return render(request, 'dashboard/dashboard.html', context)


def _render_management_page(request, title, eyebrow, intro, quick_links, spotlight_cards):
    return render(
        request,
        'dashboard/tool_page.html',
        {
            'page_title': title,
            'eyebrow': eyebrow,
            'intro': intro,
            'quick_links': quick_links,
            'spotlight_cards': spotlight_cards,
        },
    )


@login_required(login_url='accounts:login')
@user_passes_test(check_admin)
def admin_tool_page(request):
    spotlight_cards = [
        {
            'title': 'Site Administration',
            'value': 'Full Control',
            'copy': 'Open the standard Django admin to manage every registered model and system setting.',
        },
        {
            'title': 'Owner Dashboard',
            'value': 'Live Metrics',
            'copy': 'Jump back to the main dashboard for sales, inventory, and customer performance signals.',
        },
    ]
    quick_links = [
        {'label': 'Open Django Admin', 'href': '/admin/', 'primary': True},
        {'label': 'Open Owner Dashboard', 'href': '/dashboard/'},
        {'label': 'Manage Orders', 'href': '/orders/manage/'},
    ]
    return _render_management_page(
        request,
        'Admin Access',
        'Admin Control',
        'Use this page as the branded entry point before opening the deeper admin tools underneath.',
        quick_links,
        spotlight_cards,
    )


@login_required(login_url='accounts:login')
@user_passes_test(check_admin)
def products_tool_page(request):
    edit_id = request.GET.get('edit')
    product_to_edit = None
    form = ProductForm()

    try:
        if edit_id:
            product_to_edit = get_object_or_404(Product, pk=edit_id)

        if request.method == 'POST':
            toggle_product_id = request.POST.get('toggle_product_id')
            if toggle_product_id:
                product_to_toggle = get_object_or_404(Product, pk=toggle_product_id)
                product_to_toggle.is_available = not product_to_toggle.is_available
                product_to_toggle.save(update_fields=['is_available', 'updated_at'])
                messages.success(
                    request,
                    f"{product_to_toggle.name} is now {'visible in the storefront' if product_to_toggle.is_available else 'hidden from the storefront'}.",
                )
                return redirect('dashboard:products_tool_page')

            delete_product_id = request.POST.get('delete_product_id')
            if delete_product_id:
                product_to_delete = get_object_or_404(Product, pk=delete_product_id)
                product_name = product_to_delete.name
                product_to_delete.delete()
                messages.success(request, f'{product_name} was deleted successfully.')
                return redirect('dashboard:products_tool_page')

            submitted_product_id = request.POST.get('product_id')
            if submitted_product_id:
                product_to_edit = get_object_or_404(Product, pk=submitted_product_id)
                form = ProductForm(request.POST, request.FILES, instance=product_to_edit)
            else:
                form = ProductForm(request.POST, request.FILES)

            if form.is_valid():
                saved_product = form.save()
                messages.success(
                    request,
                    f'{saved_product.name} was {"updated" if submitted_product_id else "created"} successfully.'
                )
                return redirect('dashboard:products_tool_page')
        elif product_to_edit:
            form = ProductForm(instance=product_to_edit)

        products = list(Product.objects.select_related('category').order_by('-updated_at'))
        spotlight_cards = [
            {
                'title': 'Active Products',
                'value': Product.objects.filter(is_available=True).count(),
                'copy': 'Products currently visible to customers in the storefront.',
            },
            {
                'title': 'Low Stock',
                'value': Product.objects.filter(stock_quantity__lt=10).count(),
                'copy': 'Items that may need restocking soon.',
            },
            {
                'title': 'Categories',
                'value': Category.objects.count(),
                'copy': 'Catalog groupings available in the store.',
            },
        ]
    except DatabaseError:
        messages.error(request, 'Product management is temporarily unavailable because the database connection failed.')
        products = []
        spotlight_cards = [
            {'title': 'Active Products', 'value': 0, 'copy': 'Products currently visible to customers in the storefront.'},
            {'title': 'Low Stock', 'value': 0, 'copy': 'Items that may need restocking soon.'},
            {'title': 'Categories', 'value': 0, 'copy': 'Catalog groupings available in the store.'},
        ]
        form = ProductForm()
        product_to_edit = None

    management_links = [
        {'label': 'Manage Orders', 'href': '/orders/manage/', 'primary': True},
        {'label': 'View Storefront', 'href': '/products/'},
        {'label': 'Back to Dashboard', 'href': '/dashboard/'},
    ]
    return render(
        request,
        'dashboard/products_tool_page.html',
        {
            'page_title': 'Product Management',
            'eyebrow': 'Catalog Control',
            'intro': 'Review the current catalog and edit products from a branded owner page without dropping into plain admin.',
            'quick_links': [],
            'management_links': management_links,
            'spotlight_cards': spotlight_cards,
            'products': products,
            'form': form,
            'product_to_edit': product_to_edit,
        },
    )


@login_required(login_url='accounts:login')
@user_passes_test(check_admin)
def users_tool_page(request):
    if request.method == 'POST':
        remove_customer_id = request.POST.get('remove_customer_id')
        if remove_customer_id:
            customer = get_object_or_404(User.objects.select_related('profile'), pk=remove_customer_id)
            profile = getattr(customer, 'profile', None)
            if customer.is_superuser or customer.is_staff or not profile or profile.role != 'customer':
                messages.error(request, 'Only customer accounts can be removed from this page.')
                return redirect('dashboard:users_tool_page')

            order_count = customer.order_set.count()
            username = customer.username
            try:
                if order_count:
                    customer.is_active = False
                    customer.save(update_fields=['is_active'])
                    messages.warning(
                        request,
                        f"Customer account '{username}' has order history, so the account was deactivated instead of permanently deleted.",
                    )
                else:
                    customer.delete()
                    messages.success(request, f"Customer account '{username}' was deleted successfully.")
            except DatabaseError:
                messages.error(
                    request,
                    'Customer removal is temporarily unavailable because the database connection failed.',
                )
            return redirect('dashboard:users_tool_page')

    users = list(User.objects.select_related('profile').order_by('-date_joined')[:12])
    spotlight_cards = [
        {
            'title': 'Total Accounts',
            'value': User.objects.count(),
            'copy': 'All registered users across admin, staff, and customers.',
        },
        {
            'title': 'Customer Profiles',
            'value': Profile.objects.filter(role='customer').count(),
            'copy': 'Shopper accounts ready to browse, order, and track purchases.',
        },
        {
            'title': 'Staff + Admin',
            'value': Profile.objects.filter(role__in=['admin', 'staff']).count(),
            'copy': 'Internal accounts with elevated access to store operations.',
        },
    ]
    quick_links = [
        {'label': 'Back to Dashboard', 'href': '/dashboard/', 'primary': True},
    ]
    return render(
        request,
        'dashboard/users_tool_page.html',
        {
            'page_title': 'User Management',
            'eyebrow': 'Account Control',
            'intro': 'Review the latest accounts and open the next user action from a dedicated owner page.',
            'quick_links': quick_links,
            'spotlight_cards': spotlight_cards,
            'users': users,
        },
    )


@login_required(login_url='accounts:login')
@user_passes_test(check_admin)
def create_customer_tool_page(request):
    form = CustomerCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            form.save()
        except DatabaseError:
            messages.error(
                request,
                'Customer creation is temporarily unavailable because the database connection failed.',
            )
        else:
            messages.success(request, f"Customer account '{form.cleaned_data['username']}' created successfully.")
            return redirect('dashboard:create_customer_tool_page')

    spotlight_cards = [
        {
            'title': 'Customer Profiles',
            'value': Profile.objects.filter(role='customer').count(),
            'copy': 'Shopper accounts ready to browse, order, and track purchases.',
        },
        {
            'title': 'Total Accounts',
            'value': User.objects.count(),
            'copy': 'All registered users across admin, staff, and customers.',
        },
        {
            'title': 'Back Office',
            'value': 'Owner Tool',
            'copy': 'Create storefront customer accounts here without opening Django admin.',
        },
    ]
    quick_links = [
        {'label': 'Back to Users', 'href': '/dashboard/users-tools/', 'primary': True},
        {'label': 'Back to Dashboard', 'href': '/dashboard/'},
        {'label': 'View Storefront', 'href': '/products/'},
    ]
    return render(
        request,
        'dashboard/create_customer_tool_page.html',
        {
            'page_title': 'Create Customer',
            'eyebrow': 'Account Creation',
            'intro': 'Create a new customer account from the owner dashboard without dropping into Django admin.',
            'quick_links': quick_links,
            'spotlight_cards': spotlight_cards,
            'form': form,
        },
    )


@login_required(login_url='accounts:login')
@user_passes_test(check_admin)
def storefront_tool_page(request):
    featured_products = list(Product.objects.filter(is_available=True).order_by('-updated_at')[:6])
    spotlight_cards = [
        {
            'title': 'Visible Products',
            'value': Product.objects.filter(is_available=True).count(),
            'copy': 'Products currently live in the storefront experience.',
        },
        {
            'title': 'Fresh Preview',
            'value': 'Customer View',
            'copy': 'Use this page to launch the public shopping flow while staying in the management area first.',
        },
    ]
    quick_links = [
        {'label': 'Open Product Listing', 'href': '/products/', 'primary': True},
        {'label': 'Open Homepage', 'href': '/'},
        {'label': 'Back to Dashboard', 'href': '/dashboard/'},
    ]
    return render(
        request,
        'dashboard/storefront_tool_page.html',
        {
            'page_title': 'Storefront Preview',
            'eyebrow': 'Customer Experience',
            'intro': 'Preview the live store flow through a branded management page before opening the customer-facing screens.',
            'quick_links': quick_links,
            'spotlight_cards': spotlight_cards,
            'featured_products': featured_products,
        },
    )
