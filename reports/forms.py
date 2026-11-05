import calendar

from django import forms
from django.utils import timezone


class StatementOptionsForm(forms.Form):
    REPORT_SCOPES = (
        ('all', 'All transactions'),
        ('income', 'Income report'),
        ('expense', 'Expense report'),
    )
    PERIODS = (
        ('monthly', 'One month'),
        ('yearly', 'One year'),
        ('custom', 'Custom dates'),
        ('history', 'Complete history'),
    )

    report_scope = forms.ChoiceField(
        label='Report contents',
        choices=REPORT_SCOPES,
        initial='all',
    )
    period = forms.ChoiceField(label='Statement period', choices=PERIODS, initial='monthly')
    year = forms.IntegerField(label='Year', min_value=1900, required=False)
    month = forms.ChoiceField(
        label='Month',
        choices=(('', 'Choose a month'),) + tuple(
            (str(month), calendar.month_name[month]) for month in range(1, 13)
        ),
        required=False,
    )
    date_from = forms.DateField(
        label='Start date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    date_to = forms.DateField(
        label='End date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        self.fields['year'].max_value = today.year
        self.fields['year'].widget.attrs['max'] = today.year
        self.fields['year'].initial = today.year
        self.fields['month'].initial = str(today.month)
        for field in self.fields.values():
            widget = field.widget
            css_class = 'form-select' if isinstance(widget, forms.Select) else 'form-control'
            widget.attrs['class'] = css_class

    def clean_year(self):
        year = self.cleaned_data.get('year')
        if year and year > timezone.localdate().year:
            raise forms.ValidationError('Choose the current year or an earlier year.')
        return year

    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        year = cleaned_data.get('year')
        month = cleaned_data.get('month')
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if period in ('monthly', 'yearly') and not year:
            self.add_error('year', 'Choose the year for this statement.')
        if period == 'monthly' and not month:
            self.add_error('month', 'Choose the month for this statement.')
        if period == 'custom':
            if not date_from:
                self.add_error('date_from', 'Choose a start date for the custom statement.')
            if not date_to:
                self.add_error('date_to', 'Choose an end date for the custom statement.')
            if date_from and date_to and date_from > date_to:
                self.add_error('date_to', 'End date must be on or after the start date.')
        return cleaned_data
