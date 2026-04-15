"""URL-маршруты проекта pcshop."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from .views import HomeView

admin.site.site_header = 'pcshop — административная панель'
admin.site.site_title = 'pcshop admin'
admin.site.index_title = 'Управление магазином'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),

    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('catalog/', include('catalog.urls', namespace='catalog')),
    path('builds/', include('builds.urls', namespace='builds')),
    path('orders/', include('orders.urls', namespace='orders')),

    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
