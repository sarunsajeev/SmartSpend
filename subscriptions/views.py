from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import SubscriptionForm
from .models import Subscription


@login_required
def subscription_list(request):
    subscriptions = Subscription.objects.filter(user=request.user).order_by('next_renewal_date', 'name')
    return render(
        request,
        'subscriptions/list.html',
        {
            'subscriptions': subscriptions,
            'page_heading': 'Bills & Subscriptions',
            'topbar_subtitle': 'Review upcoming recurring payments',
            'today': timezone.localdate(),
            'now': timezone.localtime(),
        },
    )


@login_required
def subscription_create(request):
    form = SubscriptionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        subscription = form.save(commit=False)
        subscription.user = request.user
        subscription.save()
        messages.success(request, 'Your subscription was added.')
        return redirect('subscriptions:list')
    if request.method == 'POST':
        messages.error(request, 'Please correct the highlighted fields.')
    return render(
        request,
        'subscriptions/form.html',
        {
            'form': form,
            'page_heading': 'Add subscription',
            'topbar_subtitle': 'Track a bill or recurring service',
            'today': timezone.localdate(),
            'now': timezone.localtime(),
        },
    )


@login_required
def subscription_update(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
    form = SubscriptionForm(request.POST or None, instance=subscription)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your subscription was updated.')
        return redirect('subscriptions:list')
    if request.method == 'POST':
        messages.error(request, 'Please correct the highlighted fields.')
    return render(
        request,
        'subscriptions/form.html',
        {
            'form': form,
            'subscription': subscription,
            'page_heading': 'Edit subscription',
            'topbar_subtitle': 'Update your renewal details',
            'today': timezone.localdate(),
            'now': timezone.localtime(),
        },
    )


@login_required
def subscription_delete(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
    if request.method == 'POST':
        subscription.delete()
        messages.success(request, 'Your subscription was deleted.')
        return redirect('subscriptions:list')
    return render(
        request,
        'subscriptions/confirm_delete.html',
        {
            'subscription': subscription,
            'page_heading': 'Delete subscription',
            'topbar_subtitle': 'Confirm this change to your recurring payments',
            'today': timezone.localdate(),
            'now': timezone.localtime(),
        },
    )
