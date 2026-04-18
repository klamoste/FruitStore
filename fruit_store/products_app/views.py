import re

import re

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

HIDDEN_CATEGORY_NAMES = [
    'Beverages',
    'Cut Fruits',
    'Imported Fruits',
    'Seasonal Fruits',
]


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
        categories = Category.objects.exclude(name__in=HIDDEN_CATEGORY_NAMES).order_by('name')
        
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
    
    context = {
        'product': product,
        'form': form,
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
