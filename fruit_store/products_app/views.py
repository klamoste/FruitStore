import re
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Q
from django.http import JsonResponse
from .models import Product, Category, InventoryLog
from .forms import ProductSearchForm, AddToCartForm
from orders_app.models import Order, OrderItem


def home(request):
    """Display home page with hero section and featured products."""
    try:
        featured_products = Product.objects.filter(is_available=True).order_by('-created_at')[:8]
    except DatabaseError:
        featured_products = []
        messages.warning(
            request,
            'Products are temporarily unavailable while the catalog database is being set up.'
        )
    
    context = {
        'featured_products': featured_products,
    }
    return render(request, 'index.html', context)


def product_list(request):
    """Display all products with search and filter functionality."""
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')

    try:
        products = Product.objects.filter(is_available=True).order_by('name')
        categories = list(Category.objects.order_by('name'))
        category_names = [category.name for category in categories]
        if 'Beverages' in category_names and 'Fresh Fruits' in category_names:
            beverages_index = category_names.index('Beverages')
            fresh_fruits_index = category_names.index('Fresh Fruits')
            categories[beverages_index], categories[fresh_fruits_index] = (
                categories[fresh_fruits_index],
                categories[beverages_index],
            )
        
        if query:
            description_word_match = rf'(^|\W){re.escape(query)}(\W|$)'
            products = products.filter(
                Q(name__icontains=query) |
                Q(description__iregex=description_word_match)
            )
        
        if category_id:
            products = products.filter(category_id=category_id)
        
        min_price = request.GET.get('min_price', '')
        max_price = request.GET.get('max_price', '')
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        
        paginator = Paginator(products, 12)
        page = request.GET.get('page', 1)
        products = paginator.get_page(page)
        products.object_list = list(products.object_list)
    except DatabaseError:
        products = []
        categories = []
        messages.error(
            request,
            'The product catalog is temporarily unavailable. Please try again after the database is configured.'
        )
    
    context = {
        'products': products,
        'categories': categories,
        'query': query,
        'category_id': category_id,
    }
    return render(request, 'products/product_list.html', context)


def product_detail(request, pk):
    """Display a single product details."""
    try:
        product = get_object_or_404(Product, pk=pk)
    except DatabaseError:
        messages.error(
            request,
            'This product is temporarily unavailable because the catalog database is not ready.'
        )
        return redirect('products:product_list')

    form = AddToCartForm()
    cup_size_options = product.available_cup_sizes
    default_cup_option = cup_size_options[0] if cup_size_options else None
    
    context = {
        'product': product,
        'form': form,
        'cup_size_options': cup_size_options,
        'default_cup_option': default_cup_option,
    }
    return render(request, 'products/product_detail.html', context)


@login_required(login_url='accounts:login')
def add_to_cart(request, pk):
    """Add product to shopping cart (stored in session)."""
    try:
        product = get_object_or_404(Product, pk=pk)
    except DatabaseError:
        messages.error(
            request,
            'Your cart is temporarily unavailable because the product database is not ready.'
        )
        return redirect('products:product_list')
    
    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            selected_size = ''
            unit_price = Decimal(product.price)
            unit_label = product.unit_label

            if product.available_cup_sizes:
                selected_size = request.POST.get('selected_size', '')
                selected_option = next(
                    (option for option in product.available_cup_sizes if option['value'] == selected_size),
                    None,
                )
                if not selected_option:
                    selected_option = product.available_cup_sizes[0]
                    selected_size = selected_option['value']
                unit_price = Decimal(selected_option['price'])
                unit_label = selected_option['unit_label']
            
            if quantity > product.stock_quantity:
                messages.error(request, f'Only {product.stock_quantity} items available in stock.')
                return redirect('products:product_detail', pk=pk)
            
            cart = request.session.get('cart', {})
            product_id = str(pk)
            cart_key = f'{product_id}:{selected_size or "default"}'
            
            if cart_key in cart:
                cart[cart_key]['quantity'] += quantity
            else:
                cart[cart_key] = {
                    'product_id': product_id,
                    'quantity': quantity,
                    'price': str(unit_price),
                    'selected_size': selected_size,
                    'unit_label': unit_label,
                }
            
            request.session['cart'] = cart
            messages.success(request, f'{product.name} added to cart!')
            return redirect('orders:cart')
    
    return redirect('products:product_detail', pk=pk)


def search_products(request):
    """AJAX search for products."""
    query = request.GET.get('q', '')
    try:
        products = Product.objects.filter(
            is_available=True,
            name__icontains=query
        ).order_by('name')[:5]

        results = [{
            'id': p.id,
            'name': p.name,
            'price': str(p.price),
        } for p in products]
    except DatabaseError:
        results = []

    return JsonResponse(results, safe=False)
