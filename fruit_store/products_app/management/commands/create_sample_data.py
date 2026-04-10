from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from products_app.models import Category, Product
from accounts_app.models import Profile
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create sample data for the Fruit Store'

    def handle(self, *args, **options):
        # Create categories
        categories_data = [
            {'name': 'Fresh Fruits', 'description': 'Freshly picked fruits'},
            {'name': 'Imported Fruits', 'description': 'Imported fruits from around the world'},
            {'name': 'Seasonal Fruits', 'description': 'Seasonal fruits available now'},
            {'name': 'Cut Fruits', 'description': 'Pre-cut and packaged fruits'},
            {'name': 'Beverages', 'description': 'Fruit juices and beverages'},
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories[cat_data['name']] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {cat.name}'))

        # Create products
        products_data = [
            {
                'name': 'Fresh Apples',
                'description': 'Crispy and juicy red apples from local orchards',
                'category': 'Fresh Fruits',
                'price': Decimal('4.99'),
                'stock_quantity': 100,
                'unit': 'kg',
            },
            {
                'name': 'Organic Bananas',
                'description': 'Sweet and organic bananas, perfect for breakfast',
                'category': 'Fresh Fruits',
                'price': Decimal('2.99'),
                'stock_quantity': 150,
                'unit': 'bundle',
            },
            {
                'name': 'Imported Mangoes',
                'description': 'Juicy sweet mangoes imported from India',
                'category': 'Imported Fruits',
                'price': Decimal('6.99'),
                'stock_quantity': 50,
                'unit': 'piece',
            },
            {
                'name': 'Fresh Strawberries',
                'description': 'Red, fresh strawberries perfect for smoothies',
                'category': 'Fresh Fruits',
                'price': Decimal('5.99'),
                'stock_quantity': 80,
                'unit': 'kg',
            },
            {
                'name': 'Cut Watermelon',
                'description': 'Fresh cut watermelon, ready to eat',
                'category': 'Cut Fruits',
                'price': Decimal('7.99'),
                'stock_quantity': 40,
                'unit': 'piece',
            },
            {
                'name': 'Orange Juice',
                'description': '100% fresh squeezed orange juice',
                'category': 'Beverages',
                'price': Decimal('3.99'),
                'stock_quantity': 200,
                'unit': 'piece',
            },
            {
                'name': 'Grapes',
                'description': 'Sweet green grapes, perfect for snacking',
                'category': 'Fresh Fruits',
                'price': Decimal('5.49'),
                'stock_quantity': 120,
                'unit': 'kg',
            },
            {
                'name': 'Lemons',
                'description': 'Acidic and fresh lemons for cooking',
                'category': 'Fresh Fruits',
                'price': Decimal('2.49'),
                'stock_quantity': 200,
                'unit': 'kg',
            },
        ]

        for prod_data in products_data:
            category = categories[prod_data['category']]
            product, created = Product.objects.get_or_create(
                name=prod_data['name'],
                defaults={
                    'description': prod_data['description'],
                    'category': category,
                    'price': prod_data['price'],
                    'stock_quantity': prod_data['stock_quantity'],
                    'unit': prod_data['unit'],
                    'is_available': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created product: {product.name}'))

        # Create test users
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@fruitstore.com',
                password='admin123'
            )
            Profile.objects.create(user=admin_user, role='admin')
            self.stdout.write(self.style.SUCCESS('Created admin user: admin / admin123'))

        if not User.objects.filter(username='testuser').exists():
            test_user = User.objects.create_user(
                username='testuser',
                email='test@fruitstore.com',
                password='testuser123'
            )
            Profile.objects.create(user=test_user, role='customer')
            self.stdout.write(self.style.SUCCESS('Created test user: testuser / testuser123'))

        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
