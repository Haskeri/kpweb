"""URL-маршруты приложения catalog."""

from django.urls import path

from . import views

app_name = 'catalog'

urlpatterns = [
    # Публичная часть
    path('', views.CatalogListView.as_view(), name='list'),
    path('item/<int:pk>/', views.ComponentDetailView.as_view(), name='detail'),

    # Менеджерское управление (export/import — до шаблонов с <int:pk>)
    path('manage/', views.ComponentManageListView.as_view(), name='manage'),
    path('manage/new/', views.ComponentCreateView.as_view(), name='create'),
    path('manage/export/', views.ComponentExportView.as_view(), name='export'),
    path('manage/import/', views.ComponentImportView.as_view(), name='import'),
    path('manage/<int:pk>/edit/', views.ComponentUpdateView.as_view(), name='edit'),
    path('manage/<int:pk>/delete/', views.ComponentDeleteView.as_view(), name='delete'),
]
