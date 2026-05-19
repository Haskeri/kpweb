"""URL-маршруты приложения orders."""

from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    # Корзина
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/add-build/<int:pk>/', views.cart_add_build, name='cart_add_build'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('cart/remove-component/<int:pk>/', views.cart_remove_component, name='cart_remove_component'),
    path('cart/remove-build/<int:pk>/', views.cart_remove_build, name='cart_remove_build'),

    # Оформление заказа и ЛК клиента
    path('checkout/', views.checkout, name='checkout'),
    path('', views.OrderListView.as_view(), name='list'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='detail'),

    # Менеджерское управление
    path('manage/', views.OrderManageListView.as_view(), name='manage'),
    path('manage/<int:pk>/status/', views.manage_change_status, name='manage_status'),
    path('manage/export/', views.OrderExportView.as_view(), name='export'),
]
