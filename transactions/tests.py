from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Transaction

User = get_user_model()


class TransactionManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='maya', email='maya@example.com', password='Original-Lantern-48!River'
        )
        self.other_user = User.objects.create_user(
            username='sam', email='sam@example.com', password='Other-Lantern-48!River'
        )
        self.food = Category.objects.create(user=self.user, name='Food', kind=Category.Kind.EXPENSE)
        self.salary = Category.objects.create(user=self.user, name='Salary', kind=Category.Kind.INCOME)
        self.other_food = Category.objects.create(
            user=self.other_user, name='Food', kind=Category.Kind.EXPENSE
        )
        self.client.force_login(self.user)
        self.today = timezone.localdate()

    def expense_payload(self, **overrides):
        payload = {
            'category': self.food.pk,
            'amount': '24.50',
            'description': 'Lunch at market',
            'subcategory': 'Cafe',
            'date': self.today.isoformat(),
            'payment_method': Transaction.PaymentMethod.UPI,
        }
        payload.update(overrides)
        return payload

    def income_payload(self, **overrides):
        payload = {
            'category': self.salary.pk,
            'amount': '1500.75',
            'description': 'Monthly salary',
            'subcategory': '',
            'date': self.today.isoformat(),
            'payment_method': Transaction.PaymentMethod.BANK,
        }
        payload.update(overrides)
        return payload

    def test_create_expense_and_income(self):
        expense_response = self.client.post(
            reverse('transactions:expense_create'), self.expense_payload()
        )
        income_response = self.client.post(
            reverse('transactions:income_create'), self.income_payload()
        )

        self.assertRedirects(expense_response, reverse('transactions:list'))
        self.assertRedirects(income_response, reverse('transactions:income'))
        expense = Transaction.objects.get(description='Lunch at market')
        income = Transaction.objects.get(description='Monthly salary')
        self.assertEqual(expense.user, self.user)
        self.assertEqual(expense.kind, Transaction.Kind.EXPENSE)
        self.assertEqual(expense.amount, Decimal('24.50'))
        self.assertEqual(expense.payment_method, Transaction.PaymentMethod.UPI)
        self.assertEqual(income.kind, Transaction.Kind.INCOME)
        self.assertEqual(income.user, self.user)

    def test_income_can_be_edited_and_deleted(self):
        income = Transaction.objects.create(
            user=self.user,
            category=self.salary,
            kind=Transaction.Kind.INCOME,
            amount=Decimal('1500.75'),
            description='Monthly salary',
            date=self.today,
            payment_method=Transaction.PaymentMethod.BANK,
        )

        edit_response = self.client.post(
            reverse('transactions:update', args=[income.pk]),
            self.income_payload(amount='1750.00', description='Updated salary'),
        )
        self.assertRedirects(edit_response, reverse('transactions:income'))
        income.refresh_from_db()
        self.assertEqual(income.description, 'Updated salary')
        self.assertEqual(income.amount, Decimal('1750.00'))

        delete_response = self.client.post(reverse('transactions:delete', args=[income.pk]))
        self.assertRedirects(delete_response, reverse('transactions:income'))
        self.assertFalse(Transaction.objects.filter(pk=income.pk).exists())

    def test_form_rejects_zero_amount_and_another_users_category(self):
        zero_response = self.client.post(
            reverse('transactions:expense_create'), self.expense_payload(amount='0')
        )
        foreign_response = self.client.post(
            reverse('transactions:expense_create'),
            self.expense_payload(category=self.other_food.pk),
        )

        self.assertEqual(zero_response.status_code, 200)
        self.assertEqual(foreign_response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 0)
        self.assertContains(foreign_response, 'Select a valid choice')

    def test_edit_and_detail_only_show_owner_records(self):
        transaction = Transaction.objects.create(
            user=self.user,
            category=self.food,
            kind=Transaction.Kind.EXPENSE,
            amount=Decimal('12.00'),
            description='Old lunch',
            date=self.today,
        )
        response = self.client.post(
            reverse('transactions:update', args=[transaction.pk]),
            self.expense_payload(amount='16.25', description='Updated lunch'),
        )

        self.assertRedirects(response, reverse('transactions:list'))
        transaction.refresh_from_db()
        self.assertEqual(transaction.description, 'Updated lunch')
        self.assertEqual(transaction.amount, Decimal('16.25'))
        self.assertEqual(self.client.get(reverse('transactions:detail', args=[transaction.pk])).status_code, 200)

        private_record = Transaction.objects.create(
            user=self.other_user,
            category=self.other_food,
            kind=Transaction.Kind.EXPENSE,
            amount=Decimal('50.00'),
            description='Private record',
            date=self.today,
        )
        self.assertEqual(self.client.get(reverse('transactions:detail', args=[private_record.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('transactions:update', args=[private_record.pk])).status_code, 404)

    def test_delete_is_post_only_and_user_scoped(self):
        transaction = Transaction.objects.create(
            user=self.user,
            category=self.food,
            kind=Transaction.Kind.EXPENSE,
            amount=Decimal('12.00'),
            description='To remove',
            date=self.today,
        )
        self.assertEqual(self.client.get(reverse('transactions:delete', args=[transaction.pk])).status_code, 200)
        response = self.client.post(reverse('transactions:delete', args=[transaction.pk]))
        self.assertRedirects(response, reverse('transactions:list'))
        self.assertFalse(Transaction.objects.filter(pk=transaction.pk).exists())

        other_transaction = Transaction.objects.create(
            user=self.other_user,
            category=self.other_food,
            kind=Transaction.Kind.EXPENSE,
            amount=Decimal('50.00'),
            description='Keep private',
            date=self.today,
        )
        self.assertEqual(self.client.post(reverse('transactions:delete', args=[other_transaction.pk])).status_code, 404)
        self.assertTrue(Transaction.objects.filter(pk=other_transaction.pk).exists())

    def test_transaction_search_type_category_date_and_sort_filters(self):
        older = Transaction.objects.create(
            user=self.user,
            category=self.food,
            kind=Transaction.Kind.EXPENSE,
            amount=Decimal('10.00'),
            description='Cafe breakfast',
            date=self.today - timedelta(days=2),
        )
        newer = Transaction.objects.create(
            user=self.user,
            category=self.food,
            kind=Transaction.Kind.EXPENSE,
            amount=Decimal('40.00'),
            description='Market groceries',
            date=self.today,
        )
        income = Transaction.objects.create(
            user=self.user,
            category=self.salary,
            kind=Transaction.Kind.INCOME,
            amount=Decimal('100.00'),
            description='Salary credit',
            date=self.today,
        )

        search_response = self.client.get(reverse('transactions:all'), {'q': 'groceries'})
        self.assertEqual(search_response.context['page_obj'].paginator.count, 1)
        self.assertEqual(search_response.context['page_obj'][0], newer)

        filtered_response = self.client.get(
            reverse('transactions:all'),
            {
                'kind': Transaction.Kind.EXPENSE,
                'category': self.food.pk,
                'date_from': self.today.isoformat(),
                'date_to': self.today.isoformat(),
                'sort': 'amount_desc',
            },
        )
        self.assertEqual(list(filtered_response.context['transactions']), [newer])
        self.assertNotIn(income, filtered_response.context['transactions'])
        self.assertNotIn(older, filtered_response.context['transactions'])

        amount_sorted = self.client.get(reverse('transactions:all'), {'sort': 'amount_asc'})
        self.assertEqual(
            list(amount_sorted.context['transactions']),
            [older, newer, income],
        )
        date_sorted = self.client.get(reverse('transactions:all'), {'sort': 'date_asc'})
        self.assertEqual(date_sorted.context['transactions'][0], older)

    def test_transaction_list_is_paginated(self):
        for number in range(15):
            Transaction.objects.create(
                user=self.user,
                category=self.food,
                kind=Transaction.Kind.EXPENSE,
                amount=Decimal(number + 1),
                description=f'Expense {number}',
                date=self.today,
            )

        response = self.client.get(reverse('transactions:all'), {'page': '2'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].number, 2)
        self.assertEqual(response.context['page_obj'].paginator.count, 15)
        self.assertContains(response, 'Page 2 of 2')

    def test_category_create_update_and_delete_are_scoped(self):
        create_response = self.client.post(
            reverse('transactions:category_create'),
            {'name': 'Travel', 'kind': Category.Kind.EXPENSE},
        )
        self.assertRedirects(create_response, reverse('transactions:categories'))
        category = Category.objects.get(user=self.user, name='Travel')

        edit_response = self.client.post(
            reverse('transactions:category_update', args=[category.pk]),
            {'name': 'Local travel', 'kind': Category.Kind.EXPENSE},
        )
        self.assertRedirects(edit_response, reverse('transactions:categories'))
        category.refresh_from_db()
        self.assertEqual(category.name, 'Local travel')

        delete_response = self.client.post(reverse('transactions:category_delete', args=[category.pk]))
        self.assertRedirects(delete_response, reverse('transactions:categories'))
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())

        self.assertEqual(
            self.client.get(reverse('transactions:category_update', args=[self.other_food.pk])).status_code,
            404,
        )

    def test_category_in_use_cannot_be_deleted_or_retyped(self):
        Transaction.objects.create(
            user=self.user,
            category=self.food,
            kind=Transaction.Kind.EXPENSE,
            amount=Decimal('12.00'),
            description='Food purchase',
            date=self.today,
        )
        delete_response = self.client.post(reverse('transactions:category_delete', args=[self.food.pk]), follow=True)
        self.assertTrue(Category.objects.filter(pk=self.food.pk).exists())
        self.assertContains(delete_response, 'used by transactions')

        edit_response = self.client.post(
            reverse('transactions:category_update', args=[self.food.pk]),
            {'name': 'Food', 'kind': Category.Kind.INCOME},
        )
        self.assertEqual(edit_response.status_code, 200)
        self.food.refresh_from_db()
        self.assertEqual(self.food.kind, Category.Kind.EXPENSE)


class DashboardFinancialIntegrationTests(TestCase):
    def test_dashboard_totals_and_recent_activity_use_database_records(self):
        user = User.objects.create_user(
            username='ria', email='ria@example.com', password='Bright-Cedar-91!Cloud'
        )
        food = Category.objects.create(user=user, name='Food', kind=Category.Kind.EXPENSE)
        salary = Category.objects.create(user=user, name='Salary', kind=Category.Kind.INCOME)
        today = timezone.localdate()
        Transaction.objects.create(
            user=user, category=salary, kind=Transaction.Kind.INCOME,
            amount=Decimal('1000.00'), description='Pay', date=today,
        )
        expense = Transaction.objects.create(
            user=user, category=food, kind=Transaction.Kind.EXPENSE,
            amount=Decimal('125.50'), description='Lunch', date=today,
        )
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard:home'))

        self.assertEqual(response.context['income_total'], Decimal('1000.00'))
        self.assertEqual(response.context['expense_total'], Decimal('125.50'))
        self.assertEqual(response.context['monthly_expenses'], Decimal('125.50'))
        self.assertEqual(response.context['available_balance'], Decimal('874.50'))
        self.assertEqual(list(response.context['recent_transactions']), [expense, Transaction.objects.get(description='Pay')])
