from django.contrib import admin

from .models import Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'user', 'created_at')
    list_filter = ('kind', 'created_at')
    search_fields = ('name', 'user__username')
    autocomplete_fields = ('user',)
    list_select_related = ('user',)
    date_hierarchy = 'created_at'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('description', 'kind', 'amount', 'date', 'category', 'subcategory', 'payment_method', 'user')
    list_filter = ('kind', 'payment_method', 'date')
    search_fields = ('description', 'subcategory', 'user__username', 'category__name')
    autocomplete_fields = ('user', 'category')
    date_hierarchy = 'date'
    list_select_related = ('user', 'category')
    readonly_fields = ('created_at', 'updated_at')
