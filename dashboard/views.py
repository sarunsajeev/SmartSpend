from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render
from django.utils import timezone

from budgets.models import Goal
from subscriptions.models import Subscription
from transactions.models import Transaction


ZERO = Decimal('0.00')


def _total(queryset):
    return queryset.aggregate(total=Sum('amount'))['total'] or ZERO


def _dashboard_data(user):
    today = timezone.localdate()
    user_transactions = Transaction.objects.filter(user=user)

    income_total = _total(user_transactions.filter(kind=Transaction.Kind.INCOME))
    expense_total = _total(user_transactions.filter(kind=Transaction.Kind.EXPENSE))
    investment_total = _total(user_transactions.filter(kind=Transaction.Kind.INVESTMENT))
    available_balance = income_total - expense_total - investment_total

    first_of_month = today.replace(day=1)
    monthly_expenses = _total(
        user_transactions.filter(
            kind=Transaction.Kind.EXPENSE,
            date__year=today.year,
            date__month=today.month,
        )
    )
    monthly_income = _total(
        user_transactions.filter(
            kind=Transaction.Kind.INCOME,
            date__year=today.year,
            date__month=today.month,
        )
    )

    # Build a rolling six-month window. Missing months appear as zero in the
    # chart, while every non-zero value still comes from the user's records.
    month_starts = [first_of_month]
    for _ in range(5):
        previous_month = month_starts[-1] - timedelta(days=1)
        month_starts.append(previous_month.replace(day=1))
    month_starts.reverse()
    next_month = (first_of_month + timedelta(days=32)).replace(day=1)

    monthly_rows = (
        user_transactions.filter(
            kind=Transaction.Kind.EXPENSE,
            date__gte=month_starts[0],
            date__lt=next_month,
        )
        .order_by()
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
    )
    monthly_totals_decimal = {
        (row['month'].year, row['month'].month): row['total']
        for row in monthly_rows
    }
    monthly_chart = {
        'labels': [month.strftime('%b') for month in month_starts],
        'values': [
            float(monthly_totals_decimal.get((month.year, month.month), ZERO))
            for month in month_starts
        ],
    }

    investment_rows = (
        user_transactions.filter(
            kind=Transaction.Kind.INVESTMENT,
            date__gte=month_starts[0],
            date__lt=next_month,
        )
        .order_by()
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
    )
    investment_totals = {
        (row['month'].year, row['month'].month): float(row['total'])
        for row in investment_rows
    }
    investment_sparkline = {
        'labels': [month.strftime('%b') for month in month_starts],
        'values': [investment_totals.get((month.year, month.month), 0) for month in month_starts],
    }

    previous_month = month_starts[-2]
    previous_month_expenses = monthly_totals_decimal.get(
        (previous_month.year, previous_month.month), ZERO
    )
    expense_change_percent = None
    expense_change_label = 'No previous month to compare'
    expense_change_tone = 'trend-neutral'
    if previous_month_expenses:
        change = (monthly_expenses - previous_month_expenses) * 100 / previous_month_expenses
        expense_change_percent = abs(change).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
        if change > 0:
            expense_change_label = f'{expense_change_percent}% more than last month'
            expense_change_tone = 'trend-up'
        elif change < 0:
            expense_change_label = f'{expense_change_percent}% less than last month'
            expense_change_tone = 'trend-down'
        else:
            expense_change_label = 'Same as last month'

    category_rows = (
        user_transactions.filter(
            kind=Transaction.Kind.EXPENSE,
            date__year=today.year,
            date__month=today.month,
        )
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    category_chart = {
        'labels': [row['category__name'] or 'Uncategorized' for row in category_rows],
        'values': [float(row['total']) for row in category_rows],
    }

    active_goals = Goal.objects.filter(user=user, is_active=True)
    goal_count = active_goals.count()
    goal_target_total = active_goals.aggregate(total=Sum('target_amount'))['total'] or ZERO
    goal_current_total = active_goals.aggregate(total=Sum('current_amount'))['total'] or ZERO
    goal_progress = 0
    if goal_target_total:
        goal_progress = min(int(goal_current_total * 100 / goal_target_total), 100)
    featured_goal = active_goals.order_by('target_date', 'created_at').first()

    display_name = user.first_name or user.username
    local_now = timezone.localtime()

    return {
        'today': today,
        'now': local_now,
        'display_name': display_name,
        'page_heading': f'Hi, {display_name}',
        'show_greeting_wave': True,
        'topbar_subtitle': 'Track your expenses and transactions',
        'has_financial_records': user_transactions.exists(),
        'available_balance': available_balance,
        'income_total': income_total,
        'expense_total': expense_total,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'investment_total': investment_total,
        'goal_count': goal_count,
        'goal_target_total': goal_target_total,
        'goal_progress': goal_progress,
        'featured_goal': featured_goal,
        'month_label': today.strftime('%B %Y'),
        'monthly_chart': monthly_chart,
        'investment_sparkline': investment_sparkline,
        'category_chart': category_chart,
        'has_monthly_expenses': any(monthly_chart['values']),
        'has_investments': bool(investment_total),
        'has_recent_investments': any(investment_sparkline['values']),
        'has_category_expenses': bool(category_chart['values']),
        'expense_change_label': expense_change_label,
        'expense_change_percent': expense_change_percent,
        'expense_change_tone': expense_change_tone,
        'recent_transactions': user_transactions.select_related('category')[:5],
        'upcoming_subscriptions': Subscription.objects.filter(
            user=user, is_active=True
        ).order_by('next_renewal_date')[:4],
    }


@login_required
def home(request):
    return render(request, 'dashboard/index.html', _dashboard_data(request.user))


@login_required
def analytics(request):
    context = _dashboard_data(request.user)
    context['page_heading'] = 'Analytics'
    context['show_greeting_wave'] = False
    return render(request, 'dashboard/analytics.html', context)


@login_required
def section_page(request, section):
    if section == 'settings':
        return redirect('accounts:profile')
    sections = {
        'cards': {
            'title': 'Cards',
            'description': 'Card tracking is planned for a later stage. Your current expenses and investments remain available from the sidebar.',
            'icon': 'card',
        },
        'insight': {
            'title': 'Insight',
            'description': 'Personalized insights will be built from your recorded transactions in a later stage.',
            'icon': 'trend',
        },
        'settings': {
            'title': 'Settings',
            'description': 'Your account details are shown here. Editable profile preferences will be added in a later stage.',
            'icon': 'settings',
        },
        'help': {
            'title': 'Help Center',
            'description': 'SmartSpend keeps your records private to your account. Use the navigation to review your expenses, goals, investments, and subscriptions.',
            'icon': 'help',
        },
        'support': {
            'title': 'Support',
            'description': 'Support tools will be added as the project grows. For now, your account and records are managed through SmartSpend.',
            'icon': 'support',
        },
    }
    page = sections[section]
    return render(
        request,
        'dashboard/section.html',
        {
            'section': page,
            'section_key': section,
            'page_heading': page['title'],
            'today': timezone.localdate(),
            'now': timezone.localtime(),
            'topbar_subtitle': 'Your personal finance workspace',
        },
    )
