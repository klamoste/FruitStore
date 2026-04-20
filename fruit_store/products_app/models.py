from django.db import models

from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('piece', 'Piece'),
        ('bundle', 'Bundle'),
        ('bottle', 'Bottle'),
        ('cup', 'Cup'),
        ('liter', 'Liter'),
    ]
    SIZE_CHOICES = [
        ('', 'No size'),
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    ]
    CUP_SIZE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField()
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, blank=True, default='')
    small_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    medium_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    large_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        self.size = ''
        self.small_price = None
        self.medium_price = None
        self.large_price = None

    @property
    def unit_label(self):
        if self.unit == 'cup':
            return 'Cup'
        return self.get_unit_display()

    @property
    def available_cup_sizes(self):
        return []

    def __str__(self):
        return self.name


class InventoryLog(models.Model):
    REASON_CHOICES = [
        ('sale', 'Sale'),
        ('restock', 'Restock'),
        ('spoilage', 'Spoilage'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    change = models.IntegerField()  # positive for restock, negative for sale/spoilage
    reason = models.CharField(max_length=10, choices=REASON_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.reason} - {self.change}"
