from decimal import Decimal
from pathlib import Path

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from budgets.models import Goal
from subscriptions.models import Subscription
from transactions.models import Category, Transaction


User = get_user_model()


class WebsiteCoverageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='site-user', email='site@example.com', password='Strong-Site-42!River',
            first_name='Alex',
        )
        self.food = Category.objects.create(user=self.user, name='Food', kind=Category.Kind.EXPENSE)
        self.client.force_login(self.user)

    def test_major_private_pages_render_and_navigation_uses_named_routes(self):
        urls = [
            reverse('dashboard:home'),
            reverse('dashboard:analytics'),
            reverse('transactions:list'),
            reverse('transactions:all'),
            reverse('transactions:income'),
            reverse('transactions:investments'),
            reverse('transactions:categories'),
            reverse('budgets:goals'),
            reverse('subscriptions:list'),
            reverse('reports:index'),
            reverse('accounts:profile'),
            reverse('accounts:profile_edit'),
            reverse('accounts:password_change'),
            reverse('transactions:income_create'),
            reverse('transactions:expense_create'),
            reverse('transactions:category_create'),
            reverse('budgets:create'),
            reverse('subscriptions:create'),
            reverse('dashboard:settings'),
            reverse('dashboard:help'),
            reverse('dashboard:support'),
            reverse('dashboard:cards'),
            reverse('dashboard:insight'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                if url == reverse('dashboard:settings'):
                    self.assertRedirects(response, reverse('accounts:profile'))
                else:
                    self.assertEqual(response.status_code, 200)

        dashboard_response = self.client.get(reverse('dashboard:home'))
        self.assertContains(dashboard_response, reverse('reports:index'))
        self.assertContains(dashboard_response, reverse('budgets:goals'))
        self.assertContains(dashboard_response, reverse('subscriptions:list'))

    def test_dashboard_charts_use_database_values_and_render_chart_mounts(self):
        today = timezone.localdate()
        Transaction.objects.create(
            user=self.user, category=self.food, kind=Transaction.Kind.EXPENSE,
            amount=Decimal('38.25'), description='Groceries', date=today,
        )
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.context['monthly_chart']['values'][-1], 38.25)
        self.assertEqual(response.context['category_chart']['labels'], ['Food'])
        self.assertEqual(response.context['category_chart']['values'], [38.25])
        self.assertContains(response, 'monthlyExpensesChart')
        self.assertContains(response, 'expenseCategoryChart')

    def test_responsive_styles_cover_phone_and_tablet_widths(self):
        stylesheet = finders.find('css/styles.css')
        self.assertIsNotNone(stylesheet)
        contents = Path(stylesheet).read_text(encoding='utf-8')
        self.assertIn('@media (max-width: 720px)', contents)
        self.assertIn('@media (max-width: 480px)', contents)
        self.assertIn('.report-layout', contents)


class AdminPermissionTests(TestCase):
    def test_financial_models_are_registered_and_only_staff_can_open_admin(self):
        self.assertTrue({
            User,
            Category,
            Transaction,
            Goal,
            Subscription,
        }.issubset(set(admin.site._registry)))

        normal_user = User.objects.create_user(
            username='normal', email='normal@example.com', password='Strong-Normal-42!River'
        )
        self.client.force_login(normal_user)
        denied = self.client.get(reverse('admin:index'))
        self.assertEqual(denied.status_code, 302)
        self.assertIn(reverse('admin:login'), denied.url)

        staff_user = User.objects.create_user(
            username='staff', email='staff@example.com', password='Strong-Staff-42!River', is_staff=True
        )
        self.client.force_login(staff_user)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)

    def test_staff_without_model_permission_cannot_open_financial_changelist(self):
        staff_user = User.objects.create_user(
            username='limited-staff', email='limited@example.com',
            password='Strong-Limited-42!River', is_staff=True,
        )
        self.client.force_login(staff_user)
        response = self.client.get(reverse('admin:transactions_transaction_changelist'))
        self.assertEqual(response.status_code, 403)
