"""Представления приложения builds.

Публичный список готовых сборок, детальная страница, менеджерский CRUD
с inline-редактированием состава сборки, и интерактивный конфигуратор
сборки ПК с проверкой совместимости комплектующих.
"""

import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import DeleteView, DetailView, ListView, TemplateView, View

from accounts.permissions import StaffRequiredMixin
from catalog.models import Category, Component

from .forms import BuildForm, BuildItemFormSet
from .models import Build, BuildItem


# Порядок шагов конфигуратора и соответствие slug-категориям из БД.
CONFIGURATOR_STEPS = [
    {'key': 'cpu',         'slug': 'cpu',         'title': 'Процессор',         'icon': 'cpu-fill',         'required': True},
    {'key': 'motherboard', 'slug': 'motherboards','title': 'Материнская плата', 'icon': 'motherboard-fill', 'required': True},
    {'key': 'ram',         'slug': 'ram',         'title': 'Оперативная память','icon': 'memory',           'required': True},
    {'key': 'storage',     'slug': 'storage',     'title': 'Накопитель',        'icon': 'device-hdd-fill',  'required': True},
    {'key': 'gpu',         'slug': 'gpu',         'title': 'Видеокарта',        'icon': 'gpu-card',         'required': False},
    {'key': 'psu',         'slug': 'psu',         'title': 'Блок питания',      'icon': 'lightning-charge-fill', 'required': True},
    {'key': 'case',        'slug': 'cases',       'title': 'Корпус',            'icon': 'box-seam-fill',    'required': True},
    {'key': 'cooling',     'slug': 'cooling',     'title': 'Охлаждение',        'icon': 'wind',             'required': False},
]


class BuildListView(ListView):
    """Публичный список готовых сборок."""

    template_name = 'builds/build_list.html'
    context_object_name = 'builds'
    paginate_by = 12

    def get_queryset(self):
        return (
            Build.objects.filter(is_template=True, is_active=True)
            .prefetch_related('items__component')
            .order_by('-created_at')
        )


class BuildDetailView(DetailView):
    """Страница сборки с составом."""

    template_name = 'builds/build_detail.html'
    context_object_name = 'build'
    model = Build

    def get_queryset(self):
        return Build.objects.prefetch_related('items__component__category')


# ---------------------------------------------------------------------------
# Менеджерский CRUD
# ---------------------------------------------------------------------------

class BuildManageListView(StaffRequiredMixin, ListView):
    """Управление сборками."""

    template_name = 'builds/manage_builds.html'
    context_object_name = 'builds'
    paginate_by = 30

    def get_queryset(self):
        return Build.objects.prefetch_related('items').order_by('-created_at')


class BuildEditView(StaffRequiredMixin, View):
    """Создание и редактирование сборки с inline-формой позиций."""

    template_name = 'builds/build_form.html'

    def get_object(self, pk):
        return get_object_or_404(Build, pk=pk) if pk else None

    def get(self, request, pk=None):
        build = self.get_object(pk)
        form = BuildForm(instance=build)
        formset = BuildItemFormSet(instance=build)
        return render(request, self.template_name, {
            'form': form, 'formset': formset, 'build': build,
        })

    def post(self, request, pk=None):
        build = self.get_object(pk)
        form = BuildForm(request.POST, instance=build)
        formset = BuildItemFormSet(request.POST, instance=build)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                instance = form.save(commit=False)
                if not instance.pk:
                    instance.created_by = request.user
                instance.save()
                formset.instance = instance
                formset.save()
            messages.success(request, f'Сборка «{instance.title}» сохранена.')
            return redirect('builds:manage')
        return render(request, self.template_name, {
            'form': form, 'formset': formset, 'build': build,
        })


class BuildDeleteView(StaffRequiredMixin, DeleteView):
    model = Build
    template_name = 'builds/build_confirm_delete.html'
    success_url = reverse_lazy('builds:manage')

    def form_valid(self, form):
        title = str(self.object)
        response = super().form_valid(form)
        messages.warning(self.request, f'Сборка «{title}» удалена.')
        return response


# ---------------------------------------------------------------------------
# Конфигуратор сборки ПК
# ---------------------------------------------------------------------------

def _component_to_dict(c: Component) -> dict:
    """Сериализация комплектующего для frontend конфигуратора."""
    return {
        'id': c.pk,
        'title': c.title,
        'brand': c.brand,
        'model': c.model,
        'category': c.category.slug,
        'category_title': c.category.title,
        'price': float(c.sale_price),
        'stock': c.stock,
        'image': c.image.url if c.image else None,
        'specs': c.specs or {},
    }


class ConfiguratorView(TemplateView):
    """Главная страница конфигуратора."""

    template_name = 'builds/configurator.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Собираем комплектующие, сгруппированные по slug категории
        components_by_slug = {}
        slugs = [step['slug'] for step in CONFIGURATOR_STEPS]
        components = (
            Component.objects
            .filter(is_active=True, category__slug__in=slugs, stock__gt=0)
            .select_related('category')
            .order_by('sale_price')
        )
        for c in components:
            components_by_slug.setdefault(c.category.slug, []).append(_component_to_dict(c))

        # Для каждого шага — данные шага + список комплектующих
        steps_data = []
        for step in CONFIGURATOR_STEPS:
            steps_data.append({
                **step,
                'components': components_by_slug.get(step['slug'], []),
            })

        ctx['steps_data'] = steps_data   # Python-объект, json_script сам сериализует
        ctx['steps'] = CONFIGURATOR_STEPS
        return ctx


@require_POST
@login_required
def configurator_save(request):
    """Сохраняет сборку, собранную в конфигураторе, и опционально кладёт в корзину."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Некорректный формат данных'}, status=400)

    selection = payload.get('selection') or {}      # { 'cpu': id, 'gpu': id, ... }
    title = (payload.get('title') or 'Моя сборка').strip()[:200]
    add_to_cart = bool(payload.get('add_to_cart'))

    component_ids = [int(v) for v in selection.values() if v]
    if not component_ids:
        return JsonResponse({'ok': False, 'error': 'Не выбрано ни одного комплектующего'}, status=400)

    components = list(Component.objects.filter(pk__in=component_ids, is_active=True))
    if len(components) != len(component_ids):
        return JsonResponse({'ok': False, 'error': 'Некоторые позиции недоступны'}, status=400)

    with transaction.atomic():
        build = Build.objects.create(
            title=title,
            description='Сборка, созданная в конфигураторе',
            is_template=False,
            is_active=True,
            created_by=request.user,
        )
        BuildItem.objects.bulk_create([
            BuildItem(build=build, component=c, quantity=1) for c in components
        ])

    response = {
        'ok': True,
        'build_id': build.pk,
        'total': float(build.total_price),
        'url': reverse('builds:detail', args=[build.pk]),
    }

    if add_to_cart:
        from orders.cart import Cart
        cart = Cart(request)
        cart.add_build(build.pk, 1)
        response['cart_url'] = reverse('orders:cart')

    return JsonResponse(response)
