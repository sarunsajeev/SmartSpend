from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from budgets.models import Goal
from subscriptions.models import Subscription
from transactions.models import Category, Transaction

from .forms import StatementOptionsForm
from .services import build_statement_data


User = get_user_model()


class FinancialStatementTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.user = User.objects.create_user(
            username='riya', email='riya@example.com', password='Violet-Cloud-42!River',
            first_name='Riya', last_name='Shah',
        )
        self.other_user = User.objects.create_user(
            username='other', email='other@example.com', password='Other-Cloud-42!River',
        )
        self.food = Category.objects.create(user=self.user, name='Food', kind=Category.Kind.EXPENSE)
        self.salary = Category.objects.create(user=self.user, name='Salary', kind=Category.Kind.INCOME)
        self.other_food = Category.objects.create(
            user=self.other_user, name='Private category', kind=Category.Kind.EXPENSE
        )
        self.income = Transaction.objects.create(
            user=self.user, category=self.salary, kind=Transaction.Kind.INCOME,
            amount=Decimal('2000.00'), description='Monthly salary', date=self.today,
        )
        self.expense = Transaction.objects.create(
            user=self.user, category=self.food, kind=Transaction.Kind.EXPENSE,
            amount=Decimal('60.00'), description='Cafe lunch', date=self.today,
        )
        self.investment = Transaction.objects.create(
            user=self.user, kind=Transaction.Kind.INVESTMENT,
            amount=Decimal('50.00'), description='Index fund', date=self.today,
        )
        Transaction.objects.create(
            user=self.other_user, category=self.other_food, kind=Transaction.Kind.EXPENSE,
            amount=Decimal('999.00'), description='FOREIGN_PRIVATE_RECORD', date=self.today,
        )
        Goal.objects.create(
            user=self.user, name='Emergency fund', target_amount=Decimal('5000.00'),
            current_amount=Decimal('750.00'),
        )
        Subscription.objects.create(
            user=self.user, name='Music plan', amount=Decimal('120.00'),
            billing_cycle=Subscription.BillingCycle.MONTHLY, next_renewal_date=self.today,
        )
        self.client.force_login(self.user)

    def options(self, **overrides):
        values = {
            'report_scope': 'all',
            'period': 'monthly',
            'year': self.today.year,
            'month': str(self.today.month),
            'date_from': '',
            'date_to': '',
        }
        values.update(overrides)
        return values

    def test_monthly_statement_data_uses_only_the_signed_in_users_records(self):
        data = build_statement_data(
            self.user,
            self._clean_options(self.options()),
            today=self.today,
        )

        self.assertEqual(data.income_total, Decimal('2000.00'))
        self.assertEqual(data.expense_total, Decimal('60.00'))
        self.assertEqual(data.investment_total, Decimal('50.00'))
        self.assertEqual(data.available_balance, Decimal('1890.00'))
        self.assertEqual(data.category_breakdown[0]['name'], 'Food')
        self.assertEqual(data.category_breakdown[0]['amount'], Decimal('60.00'))
        self.assertEqual(data.monthly_spending[0]['amount'], Decimal('60.00'))
        self.assertEqual(data.transactions, [self.income, self.expense, self.investment])
        self.assertNotIn('FOREIGN_PRIVATE_RECORD', [item.description for item in data.transactions])
        self.assertEqual(data.goal_target_total, Decimal('5000.00'))
        self.assertEqual(data.goal_current_total, Decimal('750.00'))
        self.assertEqual(data.subscription_monthly_total, Decimal('120.00'))

    def _clean_options(self, values):
        form = StatementOptionsForm(values)
        self.assertTrue(form.is_valid(), form.errors)
        return form.cleaned_data

    def test_yearly_and_custom_date_options_are_validated(self):
        yearly = StatementOptionsForm(self.options(period='yearly', month=''))
        self.assertTrue(yearly.is_valid(), yearly.errors)
        data = build_statement_data(self.user, yearly.cleaned_data, today=self.today)
        self.assertEqual(data.period_start, date(self.today.year, 1, 1))
        self.assertEqual(data.period_end, date(self.today.year, 12, 31))

        custom = StatementOptionsForm(self.options(
            period='custom', date_from=self.today.isoformat(), date_to=self.today.isoformat()
        ))
        self.assertTrue(custom.is_valid(), custom.errors)
        invalid = StatementOptionsForm(self.options(
            period='custom', date_from=self.today.isoformat(),
            date_to=(self.today.replace(day=1)).isoformat() if self.today.day > 1 else (self.today - timedelta(days=1)).isoformat(),
        ))
        self.assertFalse(invalid.is_valid())
        self.assertIn('date_to', invalid.errors)

    def test_pdf_download_returns_attachment_without_writing_report_files(self):
        before = Transaction.objects.count()
        response = self.client.get(reverse('reports:download'), self.options())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename="smartspend-all-', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF-'))
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertEqual(Transaction.objects.count(), before)

    def test_income_report_contains_only_income_rows_but_period_totals_remain_complete(self):
        options = self._clean_options(self.options(report_scope='income'))
        data = build_statement_data(self.user, options, today=self.today)
        self.assertEqual(data.income_total, Decimal('2000.00'))
        self.assertEqual(data.expense_total, Decimal('60.00'))
        self.assertEqual([transaction.kind for transaction in data.transactions], [Transaction.Kind.INCOME])

    def test_statement_views_require_login_and_invalid_dates_do_not_download(self):
        self.client.logout()
        response = self.client.get(reverse('reports:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

        self.client.force_login(self.user)
        invalid_response = self.client.get(
            reverse('reports:download'),
            self.options(period='custom', date_from='', date_to=''),
        )
        self.assertEqual(invalid_response.status_code, 400)
        self.assertNotEqual(invalid_response['Content-Type'], 'application/pdf')
