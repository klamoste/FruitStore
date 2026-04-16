from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import DatabaseError, transaction
from .models import Order, OrderItem
from .forms import CheckoutForm, PaymentForm
from products_app.models import Product, InventoryLog
from accounts_app.models import Profile
from decimal import Decimal

SHIPPING_FEE = Decimal('50.00')


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
        for product_id, item in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                quantity = item['quantity']
                subtotal = Decimal(item['price']) * quantity
                total_price += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'price': Decimal(item['price']),
                    'subtotal': subtotal,
                    'product_id': product_id,
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
    
    context = {
        'cart_items': cart_items,
        'subtotal_price': total_price,
        'shipping_fee': SHIPPING_FEE,
        'final_total': (total_price + SHIPPING_FEE).quantize(Decimal('0.01')),
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
        
        if action == 'remove':
            if product_id_str in cart:
                del cart[product_id_str]
                messages.success(request, 'Item removed from cart.')
        elif action == 'update':
            if quantity:
                quantity = int(quantity)
                if quantity <= 0:
                    if product_id_str in cart:
                        del cart[product_id_str]
                        messages.success(request, 'Item removed from cart.')
                else:
                    try:
                        product = get_object_or_404(Product, id=product_id)
                        if quantity > product.stock_quantity:
                            messages.error(request, f'Only {product.stock_quantity} items available.')
                        else:
                            cart[product_id_str]['quantity'] = quantity
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
        for product_id, item in cart.items():
            product = Product.objects.get(id=product_id)
            quantity = item['quantity']
            subtotal = Decimal(item['price']) * quantity
            total_price += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
            })
    except (DatabaseError, Product.DoesNotExist):
        messages.error(
            request,
            'Checkout is temporarily unavailable while the database is being configured.'
        )
        return redirect('orders:cart')
    
    final_total = (total_price + SHIPPING_FEE).quantize(Decimal('0.01'))

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            customer_note = form.cleaned_data['customer_note']
            
            # Create order
            try:
                order = Order.objects.create(
                    user=request.user,
                    customer_note=customer_note,
                    total_price=final_total,
                    status='paid' if payment_method == 'PAID' else 'pending'
                )
                
                for item in cart_items:
                    product = item['product']
                    quantity = item['quantity']
                    subtotal = item['subtotal']
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        subtotal=subtotal
                    )
                    
                    product.stock_quantity -= quantity
                    product.save()
                    
                    InventoryLog.objects.create(
                        product=product,
                        change=-quantity,
                        reason='sale'
                    )
            except DatabaseError:
                messages.error(
                    request,
                    'We could not place your order because the database is temporarily unavailable.'
                )
            else:
                request.session['cart'] = {}
                request.session.modified = True
                
                return redirect('orders:order_detail', order_id=order.id)
    else:
        form = PaymentForm()
    
    context = {
        'form': form,
        'subtotal_price': total_price,
        'shipping_fee': SHIPPING_FEE,
        'final_total': final_total,
        'cart_items': cart_items,
        'item_count': sum(item['quantity'] for item in cart_items),
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
        order = get_object_or_404(Order, id=order_id, user=request.user)
        items = OrderItem.objects.filter(order=order)
        subtotal_price = sum((item.subtotal for item in items), Decimal('0.00'))
    except DatabaseError:
        messages.error(
            request,
            'This order is temporarily unavailable while the database is being configured.'
        )
        return redirect('orders:order_history')
    
    context = {
        'order': order,
        'items': items,
        'subtotal_price': subtotal_price,
        'shipping_fee': SHIPPING_FEE,
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
