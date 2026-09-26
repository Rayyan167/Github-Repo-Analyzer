from django.urls import path

from . import views

app_name = 'analyzer'

urlpatterns = [
    path('', views.home, name='home'),
    path('report/<int:pk>/', views.dashboard, name='dashboard'),
    path('history/', views.history, name='history'),
]
