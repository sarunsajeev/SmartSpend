from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm

User = get_user_model()


def style_fields(form):
    for field in form.fields.values():
        css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
        existing = field.widget.attrs.get('class', '')
        field.widget.attrs['class'] = f'{existing} {css_class}'.strip()
        field.widget.attrs.setdefault('placeholder', field.label)


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(label='Email address')
    first_name = forms.CharField(label='First name', max_length=150)
    last_name = forms.CharField(label='Last name', max_length=150, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['password1'].help_text = 'Use at least 8 characters and avoid common passwords.'
        self.fields['password2'].help_text = 'Enter the same password again to confirm it.'

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        labels = {'first_name': 'First name', 'last_name': 'Last name', 'email': 'Email address'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
