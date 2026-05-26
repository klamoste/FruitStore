from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import DatabaseError, transaction
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .models import DeliveryZone, Order, OrderItem
from .forms import CheckoutForm, OrderStatusUpdateForm, PaymentForm
from products_app.models import Product, InventoryLog
from accounts_app.models import Profile
from decimal import Decimal
import logging

SHIPPING_FEE = Decimal('50.00')
logger = logging.getLogger(__name__)

NEARBY_DELIVERY_CITIES = {
    'quezon city',
    'manila',
    'san juan',
    'mandaluyong',
    'marikina',
    'pasig',
}
METRO_DELIVERY_CITIES = {
    'makati',
    'taguig',
    'pasay',
    'paranaque',
    'parañaque',
    'las pinas',
    'las piñas',
    'muntinlupa',
    'caloocan',
    'malabon',
    'navotas',
    'valenzuela',
    'pateros',
}
GREATER_DELIVERY_CITIES = {
    'antipolo',
    'cainta',
    'taytay',
    'san mateo',
    'rodriguez',
    'bacoor',
    'imus',
    'dasmarinas',
    'dasmariñas',
    'san pedro',
    'binan',
    'biñan',
}
DEFAULT_DELIVERY_FEE = Decimal('180.00')
DEFAULT_ETA_LABEL = '2 to 4 days'


def normalize_location(value):
    return ' '.join((value or '').strip().lower().split())


def can_manage_orders(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return Profile.objects.filter(user=user, role__in=['admin', 'staff']).exists()


def get_order_detail_back_url(request):
    next_url = request.GET.get('next', '').strip()
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    if can_manage_orders(request.user):
        return reverse('orders:order_dashboard')
    return reverse('orders:order_history')


def format_eta_label(min_days, max_days):
    if min_days == max_days:
        return 'Same day' if min_days == 0 else f'{min_days} day' if min_days == 1 else f'{min_days} days'
    if min_days == 0:
        return f'Same day to {max_days} days'
    return f'{min_days} to {max_days} days'


def get_matching_delivery_zone(user):
    try:
        profile, _ = Profile.objects.get_or_create(user=user, defaults={'role': 'customer'})
    except DatabaseError:
        return None, None

    normalized_city = normalize_location(profile.city)
    normalized_state = normalize_location(profile.state)
    location_name = profile.city.strip() or profile.state.strip() or 'your area'

    try:
        zones = DeliveryZone.objects.filter(active=True)
        for zone in zones:
            if zone.city and normalize_location(zone.city) == normalized_city:
                return zone, location_name
            if zone.state and not zone.city and normalize_location(zone.state) == normalized_state:
                return zone, location_name
    except DatabaseError:
        return None, location_name

    return None, location_name


def get_shipping_details(user, fulfillment_method='delivery'):
    if fulfillment_method == 'pickup':
        return {
            'fee': Decimal('0.00'),
            'zone_name': 'Pickup',
            'location_name': 'Store pickup',
            'eta_label': 'Ready for pickup on your selected date',
        }

    zone, location_name = get_matching_delivery_zone(user)
    if zone is not None:
        return {
            'fee': zone.fee,
            'zone_name': zone.name,
            'location_name': location_name,
            'eta_label': format_eta_label(zone.estimated_min_days, zone.estimated_max_days),
        }

    try:
        profile, _ = Profile.objects.get_or_create(user=user, defaults={'role': 'customer'})
        normalized_city = normalize_location(profile.city)
        normalized_state = normalize_location(profile.state)
        location_name = profile.city.strip() or profile.state.strip() or 'your area'
    except DatabaseError:
        return {
            'fee': SHIPPING_FEE,
            'zone_name': 'Standard',
            'location_name': 'your area',
            'eta_label': DEFAULT_ETA_LABEL,
        }

    if normalized_city in NEARBY_DELIVERY_CITIES:
        return {
            'fee': SHIPPING_FEE,
            'zone_name': 'Nearby Zone',
            'location_name': location_name,
            'eta_label': 'Same day to 1 day',
        }
    if normalized_city in METRO_DELIVERY_CITIES:
        return {
            'fee': Decimal('80.00'),
            'zone_name': 'Metro Zone',
            'location_name': location_name,
            'eta_label': '1 to 2 days',
        }
    if normalized_city in GREATER_DELIVERY_CITIES:
        return {
            'fee': Decimal('120.00'),
            'zone_name': 'Extended Zone',
            'location_name': location_name,
            'eta_label': '2 to 3 days',
        }
    if normalized_state == 'metro manila':
        return {
            'fee': Decimal('80.00'),
            'zone_name': 'Metro Zone',
            'location_name': location_name,
            'eta_label': '1 to 2 days',
        }
    return {
        'fee': DEFAULT_DELIVERY_FEE,
        'zone_name': 'Provincial Zone',
        'location_name': location_name,
        'eta_label': DEFAULT_ETA_LABEL,
    }


def get_shipping_fee(user, fulfillment_method):
    return get_shipping_details(user, fulfillment_method)['fee']


def send_order_confirmation_notifications(request, order):
    order_url = request.build_absolute_uri(reverse('orders:order_detail', args=[order.id]))
    customer_recipients = [order.user.email] if order.user.email else []
    store_recipient = getattr(settings, 'STORE_NOTIFICATION_EMAIL', '').strip()
    store_recipients = [store_recipient] if store_recipient else []
    subject = f'Order confirmation: {order.order_code}'
    lines = [
        f'Order code: {order.order_code}',
        f'Customer: {order.user.get_full_name() or order.user.username}',
        f'Total: PHP {order.total_price}',
        f'Payment: {order.get_payment_method_display()}',
        f'Fulfillment: {order.get_fulfillment_method_display()}',
        f'Status: {order.get_status_display()}',
        f'Order details: {order_url}',
    ]
    if order.delivery_date:
        lines.append(f'Delivery date: {order.delivery_date}')
    if order.delivery_window:
        lines.append(f'Delivery window: {order.get_delivery_window_display()}')
    message = '\n'.join(lines)

    if customer_recipients:
        send_mail(
            subject,
            f'Thank you for your order.\n\n{message}',
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@fruitstore.local'),
            customer_recipients,
            fail_silently=True,
        )
    if store_recipients:
        send_mail(
            subject,
            f'A new order was placed.\n\n{message}',
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@fruitstore.local'),
            store_recipients,
            fail_silently=True,
        )


def get_cart_labels(product, item):
    selected_size = item.get('selected_size', '')
    if selected_size and product.unit == 'cup':
        selected_label = f'{selected_size.title()} Cup'
        return selected_size, selected_label, 'Cup'
    return selected_size, '', item.get('unit_label') or product.unit_label


def get_missing_profile_fields(user):
    try:
        profile, _ = Profile.objects.get_or_create(user=user, defaults={'role': 'customer'})
    except DatabaseError:
        return ['profile']

    checks = [
        ('first name', user.first_name),
        ('last name', user.last_name),
        ('email', user.email),
        ('address', profile.address),
        ('contact number', profile.contact_number),
        ('city', profile.city),
    ]
    return [label for label, value in checks if not (value and str(value).strip())]


def has_complete_profile(user):
    return not get_missing_profile_fields(user)


@login_required(login_url='accounts:login')
def view_cart(request):
    """Display shopping cart from session."""
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = Decimal('0.00')
    
    try:
        for cart_key, item in cart.items():
            try:
                product_id = item.get('product_id') or cart_key.split(':', 1)[0]
                product = Product.objects.get(id=product_id)
                quantity = item['quantity']
                subtotal = Decimal(item['price']) * quantity
                selected_size, selected_label, unit_label = get_cart_labels(product, item)
                total_price += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'price': Decimal(item['price']),
                    'subtotal': subtotal,
                    'product_id': product_id,
                    'cart_key': cart_key,
                    'selected_size': selected_size,
                    'selected_label': selected_label,
                    'unit_label': unit_label,
                    'cup_size_options': product.available_cup_sizes,
                })
            except Product.DoesNotExist:
                continue
    except DatabaseError:
        messages.error(
            request,
            'Your cart is temporarily unavailable while the database is being configured.'
        )
        cart_items = []
        total_price = Decimal('0.00')
    
    delivery_shipping = get_shipping_details(request.user, 'delivery')
    context = {
        'cart_items': cart_items,
        'subtotal_price': total_price,
        'shipping_fee': delivery_shipping['fee'],
        'shipping_zone_name': delivery_shipping['zone_name'],
        'shipping_location_name': delivery_shipping['location_name'],
        'shipping_eta_label': delivery_shipping['eta_label'],
        'final_total': (total_price + delivery_shipping['fee']).quantize(Decimal('0.01')),
        'item_count': sum(item['quantity'] for item in cart_items),
        'profile_complete': has_complete_profile(request.user),
    }
    return render(request, 'orders/cart.html', context)


@login_required(login_url='accounts:login')
def update_cart(request, product_id):
    """Update cart item quantity or remove."""
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    
    if request.method == 'POST':
        quantity = request.POST.get('quantity')
        action = request.POST.get('action')
        cart_key = request.POST.get('cart_key') or product_id_str
        
        if action == 'remove':
            if cart_key in cart:
                del cart[cart_key]
                messages.success(request, 'Item removed from cart.')
        elif action == 'change_size':
            selected_size = request.POST.get('selected_size', '')
            quantity = request.POST.get('quantity')
            if cart_key in cart:
                try:
                    product = get_object_or_404(Product, id=product_id)
                    selected_option = next(
                        (option for option in product.available_cup_sizes if option['value'] == selected_size),
                        None,
                    )
                    if not selected_option:
                        messages.error(request, 'Please choose a valid cup size.')
                    else:
                        current_item = cart[cart_key]
                        new_quantity = current_item['quantity']
                        if quantity:
                            new_quantity = max(1, int(quantity))
                        if new_quantity > product.stock_quantity:
                            messages.error(request, f'Only {product.stock_quantity} items available.')
                            request.session['cart'] = cart
                            return redirect('orders:cart')
                        new_cart_key = f'{product_id_str}:{selected_size}'
                        if new_cart_key != cart_key and new_cart_key in cart:
                            cart[new_cart_key]['quantity'] += new_quantity
                            del cart[cart_key]
                        else:
                            cart[new_cart_key] = {
                                **current_item,
                                'product_id': product_id_str,
                                'selected_size': selected_size,
                                'quantity': new_quantity,
                                'price': str(selected_option['price']),
                                'unit_label': selected_option['unit_label'],
                            }
                            if new_cart_key != cart_key:
                                del cart[cart_key]
                        messages.success(request, 'Cup size updated.')
                except DatabaseError:
                    messages.error(
                        request,
                        'Cart updates are temporarily unavailable while the database is being configured.'
                    )
        elif action == 'update':
            if quantity:
                quantity = int(quantity)
                if quantity <= 0:
                    if cart_key in cart:
                        del cart[cart_key]
                        messages.success(request, 'Item removed from cart.')
                else:
                    try:
                        product = get_object_or_404(Product, id=product_id)
                        if quantity > product.stock_quantity:
                            messages.error(request, f'Only {product.stock_quantity} items available.')
                        else:
                            cart[cart_key]['quantity'] = quantity
                            messages.success(request, 'Cart updated.')
                    except DatabaseError:
                        messages.error(
                            request,
                            'Cart updates are temporarily unavailable while the database is being configured.'
                        )
    
    request.session['cart'] = cart
    return redirect('orders:cart')


@login_required(login_url='accounts:login')
def checkout(request):
    """Checkout form to create order."""
    cart = request.session.get('cart', {})

    if not cart:
        messages.error(request, 'Your cart is empty.')
        return redirect('products:product_list')

    if not has_complete_profile(request.user):
        missing_fields = get_missing_profile_fields(request.user)
        messages.warning(
            request,
            'Please complete your profile before placing an order. Missing: '
            + ', '.join(missing_fields) + '.'
        )
        return redirect('accounts:profile')

    # Calculate total and prepare cart items
    total_price = Decimal('0.00')
    cart_items = []
    try:
        for cart_key, item in cart.items():
            product_id = item.get('product_id') or cart_key.split(':', 1)[0]
            product = Product.objects.get(id=product_id)
            quantity = item['quantity']
            subtotal = Decimal(item['price']) * quantity
            selected_size, selected_label, unit_label = get_cart_labels(product, item)
            total_price += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'unit_price': Decimal(item['price']),
                'selected_size': selected_size,
                'selected_label': selected_label,
                'unit_label': unit_label,
                'subtotal': subtotal,
            })
    except (DatabaseError, Product.DoesNotExist):
        messages.error(
            request,
            'Checkout is temporarily unavailable while the database is being configured.'
        )
        return redirect('orders:cart')
    
    selected_fulfillment = 'delivery'
    shipping_details = get_shipping_details(request.user, selected_fulfillment)
    shipping_fee = shipping_details['fee']
    final_total = (total_price + shipping_fee).quantize(Decimal('0.01'))

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            fulfillment_method = form.cleaned_data['fulfillment_method']
            payment_method = form.cleaned_data['payment_method']
            delivery_date = form.cleaned_data['delivery_date']
            delivery_window = form.cleaned_data['delivery_window']
            gcash_sender_name = form.cleaned_data['gcash_sender_name']
            gcash_reference_number = form.cleaned_data['gcash_reference_number']
            customer_note = form.cleaned_data['customer_note']
            shipping_details = get_shipping_details(request.user, fulfillment_method)
            shipping_fee = shipping_details['fee']
            final_total = (total_price + shipping_fee).quantize(Decimal('0.01'))
            
            # Create order
            try:
                with transaction.atomic():
                    order = Order.objects.create(
                        user=request.user,
                        fulfillment_method=fulfillment_method,
                        payment_method=payment_method,
                        delivery_date=delivery_date,
                        delivery_window=delivery_window,
                        gcash_sender_name=gcash_sender_name,
                        gcash_reference_number=gcash_reference_number,
                        customer_note=customer_note,
                        total_price=final_total,
                        status='pending'
                    )

                    for item in cart_items:
                        product = Product.objects.select_for_update().get(id=item['product'].id)
                        quantity = item['quantity']
                        subtotal = item['subtotal']

                        if quantity > product.stock_quantity:
                            raise ValueError(
                                f'Only {product.stock_quantity} items available for {product.name}.'
                            )

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            product_name=product.name,
                            product_category_name=product.category.name,
                            product_unit=product.unit,
                            quantity=quantity,
                            unit_price=item['unit_price'],
                            selected_size=item['selected_size'],
                            selected_unit_label=item['selected_label'],
                            subtotal=subtotal
                        )

                        product.stock_quantity -= quantity
                        product.save(update_fields=['stock_quantity', 'updated_at'])

                        InventoryLog.objects.create(
                            product=product,
                            change=-quantity,
                            reason='sale'
                        )
            except ValueError as exc:
                messages.error(request, str(exc))
            except DatabaseError:
                logger.exception(
                    'Checkout failed for user %s while writing order data.',
                    request.user.pk,
                )
                messages.error(
                    request,
                    'We could not place your order because the database is temporarily unavailable.'
                )
            else:
                send_order_confirmation_notifications(request, order)
                request.session['cart'] = {}
                request.session.modified = True
                
                return redirect('orders:order_detail', order_id=order.id)
        else:
            selected_fulfillment = request.POST.get('fulfillment_method') or 'delivery'
            shipping_details = get_shipping_details(request.user, selected_fulfillment)
            shipping_fee = shipping_details['fee']
            final_total = (total_price + shipping_fee).quantize(Decimal('0.01'))
    else:
        form = PaymentForm()
    
    context = {
        'form': form,
        'subtotal_price': total_price,
        'shipping_fee': shipping_fee,
        'delivery_shipping_fee': get_shipping_details(request.user, 'delivery')['fee'],
        'delivery_zone_name': get_shipping_details(request.user, 'delivery')['zone_name'],
        'delivery_location_name': get_shipping_details(request.user, 'delivery')['location_name'],
        'delivery_eta_label': get_shipping_details(request.user, 'delivery')['eta_label'],
        'shipping_zone_name': shipping_details['zone_name'],
        'shipping_location_name': shipping_details['location_name'],
        'shipping_eta_label': shipping_details['eta_label'],
        'final_total': final_total,
        'cart_items': cart_items,
        'item_count': sum(item['quantity'] for item in cart_items),
        'gcash_name': getattr(settings, 'STORE_GCASH_NAME', '').strip(),
        'gcash_number': getattr(settings, 'STORE_GCASH_NUMBER', '').strip(),
    }
    return render(request, 'orders/checkout.html', context)


@login_required(login_url='accounts:login')
def order_history(request):
    """Display user's order history."""
    try:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
    except DatabaseError:
        messages.error(
            request,
            'Your order history is temporarily unavailable while the database is being configured.'
        )
        orders = Order.objects.none()
    
    paginator = Paginator(orders, 10)
    page = request.GET.get('page', 1)
    orders = paginator.get_page(page)
    
    context = {'orders': orders}
    return render(request, 'orders/order_history.html', context)


@login_required(login_url='accounts:login')
def order_detail(request, order_id):
    """Display single order details."""
    try:
        order_lookup = {'id': order_id}
        if not can_manage_orders(request.user):
            order_lookup['user'] = request.user

        order = get_object_or_404(Order, **order_lookup)
        items = OrderItem.objects.filter(order=order)
        for item in items:
            item.display_name = item.display_product_name
            item.display_category = item.display_category_name
            if item.selected_size and item.product_unit == 'cup':
                item.display_unit_label = 'Cup'
                item.display_selected_label = item.selected_unit_label or f'{item.selected_size.title()} Cup'
            else:
                item.display_unit_label = item.selected_unit_label or item.display_unit_name
                item.display_selected_label = item.selected_unit_label
        subtotal_price = sum((item.subtotal for item in items), Decimal('0.00'))
        shipping_fee = max(order.total_price - subtotal_price, Decimal('0.00'))
        shipping_details = get_shipping_details(request.user if order.user_id == request.user.id else order.user, order.fulfillment_method)
    except DatabaseError:
        messages.error(
            request,
            'This order is temporarily unavailable while the database is being configured.'
        )
        return redirect('orders:order_history')
    
    context = {
        'order': order,
        'items': items,
        'back_url': get_order_detail_back_url(request),
        'subtotal_price': subtotal_price,
        'shipping_fee': shipping_fee,
        'shipping_zone_name': shipping_details['zone_name'],
        'shipping_location_name': shipping_details['location_name'],
        'shipping_eta_label': shipping_details['eta_label'],
    }
    return render(request, 'orders/order_detail.html', context)


@login_required(login_url='accounts:login')
@transaction.atomic
def cancel_order(request, order_id):
    if request.method != 'POST':
        return redirect('orders:order_detail', order_id=order_id)

    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if not order.can_cancel:
            messages.error(request, 'This order can no longer be cancelled.')
            return redirect('orders:order_detail', order_id=order.id)

        for item in OrderItem.objects.select_related('product').filter(order=order):
            product = item.product
            if product is None:
                continue
            product.stock_quantity += item.quantity
            product.save(update_fields=['stock_quantity'])
            InventoryLog.objects.create(
                product=product,
                change=item.quantity,
                reason='restock'
            )

        order.status = 'cancelled'
        order.save(update_fields=['status', 'updated_at'])
    except DatabaseError:
        messages.error(
            request,
            'Order cancellation is temporarily unavailable while the database is being configured.'
        )
        return redirect('orders:order_history')

    messages.success(request, f'Order {order.order_code} has been cancelled.')
    return redirect('orders:order_detail', order_id=order.id)


@login_required(login_url='accounts:login')
@user_passes_test(can_manage_orders)
def order_operations_dashboard(request):
    return _render_order_dashboard(request, delivered_only=False)


@login_required(login_url='accounts:login')
@user_passes_test(can_manage_orders)
def delivered_orders_dashboard(request):
    return _render_order_dashboard(request, delivered_only=True)


def _render_order_dashboard(request, delivered_only=False):
    status_filter = request.GET.get('status', '').strip()
    fulfillment_filter = request.GET.get('fulfillment', '').strip()
    query = request.GET.get('q', '').strip()

    try:
        orders = Order.objects.select_related('user').annotate(
            item_count=Count('orderitem'),
        )
        if delivered_only:
            orders = orders.filter(status='delivered')
        if status_filter:
            orders = orders.filter(status=status_filter)
        if fulfillment_filter:
            orders = orders.filter(fulfillment_method=fulfillment_filter)
        if query:
            orders = orders.filter(
                Q(order_code__icontains=query)
                | Q(user__username__icontains=query)
                | Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
                | Q(assigned_courier__icontains=query)
            )
        if delivered_only:
            orders = list(orders.order_by('-delivery_date', '-updated_at', '-created_at')[:50])
        else:
            orders = list(orders.order_by('delivery_date', '-created_at')[:50])
        for order in orders:
            order.priority_badge = 'High' if order.queue_priority >= 60 else 'Medium' if order.queue_priority >= 30 else 'Low'
            order.show_status_form = (not delivered_only) and order.status != 'delivered'
        if not delivered_only:
            orders.sort(
                key=lambda order: (
                    -order.queue_priority,
                    order.delivery_date is None,
                    order.delivery_date or timezone.localdate(),
                    -order.created_at.timestamp(),
                )
            )
    except DatabaseError:
        messages.error(request, 'The staff dashboard is temporarily unavailable while the database is being configured.')
        orders = []

    grouped_orders = []
    if delivered_only:
        delivered_buckets = []
        bucket_map = {}
        for order in orders:
            if order.delivery_date:
                bucket_key = order.delivery_date.isoformat()
                bucket_title = order.delivery_date.strftime('%B %d, %Y')
            else:
                bucket_key = 'unscheduled'
                bucket_title = 'No delivery date'

            if bucket_key not in bucket_map:
                bucket_map[bucket_key] = {
                    'title': bucket_title,
                    'count': 0,
                    'orders': [],
                }
                delivered_buckets.append(bucket_map[bucket_key])

            bucket_map[bucket_key]['orders'].append(order)
            bucket_map[bucket_key]['count'] += 1
        grouped_orders = delivered_buckets
    else:
        status_order = ['pending', 'paid', 'shipped', 'cancelled', 'delivered']
        status_labels = dict(Order.STATUS_CHOICES)
        active_buckets = []
        bucket_map = {}
        for status in status_order:
            label = status_labels.get(status, status.title())
            bucket = {
                'key': status,
                'title': f'{label} Orders',
                'count': 0,
                'orders': [],
            }
            bucket_map[status] = bucket
            active_buckets.append(bucket)

        for order in orders:
            bucket = bucket_map.get(order.status)
            if bucket is None:
                bucket = {
                    'key': order.status,
                    'title': f'{order.get_status_display()} Orders',
                    'count': 0,
                    'orders': [],
                }
                bucket_map[order.status] = bucket
                active_buckets.append(bucket)
            bucket['orders'].append(order)
            bucket['count'] += 1

        grouped_orders = [bucket for bucket in active_buckets if bucket['orders']]

    context = {
        'orders': orders,
        'grouped_orders': grouped_orders,
        'dashboard_title': 'Delivered Orders' if delivered_only else 'Order Queue Dashboard',
        'dashboard_intro': (
            'Review completed deliveries separately from active work so the current queue stays easier to manage.'
            if delivered_only
            else 'Review incoming orders, prioritize urgent deliveries, assign couriers, and move orders through the pipeline.'
        ),
        'dashboard_badge': 'Delivered Archive' if delivered_only else 'Staff Operations',
        'owner_link_label': 'Active Order Queue' if delivered_only else 'Delivered Orders',
        'owner_link_href': reverse('orders:order_dashboard') if delivered_only else reverse('orders:delivered_orders_dashboard'),
        'empty_title': 'No delivered orders yet' if delivered_only else 'No matching orders',
        'empty_copy': (
            'Delivered orders will appear here once they are completed.'
            if delivered_only
            else 'Try clearing the filters or wait for new orders to arrive.'
        ),
        'show_priority': not delivered_only,
        'show_status_form': not delivered_only,
        'status_filter': status_filter,
        'fulfillment_filter': fulfillment_filter,
        'query': query,
        'status_choices': Order.STATUS_CHOICES,
        'fulfillment_choices': Order.FULFILLMENT_METHOD_CHOICES,
        'status_form': OrderStatusUpdateForm(),
    }
    return render(request, 'orders/order_dashboard.html', context)


@login_required(login_url='accounts:login')
@user_passes_test(can_manage_orders)
@transaction.atomic
def update_order_status(request, order_id):
    if request.method != 'POST':
        return redirect('orders:order_dashboard')

    order = get_object_or_404(Order, id=order_id)
    form = OrderStatusUpdateForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Please review the order update form and try again.')
        return redirect('orders:order_dashboard')

    try:
        order.status = form.cleaned_data['status']
        order.assigned_courier = form.cleaned_data['assigned_courier'].strip()
        order.internal_note = form.cleaned_data['internal_note'].strip()
        order.save(update_fields=['status', 'assigned_courier', 'internal_note', 'updated_at'])
    except DatabaseError:
        messages.error(request, 'We could not update that order right now.')
        return redirect('orders:order_dashboard')

    messages.success(request, f'Updated {order.order_code} to {order.get_status_display()}.')
    return redirect('orders:order_dashboard')
