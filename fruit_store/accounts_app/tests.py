from django.contrib.auth.models import User
from django.test import TestCase

from .models import Profile


class ProfileTests(TestCase):
    def test_profile_can_be_created_with_model_defaults(self):
        user = User.objects.create_user(username='profile-user', password='secret123')

        profile, created = Profile.objects.get_or_create(user=user, defaults={'role': 'customer'})

        self.assertTrue(created)
        self.assertEqual(profile.avatar_mode, 'template')
        self.assertEqual(profile.avatar_template, 'leaf')
        self.assertFalse(profile.profile_image)
