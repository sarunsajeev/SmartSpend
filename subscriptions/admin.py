from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'amount', 'billing_cycle', 'next_renewal_date', 'is_active')
    list_filter = ('billing_cycle', 'is_active', 'next_renewal_date')
    search_fields = ('name', 'user__username')
    autocomplete_fields = ('user',)
    list_select_related = ('user',)
    date_hierarchy = 'next_renewal_date'
    readonly_fields = ('created_at',)
