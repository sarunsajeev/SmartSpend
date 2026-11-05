from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    class Kind(models.TextChoices):
        INCOME = 'income', 'Income'
        EXPENSE = 'expense', 'Expense'
        INVESTMENT = 'investment', 'Investment'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transaction_categories',
    )
    name = models.CharField(max_length=80)
    kind = models.CharField(max_length=12, choices=Kind.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name', 'kind'],
                name='unique_user_category_kind',
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.get_kind_display()})'


class Transaction(models.Model):
    class Kind(models.TextChoices):
        INCOME = 'income', 'Income'
        EXPENSE = 'expense', 'Expense'
        INVESTMENT = 'investment', 'Investment'

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Cash'
        UPI = 'upi', 'UPI'
        CARD = 'card', 'Card'
        BANK = 'bank', 'Bank'
        OTHER = 'other', 'Other'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='transactions',
        blank=True,
        null=True,
    )
    kind = models.CharField(max_length=12, choices=Kind.choices)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    description = models.CharField(max_length=180, blank=True)
    subcategory = models.CharField(max_length=80, blank=True, default='')
    payment_method = models.CharField(
        max_length=8,
        choices=PaymentMethod.choices,
        blank=True,
        default='',
    )
    date = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'kind', 'date']),
        ]

    def clean(self):
        super().clean()
        if self.category_id and self.user_id:
            if self.category.user_id != self.user_id:
                raise ValidationError({'category': 'Choose one of your own categories.'})
            if self.category.kind != self.kind:
                raise ValidationError({'category': 'Category type must match transaction type.'})

    def __str__(self):
        label = self.description or self.get_kind_display()
        return f'{label} — {self.amount}'
