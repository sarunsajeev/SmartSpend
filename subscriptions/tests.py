from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Subscription


User = get_user_model()


class SubscriptionManagementTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.user = User.objects.create_user(
            username='sub-user', email='sub@example.com', password='Strong-Sub-42!River'
        )
        self.other_user = User.objects.create_user(
            username='other-sub-user', email='other-sub@example.com', password='Strong-Sub-43!River'
        )
        self.subscription = Subscription.objects.create(
            user=self.user, name='Music plan', amount=Decimal('9.99'),
            billing_cycle=Subscription.BillingCycle.MONTHLY, next_renewal_date=self.today,
        )
        self.other_subscription = Subscription.objects.create(
            user=self.other_user, name='Private service', amount=Decimal('22.00'),
            billing_cycle=Subscription.BillingCycle.YEARLY, next_renewal_date=self.today,
        )
        self.client.force_login(self.user)

    def payload(self, **updates):
        data = {
            'name': 'Cloud storage',
            'amount': '4.99',
            'billing_cycle': Subscription.BillingCycle.MONTHLY,
            'next_renewal_date': self.today.isoformat(),
            'is_active': 'on',
        }
        data.update(updates)
        return data

    def test_subscription_create_update_delete(self):
        response = self.client.post(reverse('subscriptions:create'), self.payload())
        self.assertRedirects(response, reverse('subscriptions:list'))
        subscription = Subscription.objects.get(user=self.user, name='Cloud storage')

        response = self.client.post(
            reverse('subscriptions:update', args=[subscription.pk]),
            self.payload(name='Updated storage', amount='5.49'),
        )
        self.assertRedirects(response, reverse('subscriptions:list'))
        subscription.refresh_from_db()
        self.assertEqual(subscription.name, 'Updated storage')
        self.assertEqual(subscription.amount, Decimal('5.49'))

        response = self.client.post(reverse('subscriptions:delete', args=[subscription.pk]))
        self.assertRedirects(response, reverse('subscriptions:list'))
        self.assertFalse(Subscription.objects.filter(pk=subscription.pk).exists())

    def test_subscription_validation_and_owner_scope(self):
        response = self.client.post(reverse('subscriptions:create'), self.payload(amount='0'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Subscription.objects.filter(user=self.user, name='Cloud storage').exists())

        self.assertEqual(
            self.client.get(reverse('subscriptions:update', args=[self.other_subscription.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(reverse('subscriptions:delete', args=[self.other_subscription.pk])).status_code,
            404,
        )
        self.assertTrue(Subscription.objects.filter(pk=self.other_subscription.pk).exists())

    def test_subscription_list_only_shows_the_signed_in_users_records(self):
        response = self.client.get(reverse('subscriptions:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Music plan')
        self.assertNotContains(response, 'Private service')
