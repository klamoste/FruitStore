import re
from decimal import Decimal
from types import SimpleNamespace

from django.core.management import call_command
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


FALLBACK_CATALOG = [
    {
        'id': 1,
        'name': 'Fresh Apples',
        'description': 'Crispy and juicy red apples from local orchards.',
        'category': 'Fresh Fruits',
        'price': Decimal('4.99'),
        'stock_quantity': 100,
        'unit_label': 'Kilogram',
    },
    {
        'id': 2,
        'name': 'Organic Bananas',
        'description': 'Sweet and organic bananas, perfect for breakfast.',
        'category': 'Fresh Fruits',
        'price': Decimal('2.99'),
        'stock_quantity': 150,
        'unit_label': 'Bundle',
    },
    {
        'id': 3,
        'name': 'Imported Mangoes',
        'description': 'Juicy sweet mangoes imported from India.',
        'category': 'Imported Fruits',
        'price': Decimal('6.99'),
        'stock_quantity': 50,
        'unit_label': 'Piece',
    },
    {
        'id': 4,
        'name': 'Fresh Strawberries',
        'description': 'Red, fresh strawberries perfect for smoothies.',
        'category': 'Fresh Fruits',
        'price': Decimal('5.99'),
        'stock_quantity': 80,
        'unit_label': 'Kilogram',
    },
    {
        'id': 5,
        'name': 'Cut Watermelon',
        'description': 'Fresh cut watermelon, ready to eat.',
        'category': 'Cut Fruits',
        'price': Decimal('7.99'),
        'stock_quantity': 40,
        'unit_label': 'Piece',
    },
    {
        'id': 6,
        'name': 'Orange Juice',
        'description': '100% fresh squeezed orange juice.',
        'category': 'Beverages',
        'price': Decimal('3.99'),
        'stock_quantity': 200,
        'unit_label': 'Cup',
    },
    {
        'id': 7,
        'name': 'Grapes',
        'description': 'Sweet green grapes, perfect for snacking.',
        'category': 'Fresh Fruits',
        'price': Decimal('5.49'),
        'stock_quantity': 120,
        'unit_label': 'Kilogram',
    },
    {
        'id': 8,
        'name': 'Lemons',
        'description': 'Acidic and fresh lemons for cooking.',
        'category': 'Fresh Fruits',
        'price': Decimal('2.49'),
        'stock_quantity': 200,
        'unit_label': 'Kilogram',
    },
]


def build_fallback_products():
    products = []
    for item in FALLBACK_CATALOG:
        products.append(
            SimpleNamespace(
                id=item['id'],
                pk=item['id'],
                name=item['name'],
                description=item['description'],
                category=SimpleNamespace(name=item['category']),
                price=item['price'],
                stock_quantity=item['stock_quantity'],
                unit_label=item['unit_label'],
                available_cup_sizes=[],
                image=None,
                is_available=True,
                is_fallback=True,
            )
        )
    return products


def build_fallback_categories():
    category_names = []
    for item in FALLBACK_CATALOG:
        if item['category'] not in category_names:
            category_names.append(item['category'])

    if 'Beverages' in category_names and 'Fresh Fruits' in category_names:
        beverages_index = category_names.index('Beverages')
        fresh_fruits_index = category_names.index('Fresh Fruits')
        category_names[beverages_index], category_names[fresh_fruits_index] = (
            category_names[fresh_fruits_index],
            category_names[beverages_index],
        )

    return [
        SimpleNamespace(id=index, name=name)
        for index, name in enumerate(category_names, start=1)
    ]


def get_fallback_product(product_id):
    return next((product for product in build_fallback_products() if product.id == product_id), None)


def ensure_sample_catalog():
    """Seed demo data when the deployed catalog is empty."""
    if not Product.objects.exists():
        call_command('create_sample_data', verbosity=0)


def home(request):
    """Display home page with hero section and featured products."""
    catalog_readonly = False
    try:
        ensure_sample_catalog()
        featured_products = Product.objects.filter(is_available=True).order_by('-created_at')[:8]
    except DatabaseError:
        featured_products = build_fallback_products()[:8]
        catalog_readonly = True
    
    context = {
        'featured_products': featured_products,
        'catalog_readonly': catalog_readonly,
    }
    return render(request, 'index.html', context)


def product_list(request):
    """Display all products with search and filter functionality."""
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    catalog_unavailable = False
    catalog_readonly = False

    try:
        ensure_sample_catalog()
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
        catalog_readonly = True
        products = build_fallback_products()
        categories = build_fallback_categories()

        if query:
            description_word_match = re.compile(rf'(^|\W){re.escape(query)}(\W|$)', re.IGNORECASE)
            products = [
                product for product in products
                if query.lower() in product.name.lower()
                or description_word_match.search(product.description)
            ]

        if category_id:
            selected_category = next(
                (category for category in categories if str(category.id) == category_id),
                None,
            )
            if selected_category:
                products = [
                    product for product in products
                    if product.category.name == selected_category.name
                ]

        paginator = Paginator(products, 12)
        page = request.GET.get('page', 1)
        products = paginator.get_page(page)
        products.object_list = list(products.object_list)
    
    context = {
        'products': products,
        'categories': categories,
        'query': query,
        'category_id': category_id,
        'catalog_unavailable': catalog_unavailable,
        'catalog_readonly': catalog_readonly,
    }
    return render(request, 'products/product_list.html', context)


def product_detail(request, pk):
    """Display a single product details."""
    try:
        product = get_object_or_404(Product, pk=pk)
        catalog_readonly = False
    except DatabaseError:
        product = get_fallback_product(pk)
        catalog_readonly = product is not None
        if product is None:
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
        'catalog_readonly': catalog_readonly,
    }
    return render(request, 'products/product_detail.html', context)


@login_required(login_url='accounts:login')
def add_to_cart(request, pk):
    """Add product to shopping cart (stored in session)."""
    try:
        product = get_object_or_404(Product, pk=pk)
    except DatabaseError:
        if get_fallback_product(pk):
            messages.error(
                request,
                'Shopping is temporarily in preview mode while the live database is unavailable.'
            )
            return redirect('products:product_detail', pk=pk)
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
        results = [
            {
                'id': product.id,
                'name': product.name,
                'price': str(product.price),
            }
            for product in build_fallback_products()
            if query.lower() in product.name.lower()
        ][:5]

    return JsonResponse(results, safe=False)
