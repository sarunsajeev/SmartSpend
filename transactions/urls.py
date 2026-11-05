from django.urls import path

from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.expense_list, name='list'),
    path('all/', views.all_transactions, name='all'),
    path('income/', views.income_list, name='income'),
    path('income/add/', views.transaction_create, {'kind': 'income'}, name='income_create'),
    path('expenses/add/', views.transaction_create, {'kind': 'expense'}, name='expense_create'),
    path('investments/', views.investment_list, name='investments'),
    path('categories/', views.category_list, name='categories'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('<int:pk>/edit/', views.transaction_update, name='update'),
    path('<int:pk>/delete/', views.transaction_delete, name='delete'),
    path('<int:pk>/', views.transaction_detail, name='detail'),
]
