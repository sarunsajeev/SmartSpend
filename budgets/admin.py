from django.contrib import admin

from .models import Goal


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'target_amount', 'current_amount', 'target_date', 'is_active')
    list_filter = ('is_active', 'target_date')
    search_fields = ('name', 'user__username')
    autocomplete_fields = ('user',)
    list_select_related = ('user',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
