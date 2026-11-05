from django.urls import path

from . import views

app_name = 'budgets'

urlpatterns = [
    path('', views.goal_list, name='goals'),
    path('add/', views.goal_create, name='create'),
    path('<int:pk>/edit/', views.goal_update, name='update'),
    path('<int:pk>/delete/', views.goal_delete, name='delete'),
]
