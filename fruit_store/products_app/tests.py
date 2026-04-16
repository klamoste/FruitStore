from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class ProductViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name='Fresh Fruits', description='Fresh picks')
        Product.objects.create(
            name='Apple',
            description='Crisp and sweet',
            category=category,
            price='10.50',
            stock_quantity=12,
            unit='kg',
            is_available=True,
        )
        cls.user = User.objects.create_user(username='buyer', password='secret123')

    def test_product_list_renders_products(self):
        response = self.client.get(reverse('products:product_list'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Apple')

    def test_product_list_handles_database_error(self):
        with patch('products_app.views.Product.objects.filter', side_effect=DatabaseError('boom')):
            response = self.client.get(reverse('products:product_list'), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'temporarily unavailable')

    def test_add_to_cart_requires_login(self):
        product = Product.objects.get(name='Apple')

        response = self.client.post(
            reverse('products:add_to_cart', args=[product.id]),
            {'quantity': 1},
            secure=True,
        )

        self.assertEqual(response.status_code, 302)
