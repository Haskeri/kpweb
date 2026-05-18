"""Представления приложения catalog.

Публичный каталог (список/деталь), менеджерский CRUD для комплектующих
и импорт/экспорт в формате CSV.
"""

import csv
import io
import json

from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from accounts.permissions import StaffRequiredMixin

from .forms import CatalogFilterForm, ComponentForm
from .models import Category, Component

PAGE_SIZE = 12


class CatalogListView(ListView):
    """Публичный каталог комплектующих с фильтрами."""

    model = Component
    template_name = 'catalog/component_list.html'
    context_object_name = 'components'
    paginate_by = PAGE_SIZE

    def get_queryset(self):
        qs = Component.objects.filter(is_active=True).select_related('category')
        self.filter_form = CatalogFilterForm(self.request.GET or None)
        if self.filter_form.is_valid():
            cd = self.filter_form.cleaned_data
            if cd.get('q'):
                qs = qs.filter(Q(title__icontains=cd['q']) | Q(brand__icontains=cd['q']))
            if cd.get('category'):
                qs = qs.filter(category=cd['category'])
            if cd.get('brand'):
                qs = qs.filter(brand__icontains=cd['brand'])
            if cd.get('min_price') is not None:
                qs = qs.filter(sale_price__gte=cd['min_price'])
            if cd.get('max_price') is not None:
                qs = qs.filter(sale_price__lte=cd['max_price'])
            if cd.get('only_in_stock'):
                qs = qs.filter(stock__gt=0)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_form'] = self.filter_form
        ctx['categories'] = Category.objects.all()
        return ctx


class ComponentDetailView(DetailView):
    """Страница карточки товара."""

    model = Component
    template_name = 'catalog/component_detail.html'
    context_object_name = 'component'

    def get_queryset(self):
        return Component.objects.filter(is_active=True).select_related('category')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Похожие товары из той же категории (исключая текущий)
        ctx['related'] = (
            Component.objects
            .filter(is_active=True, category=self.object.category, stock__gt=0)
            .exclude(pk=self.object.pk)
            .select_related('category')
            .order_by('sale_price')[:4]
        )
        return ctx


# ---------------------------------------------------------------------------
# Менеджерский CRUD
# ---------------------------------------------------------------------------

class ComponentManageListView(StaffRequiredMixin, ListView):
    """Управление каталогом для менеджера."""

    model = Component
    template_name = 'catalog/manage_components.html'
    context_object_name = 'components'
    paginate_by = 30

    def get_queryset(self):
        qs = Component.objects.select_related('category').order_by('category__title', 'title')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(brand__icontains=q) | Q(model__icontains=q))
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category_id=category)
        if self.request.GET.get('low'):
            qs = qs.filter(stock__lte=Component.LOW_STOCK_THRESHOLD)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.all()
        ctx['low_threshold'] = Component.LOW_STOCK_THRESHOLD
        ctx['query'] = self.request.GET.get('q', '')
        return ctx


class ComponentCreateView(StaffRequiredMixin, CreateView):
    model = Component
    form_class = ComponentForm
    template_name = 'catalog/component_form.html'
    success_url = reverse_lazy('catalog:manage')

    def form_valid(self, form):
        messages.success(self.request, f'Товар «{form.instance}» создан.')
        return super().form_valid(form)


class ComponentUpdateView(StaffRequiredMixin, UpdateView):
    model = Component
    form_class = ComponentForm
    template_name = 'catalog/component_form.html'
    success_url = reverse_lazy('catalog:manage')

    def form_valid(self, form):
        messages.success(self.request, f'Товар «{form.instance}» обновлён.')
        return super().form_valid(form)


class ComponentDeleteView(StaffRequiredMixin, DeleteView):
    model = Component
    template_name = 'catalog/component_confirm_delete.html'
    success_url = reverse_lazy('catalog:manage')

    def form_valid(self, form):
        title = str(self.object)
        response = super().form_valid(form)
        messages.warning(self.request, f'Товар «{title}» удалён.')
        return response


# ---------------------------------------------------------------------------
# Импорт / экспорт CSV
# ---------------------------------------------------------------------------

class ComponentExportView(StaffRequiredMixin, View):
    """Выгрузка всего каталога в CSV (разделитель «;»)."""

    HEADERS = ['id', 'category', 'title', 'brand', 'model', 'specs',
               'purchase_price', 'sale_price', 'stock', 'is_active']

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="catalog.csv"'
        response.write('﻿')  # BOM для корректного открытия в Excel
        writer = csv.writer(response, delimiter=';')
        writer.writerow(self.HEADERS)
        for c in Component.objects.select_related('category').order_by('category__title', 'title'):
            writer.writerow([
                c.pk, c.category.slug, c.title, c.brand, c.model,
                json.dumps(c.specs, ensure_ascii=False),
                c.purchase_price, c.sale_price, c.stock,
                '1' if c.is_active else '0',
            ])
        return response


from django import forms as djforms


class CSVImportForm(djforms.Form):
    csv_file = djforms.FileField(
        label='CSV-файл',
        help_text='Кодировка UTF-8, разделитель «;».',
        widget=djforms.ClearableFileInput(attrs={'class': 'form-control'}),
    )


class ComponentImportView(StaffRequiredMixin, View):
    """Загрузка каталога из CSV."""

    template_name = 'catalog/import_components.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': CSVImportForm()})

    def post(self, request, *args, **kwargs):
        form = CSVImportForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        file = form.cleaned_data['csv_file']
        # Поддержка BOM из Excel
        raw = file.read().decode('utf-8-sig', errors='replace')
        reader = csv.DictReader(io.StringIO(raw), delimiter=';')

        created = updated = skipped = 0
        errors = []

        for row_num, row in enumerate(reader, start=2):  # 2 потому что 1 — заголовок
            slug = (row.get('category') or '').strip().lower()
            title = (row.get('title') or '').strip()
            if not slug or not title:
                errors.append(f'Строка {row_num}: пустая категория или название.')
                skipped += 1
                continue
            try:
                category = Category.objects.get(slug=slug)
            except Category.DoesNotExist:
                category, _ = Category.objects.get_or_create(
                    slug=slug,
                    defaults={'title': slug.upper()},
                )

            specs_raw = (row.get('specs') or '').strip()
            try:
                specs = json.loads(specs_raw) if specs_raw else {}
            except json.JSONDecodeError:
                specs = {}

            defaults = {
                'category': category,
                'brand': (row.get('brand') or '').strip(),
                'model': (row.get('model') or '').strip(),
                'specs': specs,
                'purchase_price': row.get('purchase_price') or 0,
                'sale_price': row.get('sale_price') or 0,
                'stock': int(row.get('stock') or 0),
                'is_active': (row.get('is_active') or '1').strip() in ('1', 'true', 'True', 'yes'),
            }

            obj, created_flag = Component.objects.update_or_create(
                title=title,
                defaults=defaults,
            )
            if created_flag:
                created += 1
            else:
                updated += 1

        messages.success(
            request,
            f'Импорт завершён: создано {created}, обновлено {updated}, пропущено {skipped}.',
        )
        for err in errors[:10]:
            messages.warning(request, err)
        return redirect('catalog:manage')
