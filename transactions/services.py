from .models import Category


DEFAULT_CATEGORIES = {
    Category.Kind.EXPENSE: (
        'Food',
        'Shopping',
        'Transport',
        'Entertainment',
        'Bills',
        'Healthcare',
        'Education',
        'Other',
    ),
    Category.Kind.INCOME: (
        'Salary',
        'Freelance',
        'Business',
        'Investments',
        'Gifts',
        'Other',
    ),
    Category.Kind.INVESTMENT: ('Investments',),
}


def create_default_categories(user):
    """Create the starter category set for a new user without duplicating rows."""
    for kind, names in DEFAULT_CATEGORIES.items():
        for name in names:
            Category.objects.get_or_create(user=user, name=name, kind=kind)
