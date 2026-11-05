from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    path('analytics/', views.analytics, name='analytics'),
    path('cards/', views.section_page, {'section': 'cards'}, name='cards'),
    path('insight/', views.section_page, {'section': 'insight'}, name='insight'),
    path('settings/', views.section_page, {'section': 'settings'}, name='settings'),
    path('help/', views.section_page, {'section': 'help'}, name='help'),
    path('support/', views.section_page, {'section': 'support'}, name='support'),
]
