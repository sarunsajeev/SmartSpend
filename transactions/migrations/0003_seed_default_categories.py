from django.conf import settings
from django.db import migrations


DEFAULT_CATEGORIES = {
    'expense': (
        'Food', 'Shopping', 'Transport', 'Entertainment',
        'Bills', 'Healthcare', 'Education', 'Other',
    ),
    'income': ('Salary', 'Freelance', 'Business', 'Investments', 'Gifts', 'Other'),
    'investment': ('Investments',),
}


def seed_existing_users(apps, schema_editor):
    app_label, model_name = settings.AUTH_USER_MODEL.split('.')
    User = apps.get_model(app_label, model_name)
    Category = apps.get_model('transactions', 'Category')
    database = schema_editor.connection.alias

    for user_id in User.objects.using(database).values_list('pk', flat=True).iterator():
        for kind, names in DEFAULT_CATEGORIES.items():
            for name in names:
                Category.objects.using(database).get_or_create(
                    user_id=user_id,
                    kind=kind,
                    name=name,
                )


class Migration(migrations.Migration):
    dependencies = [
        ('transactions', '0002_transaction_payment_method_transaction_subcategory'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(seed_existing_users, migrations.RunPython.noop),
    ]
