from django.urls import path

from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.subscription_list, name='list'),
    path('add/', views.subscription_create, name='create'),
    path('<int:pk>/edit/', views.subscription_update, name='update'),
    path('<int:pk>/delete/', views.subscription_delete, name='delete'),
]
