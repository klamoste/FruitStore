from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, Category, InventoryLog
from .forms import ProductSearchForm, AddToCartForm
from orders_app.models import Order, OrderItem


def home(request):
    """Display home page with hero section and featured products."""
    featured_products = Product.objects.filter(is_available=True)[:8]
    
    context = {
        'featured_products': featured_products,
    }
    return render(request, 'index.html', context)


def product_list(request):
    """Display all products with search and filter functionality."""
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()
    
    # Search
    query = request.GET.get('q', '')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
    
    # Filter by category
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Filter by price
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Pagination
    paginator = Paginator(products, 12)
    page = request.GET.get('page', 1)
    products = paginator.get_page(page)
    
    context = {
        'products': products,
        'categories': categories,
        'query': query,
        'category_id': category_id,
    }
    return render(request, 'products/product_list.html', context)


def product_detail(request, pk):
    """Display a single product details."""
    product = get_object_or_404(Product, pk=pk)
    form = AddToCartForm()
    
    context = {
        'product': product,
        'form': form,
    }
    return render(request, 'products/product_detail.html', context)


@login_required(login_url='accounts:login')
def add_to_cart(request, pk):
    """Add product to shopping cart (stored in session)."""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            
            if quantity > product.stock_quantity:
                messages.error(request, f'Only {product.stock_quantity} items available in stock.')
                return redirect('products:product_detail', pk=pk)
            
            cart = request.session.get('cart', {})
            product_id = str(pk)
            
            if product_id in cart:
                cart[product_id]['quantity'] += quantity
            else:
                cart[product_id] = {
                    'quantity': quantity,
                    'price': str(product.price)
                }
            
            request.session['cart'] = cart
            messages.success(request, f'{product.name} added to cart!')
            return redirect('orders:cart')
    
    return redirect('products:product_detail', pk=pk)


def search_products(request):
    """AJAX search for products."""
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        is_available=True,
        name__icontains=query
    )[:5]
    
    results = [{
        'id': p.id,
        'name': p.name,
        'price': str(p.price),
    } for p in products]
    
    import json
    return json.dumps(results)
