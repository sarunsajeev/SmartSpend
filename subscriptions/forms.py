from django import forms

from .models import Subscription


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ('name', 'amount', 'billing_cycle', 'next_renewal_date', 'is_active')
        labels = {
            'name': 'Service name',
            'amount': 'Amount per billing cycle',
            'billing_cycle': 'Billing cycle',
            'next_renewal_date': 'Next renewal date',
            'is_active': 'Include in upcoming renewals',
        }
        widgets = {
            'name': forms.TextInput(attrs={'maxlength': '100'}),
            'amount': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01', 'inputmode': 'decimal'}),
            'next_renewal_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else ('form-select' if isinstance(field.widget, forms.Select) else 'form-control')
