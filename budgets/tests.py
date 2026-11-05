from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Goal


User = get_user_model()


class GoalManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='goal-user', email='goal@example.com', password='Strong-Goal-42!River'
        )
        self.other_user = User.objects.create_user(
            username='other-goal-user', email='other-goal@example.com', password='Strong-Goal-43!River'
        )
        self.goal = Goal.objects.create(
            user=self.user, name='Emergency fund', target_amount=Decimal('500.00'),
            current_amount=Decimal('100.00'),
        )
        self.other_goal = Goal.objects.create(
            user=self.other_user, name='Private goal', target_amount=Decimal('900.00'),
        )
        self.client.force_login(self.user)

    def payload(self, **updates):
        data = {
            'name': 'Travel fund',
            'target_amount': '1200.00',
            'current_amount': '150.00',
            'target_date': '',
            'is_active': 'on',
        }
        data.update(updates)
        return data

    def test_goal_create_update_delete_and_progress_calculation(self):
        response = self.client.post(reverse('budgets:create'), self.payload())
        self.assertRedirects(response, reverse('budgets:goals'))
        goal = Goal.objects.get(user=self.user, name='Travel fund')
        self.assertEqual(goal.progress_percentage, 12)

        response = self.client.post(
            reverse('budgets:update', args=[goal.pk]),
            self.payload(name='Updated trip', current_amount='300.00'),
        )
        self.assertRedirects(response, reverse('budgets:goals'))
        goal.refresh_from_db()
        self.assertEqual(goal.name, 'Updated trip')
        self.assertEqual(goal.progress_percentage, 25)

        response = self.client.post(reverse('budgets:delete', args=[goal.pk]))
        self.assertRedirects(response, reverse('budgets:goals'))
        self.assertFalse(Goal.objects.filter(pk=goal.pk).exists())

    def test_goal_form_rejects_invalid_amounts_and_other_users_goals_are_private(self):
        response = self.client.post(
            reverse('budgets:create'),
            self.payload(target_amount='100.00', current_amount='150.00'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Goal.objects.filter(user=self.user, name='Travel fund').exists())

        self.assertEqual(self.client.get(reverse('budgets:update', args=[self.other_goal.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('budgets:delete', args=[self.other_goal.pk])).status_code, 404)
        self.assertTrue(Goal.objects.filter(pk=self.other_goal.pk).exists())

    def test_goal_page_only_shows_the_signed_in_users_records(self):
        response = self.client.get(reverse('budgets:goals'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Emergency fund')
        self.assertNotContains(response, 'Private goal')
