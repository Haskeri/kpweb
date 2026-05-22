"""URL-маршруты приложения builds."""

from django.urls import path

from . import views

app_name = 'builds'

urlpatterns = [
    # Публичная часть
    path('', views.BuildListView.as_view(), name='list'),
    path('configure/', views.ConfiguratorView.as_view(), name='configure'),
    path('configure/save/', views.configurator_save, name='configure_save'),
    path('<int:pk>/', views.BuildDetailView.as_view(), name='detail'),

    # Менеджерское управление
    path('manage/', views.BuildManageListView.as_view(), name='manage'),
    path('manage/new/', views.BuildEditView.as_view(), name='create'),
    path('manage/<int:pk>/edit/', views.BuildEditView.as_view(), name='edit'),
    path('manage/<int:pk>/delete/', views.BuildDeleteView.as_view(), name='delete'),
]
