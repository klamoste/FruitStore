from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Order, OrderItem
from .forms import CheckoutForm, PaymentForm
from products_app.models import Product, InventoryLog
from decimal import Decimal


@login_required(login_url='accounts:login')
def view_cart(request):
    """Display shopping cart from session."""
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = Decimal('0.00')
    
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
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'final_total': total_price.quantize(Decimal('0.01')),
        'item_count': sum(item['quantity'] for item in cart_items),
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
                    product = get_object_or_404(Product, id=product_id)
                    if quantity > product.stock_quantity:
                        messages.error(request, f'Only {product.stock_quantity} items available.')
                    else:
                        cart[product_id_str]['quantity'] = quantity
                        messages.success(request, 'Cart updated.')
    
    request.session['cart'] = cart
    return redirect('orders:cart')


@login_required(login_url='accounts:login')
def checkout(request):
    """Checkout form to create order."""
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.error(request, 'Your cart is empty.')
        return redirect('products:product_list')
    
    # Calculate total and prepare cart items
    total_price = Decimal('0.00')
    cart_items = []
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
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            
            # Create order
            order = Order.objects.create(
                user=request.user,
                total_price=total_price,
                status='paid' if payment_method == 'PAID' else 'pending'
            )
            
            # Create order items and update inventory
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
                
                # Update stock
                product.stock_quantity -= quantity
                product.save()
                
                # Log inventory change
                InventoryLog.objects.create(
                    product=product,
                    change=-quantity,
                    reason='sale'
                )
            
            # Clear cart
            request.session['cart'] = {}
            request.session.modified = True
            
            messages.success(request, f'Order placed successfully! Order ID: {order.id}')
            return redirect('orders:order_detail', order_id=order.id)
    else:
        form = PaymentForm()
    
    final_total = total_price.quantize(Decimal('0.01'))
    
    context = {
        'form': form,
        'total_price': total_price,
        'final_total': final_total,
        'cart_items': cart_items,
        'item_count': sum(item['quantity'] for item in cart_items),
    }
    return render(request, 'orders/checkout.html', context)


@login_required(login_url='accounts:login')
def order_history(request):
    """Display user's order history."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    paginator = Paginator(orders, 10)
    page = request.GET.get('page', 1)
    orders = paginator.get_page(page)
    
    context = {'orders': orders}
    return render(request, 'orders/order_history.html', context)


@login_required(login_url='accounts:login')
def order_detail(request, order_id):
    """Display single order details."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = OrderItem.objects.filter(order=order)
    
    context = {
        'order': order,
        'items': items,
    }
    return render(request, 'orders/order_detail.html', context)
