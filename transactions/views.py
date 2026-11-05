from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CategoryForm, TransactionFilterForm, TransactionForm
from .models import Category, Transaction


def _transaction_list(request, kind=None, title='All transactions'):
    filter_form = TransactionFilterForm(request.GET or None, user=request.user)
    transactions = Transaction.objects.filter(user=request.user).select_related('category')
    if kind:
        transactions = transactions.filter(kind=kind)

    if filter_form.is_valid():
        filters = filter_form.cleaned_data
        query = filters.get('q')
        selected_kind = filters.get('kind')
        category = filters.get('category')
        date_from = filters.get('date_from')
        date_to = filters.get('date_to')

        if query:
            transactions = transactions.filter(
                Q(description__icontains=query)
                | Q(subcategory__icontains=query)
                | Q(category__name__icontains=query)
            )
        if selected_kind and not kind:
            transactions = transactions.filter(kind=selected_kind)
        if category:
            transactions = transactions.filter(category=category)
        if date_from:
            transactions = transactions.filter(date__gte=date_from)
        if date_to:
            transactions = transactions.filter(date__lte=date_to)

        sort = filters.get('sort') or 'date_desc'
    else:
        sort = request.GET.get('sort') if request.GET.get('sort') in {
            'date_desc', 'date_asc', 'amount_desc', 'amount_asc'
        } else 'date_desc'

    sort_fields = {
        'date_desc': ('-date', '-created_at'),
        'date_asc': ('date', 'created_at'),
        'amount_desc': ('-amount', '-date'),
        'amount_asc': ('amount', '-date'),
    }
    transactions = transactions.order_by(*sort_fields[sort])
    paginator = Paginator(transactions, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    pagination_parameters = request.GET.copy()
    pagination_parameters.pop('page', None)

    fixed_kind = kind
    mode_title = title
    return render(
        request,
        'transactions/list.html',
        {
            'transactions': page_obj.object_list,
            'page_obj': page_obj,
            'filter_form': filter_form,
            'query': request.GET.get('q', ''),
            'pagination_query': pagination_parameters.urlencode(),
            'page_title': mode_title,
            'page_heading': mode_title,
            'topbar_subtitle': 'Search, filter, and review your financial activity',
            'fixed_kind': fixed_kind,
            'today': timezone.localdate(),
            'now': timezone.localtime(),
        },
    )


@login_required
def expense_list(request):
    return _transaction_list(request, Transaction.Kind.EXPENSE, 'All Expenses')


@login_required
def all_transactions(request):
    return _transaction_list(request, title='All transactions')


@login_required
def income_list(request):
    return _transaction_list(request, Transaction.Kind.INCOME, 'Income')


@login_required
def investment_list(request):
    return _transaction_list(request, Transaction.Kind.INVESTMENT, 'Investments')


def _redirect_after_transaction(kind):
    if kind == Transaction.Kind.INCOME:
        return redirect('transactions:income')
    if kind == Transaction.Kind.INVESTMENT:
        return redirect('transactions:investments')
    return redirect('transactions:list')


@login_required
def transaction_create(request, kind):
    if kind not in (Transaction.Kind.INCOME, Transaction.Kind.EXPENSE):
        return redirect('transactions:all')
    form = TransactionForm(
        request.POST or None,
        user=request.user,
        kind=kind,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{form.instance.get_kind_display()} was added.')
        return _redirect_after_transaction(kind)
    if request.method == 'POST':
        messages.error(request, 'Please correct the highlighted fields.')
    title = 'Add income' if kind == Transaction.Kind.INCOME else 'Add expense'
    return render(
        request,
        'transactions/form.html',
        {
            'form': form,
            'page_title': title,
            'page_heading': title,
            'topbar_subtitle': 'Enter a financial record for your account',
            'kind': kind,
            'today': timezone.localdate(),
            'now': timezone.localtime(),
        },
    )


@login_required
def transaction_update(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    form = TransactionForm(
        request.POST or None,
        instance=transaction,
        user=request.user,
        kind=transaction.kind,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your transaction was updated.')
        return _redirect_after_transaction(transaction.kind)
    if request.method == 'POST':
        messages.error(request, 'Please correct the highlighted fields.')
    return render(
        request,
        'transactions/form.html',
        {
            'form': form,
            'transaction': transaction,
            'page_title': 'Edit transaction',
            'page_heading': 'Edit transaction',
            'topbar_subtitle': 'Update this record in your account',
            'kind': transaction.kind,
            'today': timezone.localdate(),
            'now': timezone.localtime(),
        },
    )


@login_required
def transaction_detail(request, pk):
    transaction = get_object_or_404(
        Transaction.objects.select_related('category'),
        pk=pk,
        user=request.user,
    )
    return render(
        request,
        'transactions/detail.html',
        {
            'transaction': transaction,
            'page_heading': 'Transaction details',
            'topbar_subtitle': 'Review this financial record',
            'today': timezone.localdate(),
            'now': timezone.localtime(),
        },
    )


@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        kind = transaction.kind
        transaction.delete()
        messages.success(request, 'The transaction was deleted.')
        return _redirect_after_transaction(kind)
    return render(
        request,
        'transactions/confirm_delete.html',
        {
            'transaction': transaction,
            'page_heading': 'Delete transaction',
            'topbar_subtitle': 'Confirm this change to your records',
            'today': timezone.localdate(),
            'now': timezone.localtime(),
        },
    )


@login_required
def category_list(request):
    categories = (
        Category.objects.filter(user=request.user)
        .annotate(transaction_count=Count('transactions', filter=Q(transactions__user=request.user)))
        .order_by('kind', 'name')
    )
    return render(
        request,
        'transactions/categories.html',
        {
            'categories': categories,
            'page_heading': 'Categories',
            'topbar_subtitle': 'Organize your income, expenses, and investments',
            'today': timezone.localdate(),
            'now': timezone.localtime(),
        },
    )


@login_required
def category_create(request):
    form = CategoryForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        category = form.save(commit=False)
        category.user = request.user
        category.save()
        messages.success(request, 'Your category was created.')
        return redirect('transactions:categories')
    if request.method == 'POST':
        messages.error(request, 'Please correct the highlighted fields.')
    return render(
        request,
        'transactions/category_form.html',
        {
            'form': form,
            'page_heading': 'Add category',
            'topbar_subtitle': 'Create a category for your account',
            'today': timezone.localdate(),
            'now': timezone.localtime(),
        },
    )


@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    form = CategoryForm(request.POST or None, instance=category, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your category was updated.')
        return redirect('transactions:categories')
    if request.method == 'POST':
        messages.error(request, 'Please correct the highlighted fields.')
    return render(
        request,
        'transactions/category_form.html',
        {
            'form': form,
            'category': category,
            'page_heading': 'Edit category',
            'topbar_subtitle': 'Update this category for your account',
            'today': timezone.localdate(),
            'now': timezone.localtime(),
        },
    )


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        try:
            category.delete()
        except ProtectedError:
            messages.error(request, 'This category is used by transactions. Edit it instead of deleting it.')
        else:
            messages.success(request, 'Your category was deleted.')
        return redirect('transactions:categories')
    return render(
        request,
        'transactions/category_confirm_delete.html',
        {
            'category': category,
            'page_heading': 'Delete category',
            'topbar_subtitle': 'Confirm this category change',
            'today': timezone.localdate(),
            'now': timezone.localtime(),
        },
    )
