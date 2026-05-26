from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Profile


class CustomerNavbarTests(TestCase):
    def test_customer_sees_store_links_in_navbar(self):
        user = User.objects.create_user(username='shopper', password='secret123')
        Profile.objects.create(user=user, role='customer')

        self.client.login(username='shopper', password='secret123')
        response = self.client.get(reverse('products:home'))

        self.assertContains(response, '>Home</a>', html=False)
        self.assertContains(response, '>Cart</a>', html=False)
        self.assertContains(response, '>Orders</a>', html=False)
        self.assertNotContains(response, 'Manage Orders')
        self.assertNotContains(response, 'Manage Products')

    def test_admin_does_not_see_customer_store_links_in_navbar(self):
        user = User.objects.create_user(
            username='adminuser',
            password='secret123',
            is_staff=True,
        )
        Profile.objects.create(user=user, role='admin')

        self.client.login(username='adminuser', password='secret123')
        response = self.client.get(reverse('products:home'))

        self.assertNotContains(response, '>Home</a>', html=False)
        self.assertNotContains(response, '>Cart</a>', html=False)
        self.assertNotContains(response, '>Orders</a>', html=False)
        self.assertContains(response, 'Manage Orders')
