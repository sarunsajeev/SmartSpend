from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.statement_index, name='index'),
    path('download/', views.statement_download, name='download'),
]
