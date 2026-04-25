"""Общие представления уровня проекта (главная страница)."""

from django.db.models import Count, Q
from django.views.generic import TemplateView

from builds.models import Build
from catalog.models import Category, Component


class HomeView(TemplateView):
    """Главная страница магазина."""

    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.annotate(
            component_count=Count('components', filter=Q(components__is_active=True))
        ).all()[:8]
        # prefetch_related('items__component') исключает N+1 при вызове total_price/items_count
        ctx['featured_builds'] = (
            Build.objects
            .filter(is_template=True, is_active=True)
            .prefetch_related('items__component')
            .order_by('-created_at')[:6]
        )
        # Новинки — последние 8 добавленных активных товаров
        ctx['new_components'] = (
            Component.objects
            .filter(is_active=True, stock__gt=0)
            .select_related('category')
            .order_by('-created_at')[:8]
        )
        return ctx
