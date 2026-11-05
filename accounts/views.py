from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from transactions.services import create_default_categories

from .forms import (
    ProfileEditForm,
    RegistrationForm,
    StyledAuthenticationForm,
    StyledPasswordChangeForm,
)


class SmartSpendLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    authentication_form = StyledAuthenticationForm

    def form_valid(self, form):
        messages.success(self.request, 'Welcome back to SmartSpend.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'We could not sign you in. Check your username and password.')
        return super().form_invalid(form)


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = form.save()
            create_default_categories(user)
        auth_login(request, user)
        messages.success(request, 'Your SmartSpend account is ready.')
        return redirect('dashboard:home')

    if request.method == 'POST':
        messages.error(request, 'Please correct the highlighted fields.')
    return render(
        request,
        'accounts/register.html',
        {
            'form': form,
            'page_heading': 'Create your account',
            'today': timezone.localdate(),
        },
    )


@login_required
def profile(request):
    return render(
        request,
        'accounts/profile.html',
        {
            'page_heading': 'My profile',
            'topbar_subtitle': 'Manage your account and security',
            'today': timezone.localdate(),
            'now': timezone.localtime(),
        },
    )


@login_required
def profile_edit(request):
    form = ProfileEditForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your profile has been updated.')
        return redirect('accounts:profile')
    if request.method == 'POST':
        messages.error(request, 'Please correct the highlighted fields.')
    return render(
        request,
        'accounts/profile_form.html',
        {
            'form': form,
            'page_heading': 'Edit profile',
            'topbar_subtitle': 'Update your name and email address',
            'today': timezone.localdate(),
            'now': timezone.localtime(),
        },
    )


class SmartSpendPasswordChangeView(PasswordChangeView):
    form_class = StyledPasswordChangeForm
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        messages.success(self.request, 'Your password has been changed.')
        return super().form_valid(form)


@login_required
@require_POST
def logout_view(request):
    auth_logout(request)
    messages.success(request, 'You have signed out safely.')
    return redirect('accounts:login')

# Create your views here.
