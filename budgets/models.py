from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Goal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='financial_goals',
    )
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    current_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    target_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['target_date', 'name']

    def clean(self):
        super().clean()
        if (
            self.current_amount is not None
            and self.target_amount is not None
            and self.current_amount > self.target_amount
        ):
            raise ValidationError({'current_amount': 'Saved amount cannot exceed the goal target.'})

    @property
    def progress_percentage(self):
        if not self.target_amount:
            return 0
        return min(int(self.current_amount * 100 / self.target_amount), 100)

    def __str__(self):
        return self.name
