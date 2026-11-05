from django import forms

from .models import Goal


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ('name', 'target_amount', 'current_amount', 'target_date', 'is_active')
        labels = {
            'name': 'Goal name',
            'target_amount': 'Target amount',
            'current_amount': 'Amount saved',
            'target_date': 'Target date (optional)',
            'is_active': 'Keep this goal active',
        }
        widgets = {
            'name': forms.TextInput(attrs={'maxlength': '100'}),
            'target_amount': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01', 'inputmode': 'decimal'}),
            'current_amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01', 'inputmode': 'decimal'}),
            'target_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
