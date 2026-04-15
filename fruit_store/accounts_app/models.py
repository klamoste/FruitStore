from django.db import models

from django.contrib.auth.models import User


class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('customer', 'Customer'),
    ]
    AVATAR_MODE_CHOICES = [
        ('template', 'Template'),
        ('upload', 'Uploaded Photo'),
    ]
    AVATAR_TEMPLATE_CHOICES = [
        ('leaf', 'Leaf'),
        ('basket', 'Basket'),
        ('sun', 'Sun'),
        ('berry', 'Berry'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    address = models.CharField(max_length=255, blank=True)
    contact_number = models.CharField(max_length=30, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    avatar_mode = models.CharField(max_length=10, choices=AVATAR_MODE_CHOICES, default='template')
    avatar_template = models.CharField(max_length=20, choices=AVATAR_TEMPLATE_CHOICES, default='leaf')
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


