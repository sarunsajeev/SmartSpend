from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from transactions.models import Category

User = get_user_model()


class AccountFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='maya',
            email='maya@example.com',
            password='Original-Lantern-48!River',
            first_name='Maya',
            last_name='Rao',
        )

    def test_registration_creates_user_categories_and_signs_user_in(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'username': 'arjun',
                'email': 'arjun@example.com',
                'first_name': 'Arjun',
                'last_name': 'Sen',
                'password1': 'Velvet-Planet-76!Maple',
                'password2': 'Velvet-Planet-76!Maple',
            },
        )

        self.assertRedirects(response, reverse('dashboard:home'))
        user = User.objects.get(username='arjun')
        self.assertTrue(user.check_password('Velvet-Planet-76!Maple'))
        self.assertNotEqual(user.password, 'Velvet-Planet-76!Maple')
        self.assertIn('_auth_user_id', self.client.session)
        self.assertTrue(Category.objects.filter(user=user, kind=Category.Kind.EXPENSE, name='Food').exists())
        self.assertTrue(Category.objects.filter(user=user, kind=Category.Kind.INCOME, name='Salary').exists())
        self.assertTrue(Category.objects.filter(user=user, kind=Category.Kind.INVESTMENT, name='Investments').exists())

    def test_registration_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'username': 'newuser',
                'email': 'new@example.com',
                'first_name': 'New',
                'last_name': '',
                'password1': 'Velvet-Planet-76!Maple',
                'password2': 'Different-Planet-76!Maple',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())
        self.assertContains(response, 'The two password fields didn’t match')

    def test_login_and_logout_use_django_session(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'maya', 'password': 'Original-Lantern-48!River'},
        )
        self.assertRedirects(response, reverse('dashboard:home'))
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('accounts:logout'), follow=True)
        self.assertRedirects(response, reverse('accounts:login'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertContains(response, 'You have signed out safely.')

    def test_invalid_login_shows_an_error(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'maya', 'password': 'wrong-password'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'We could not sign you in')

    def test_profile_edit_updates_only_the_signed_in_user(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('accounts:profile')).status_code, 200)
        response = self.client.post(
            reverse('accounts:profile_edit'),
            {'first_name': 'Maya Devi', 'last_name': 'Rao', 'email': 'maya.new@example.com'},
        )

        self.assertRedirects(response, reverse('accounts:profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Maya Devi')
        self.assertEqual(self.user.email, 'maya.new@example.com')

    def test_password_change_validates_and_keeps_session(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('accounts:password_change'),
            {
                'old_password': 'Original-Lantern-48!River',
                'new_password1': 'New-Copper-Harbor-64!Pine',
                'new_password2': 'New-Copper-Harbor-64!Pine',
            },
        )

        self.assertRedirects(response, reverse('accounts:profile'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('New-Copper-Harbor-64!Pine'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_financial_pages_require_authentication(self):
        private_urls = [
            reverse('dashboard:home'),
            reverse('transactions:list'),
            reverse('transactions:categories'),
            reverse('subscriptions:list'),
            reverse('budgets:goals'),
            reverse('accounts:profile'),
        ]
        for url in private_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('accounts:login'), response.url)
