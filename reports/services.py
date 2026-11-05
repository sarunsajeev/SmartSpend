import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from budgets.models import Goal
from subscriptions.models import Subscription
from transactions.models import Transaction


ZERO = Decimal('0.00')
MONTHS_IN_CHART = 12


@dataclass
class StatementData:
    period_start: date | None
    period_end: date | None
    period_label: str
    report_scope: str
    report_scope_label: str
    income_total: Decimal
    expense_total: Decimal
    investment_total: Decimal
    available_balance: Decimal
    category_breakdown: list
    monthly_spending: list
    transactions: list
    subscriptions: list
    subscription_monthly_total: Decimal
    goals: list
    goal_target_total: Decimal
    goal_current_total: Decimal


def _month_starts(start, end):
    current = date(start.year, start.month, 1)
    final = date(end.year, end.month, 1)
    months = []
    while current <= final:
        months.append(current)
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return months


def period_bounds(options, today=None):
    today = today or timezone.localdate()
    period = options['period']
    if period == 'monthly':
        year = options['year']
        month = int(options['month'])
        return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
    if period == 'yearly':
        year = options['year']
        return date(year, 1, 1), date(year, 12, 31)
    if period == 'custom':
        return options['date_from'], options['date_to']
    return None, today


def _apply_period(queryset, period_start, period_end):
    if period_start:
        queryset = queryset.filter(date__gte=period_start)
    if period_end:
        queryset = queryset.filter(date__lte=period_end)
    return queryset


def _total(queryset):
    return queryset.aggregate(total=Sum('amount'))['total'] or ZERO


def _monthly_spending(expenses, period_start, period_end, today):
    if period_start is None or period_end is None:
        end_month = date(today.year, today.month, 1)
        start_year, start_month = end_month.year, end_month.month - (MONTHS_IN_CHART - 1)
        while start_month <= 0:
            start_month += 12
            start_year -= 1
        months = _month_starts(date(start_year, start_month, 1), end_month)
    else:
        months = _month_starts(period_start, period_end)
        if len(months) > MONTHS_IN_CHART:
            months = months[-MONTHS_IN_CHART:]

    chart_start = months[0]
    last_month = months[-1]
    chart_end = date(
        last_month.year,
        last_month.month,
        calendar.monthrange(last_month.year, last_month.month)[1],
    )
    month_totals = {
        (row['month'].year, row['month'].month): row['total']
        for row in expenses.filter(date__gte=chart_start, date__lte=chart_end)
        .order_by()
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
    }
    return [
        {
            'label': month.strftime('%b %Y'),
            'short_label': month.strftime('%b'),
            'amount': month_totals.get((month.year, month.month), ZERO),
        }
        for month in months
    ]


def _monthly_subscription_cost(subscription):
    if subscription.billing_cycle == Subscription.BillingCycle.WEEKLY:
        return subscription.amount * Decimal('52') / Decimal('12')
    if subscription.billing_cycle == Subscription.BillingCycle.QUARTERLY:
        return subscription.amount / Decimal('3')
    if subscription.billing_cycle == Subscription.BillingCycle.YEARLY:
        return subscription.amount / Decimal('12')
    return subscription.amount


def build_statement_data(user, options, today=None):
    """Gather statement figures with every financial query scoped to one user."""
    today = today or timezone.localdate()
    period_start, period_end = period_bounds(options, today)
    all_transactions = Transaction.objects.filter(user=user).select_related('category')
    period_transactions = _apply_period(all_transactions, period_start, period_end)

    totals = {
        kind: _total(period_transactions.filter(kind=kind))
        for kind in (Transaction.Kind.INCOME, Transaction.Kind.EXPENSE, Transaction.Kind.INVESTMENT)
    }
    as_of_transactions = all_transactions
    if period_end:
        as_of_transactions = as_of_transactions.filter(date__lte=period_end)
    available_balance = (
        _total(as_of_transactions.filter(kind=Transaction.Kind.INCOME))
        - _total(as_of_transactions.filter(kind=Transaction.Kind.EXPENSE))
        - _total(as_of_transactions.filter(kind=Transaction.Kind.INVESTMENT))
    )

    expense_transactions = period_transactions.filter(kind=Transaction.Kind.EXPENSE)
    category_breakdown = [
        {
            'name': row['category__name'] or 'Uncategorized',
            'amount': row['total'],
            'share': (row['total'] * Decimal('100') / totals[Transaction.Kind.EXPENSE])
            if totals[Transaction.Kind.EXPENSE]
            else ZERO,
        }
        for row in expense_transactions.values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    ]

    scope = options.get('report_scope', 'all')
    report_transactions = period_transactions
    if scope in (Transaction.Kind.INCOME, Transaction.Kind.EXPENSE):
        report_transactions = report_transactions.filter(kind=scope)
    report_transactions = list(report_transactions.order_by('date', 'created_at'))

    if period_start and period_end:
        period_label = f'{period_start.strftime("%d %b %Y")} - {period_end.strftime("%d %b %Y")}'
    else:
        period_label = 'Complete transaction history'
    if options['period'] == 'monthly':
        period_label = date(options['year'], int(options['month']), 1).strftime('%B %Y')
    elif options['period'] == 'yearly':
        period_label = str(options['year'])
    elif options['period'] == 'history':
        period_label = f'Complete transaction history through {today.strftime("%d %b %Y")}'

    subscriptions = list(
        Subscription.objects.filter(user=user, is_active=True).order_by('next_renewal_date', 'name')
    )
    subscription_monthly_total = sum(
        (_monthly_subscription_cost(subscription) for subscription in subscriptions), ZERO
    ).quantize(Decimal('0.01'))

    goals = list(Goal.objects.filter(user=user, is_active=True).order_by('target_date', 'name'))
    goal_target_total = sum((goal.target_amount for goal in goals), ZERO)
    goal_current_total = sum((goal.current_amount for goal in goals), ZERO)

    scope_labels = dict((key, label) for key, label in (
        ('all', 'All transactions'),
        (Transaction.Kind.INCOME, 'Income report'),
        (Transaction.Kind.EXPENSE, 'Expense report'),
    ))
    return StatementData(
        period_start=period_start,
        period_end=period_end,
        period_label=period_label,
        report_scope=scope,
        report_scope_label=scope_labels[scope],
        income_total=totals[Transaction.Kind.INCOME],
        expense_total=totals[Transaction.Kind.EXPENSE],
        investment_total=totals[Transaction.Kind.INVESTMENT],
        available_balance=available_balance,
        category_breakdown=category_breakdown,
        monthly_spending=_monthly_spending(expense_transactions, period_start, period_end, today),
        transactions=report_transactions,
        subscriptions=subscriptions,
        subscription_monthly_total=subscription_monthly_total,
        goals=goals,
        goal_target_total=goal_target_total,
        goal_current_total=goal_current_total,
    )
