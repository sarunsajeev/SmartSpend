from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import GoalForm
from .models import Goal


def _page_context(request, heading, subtitle):
    return {
        'page_heading': heading,
        'topbar_subtitle': subtitle,
        'today': timezone.localdate(),
        'now': timezone.localtime(),
    }


@login_required
def goal_list(request):
    goals = Goal.objects.filter(user=request.user).order_by('-is_active', 'target_date', 'name')
    context = _page_context(request, 'Goals', 'Track progress toward your milestones')
    context['goals'] = goals
    return render(request, 'budgets/list.html', context)


@login_required
def goal_create(request):
    form = GoalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        goal = form.save(commit=False)
        goal.user = request.user
        goal.save()
        messages.success(request, 'Your savings goal was created.')
        return redirect('budgets:goals')
    if request.method == 'POST':
        messages.error(request, 'Please correct the highlighted fields.')
    context = _page_context(request, 'Add a goal', 'Create a savings target for your account')
    context['form'] = form
    return render(request, 'budgets/form.html', context)


@login_required
def goal_update(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    form = GoalForm(request.POST or None, instance=goal)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your savings goal was updated.')
        return redirect('budgets:goals')
    if request.method == 'POST':
        messages.error(request, 'Please correct the highlighted fields.')
    context = _page_context(request, 'Edit a goal', 'Update this savings target')
    context.update({'form': form, 'goal': goal})
    return render(request, 'budgets/form.html', context)


@login_required
def goal_delete(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Your savings goal was deleted.')
        return redirect('budgets:goals')
    context = _page_context(request, 'Delete a goal', 'Confirm this change to your goals')
    context['goal'] = goal
    return render(request, 'budgets/confirm_delete.html', context)
