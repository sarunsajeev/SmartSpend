from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Category, Transaction


class TransactionForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d'],
    )

    class Meta:
        model = Transaction
        fields = ('category', 'amount', 'description', 'subcategory', 'date', 'payment_method')
        labels = {
            'category': 'Category',
            'amount': 'Amount',
            'description': 'Description',
            'subcategory': 'Subcategory (optional)',
            'date': 'Date',
            'payment_method': 'Payment method',
        }
        widgets = {
            'amount': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01', 'inputmode': 'decimal'}),
            'description': forms.TextInput(attrs={'maxlength': '180'}),
            'subcategory': forms.TextInput(attrs={'maxlength': '80'}),
        }

    def __init__(self, *args, user, kind, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.kind = kind
        self.instance.user = user
        self.instance.kind = kind
        self.fields['category'].queryset = Category.objects.filter(user=user, kind=kind)
        self.fields['category'].empty_label = 'Choose a category'
        self.fields['category'].required = True
        self.fields['description'].required = True
        self.fields['payment_method'].required = True
        if not self.instance.pk:
            self.fields['date'].initial = timezone.localdate()

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'

    def clean_category(self):
        category = self.cleaned_data['category']
        if category.user_id != self.user.pk or category.kind != self.kind:
            raise ValidationError('Choose one of your categories for this transaction type.')
        return category

    def save(self, commit=True):
        self.instance.user = self.user
        self.instance.kind = self.kind
        return super().save(commit=commit)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'kind')
        labels = {'name': 'Category name', 'kind': 'Category type'}
        widgets = {'name': forms.TextInput(attrs={'maxlength': '80'})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'

    def clean_name(self):
        return self.cleaned_data['name'].strip()

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        kind = cleaned_data.get('kind')
        if not name or not kind:
            return cleaned_data
        duplicate = Category.objects.filter(user=self.user, kind=kind, name__iexact=name)
        if self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            self.add_error('name', 'You already have a category with this name and type.')
        return cleaned_data

    def clean_kind(self):
        kind = self.cleaned_data['kind']
        if self.instance.pk and self.instance.kind != kind and self.instance.transactions.exists():
            raise ValidationError('A category used by transactions cannot change type. Create another category instead.')
        return kind


class TransactionFilterForm(forms.Form):
    SORT_CHOICES = (
        ('date_desc', 'Newest first'),
        ('date_asc', 'Oldest first'),
        ('amount_desc', 'Highest amount'),
        ('amount_asc', 'Lowest amount'),
    )

    q = forms.CharField(required=False, label='Search', max_length=100)
    kind = forms.ChoiceField(
        required=False,
        label='Type',
        choices=(('', 'All types'), *Transaction.Kind.choices),
    )
    category = forms.ModelChoiceField(
        required=False,
        label='Category',
        queryset=Category.objects.none(),
        empty_label='All categories',
    )
    date_from = forms.DateField(required=False, label='From', widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, label='To', widget=forms.DateInput(attrs={'type': 'date'}))
    sort = forms.ChoiceField(required=False, label='Sort', choices=SORT_CHOICES, initial='date_desc')

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        if date_from and date_to and date_from > date_to:
            self.add_error('date_to', 'End date must be on or after the start date.')
        return cleaned_data
