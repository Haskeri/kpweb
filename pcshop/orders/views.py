"""Представления приложения orders.

Корзина (session-based), оформление заказа, список заказов клиента,
управление заказами менеджера, выгрузка отчёта в CSV.
"""

import csv
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F, Sum, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, View

from accounts.permissions import StaffRequiredMixin
from builds.models import Build
from catalog.models import Component

from .cart import Cart
from .forms import CheckoutForm, OrderStatusForm
from .models import Order, OrderItem, OrderStatus


# ---------------------------------------------------------------------------
# Корзина
# ---------------------------------------------------------------------------

def cart_view(request):
    """Просмотр содержимого корзины."""
    cart = Cart(request)
    return render(request, 'orders/cart.html', {
        'component_lines': cart.component_lines(),
        'build_lines': cart.build_lines(),
        'total': cart.total(),
        'is_empty': cart.is_empty(),
    })


@require_POST
def cart_add(request):
    """Добавить комплектующее в корзину (по component_id из POST)."""
    component_id = request.POST.get('component_id')
    try:
        qty = max(1, int(request.POST.get('quantity', 1)))
    except (ValueError, TypeError):
        qty = 1
    if component_id:
        cart = Cart(request)
        cart.add_component(component_id, qty)
        messages.success(request, 'Товар добавлен в корзину.')
    return redirect(request.META.get('HTTP_REFERER') or reverse('catalog:list'))


@require_POST
def cart_add_build(request, pk):
    """Добавить сборку в корзину."""
    get_object_or_404(Build, pk=pk, is_active=True)
    cart = Cart(request)
    cart.add_build(pk, 1)
    messages.success(request, 'Сборка добавлена в корзину.')
    return redirect('orders:cart')


@require_POST
def cart_update(request):
    """Изменить количество позиции в корзине."""
    cart = Cart(request)
    component_id = request.POST.get('component_id')
    if component_id:
        qty = int(request.POST.get('quantity', 0))
        cart.set_component_qty(int(component_id), qty)
    return redirect('orders:cart')


@require_POST
def cart_remove_component(request, pk):
    Cart(request).remove_component(pk)
    return redirect('orders:cart')


@require_POST
def cart_remove_build(request, pk):
    Cart(request).remove_build(pk)
    return redirect('orders:cart')


# ---------------------------------------------------------------------------
# Оформление заказа
# ---------------------------------------------------------------------------

@login_required
def checkout(request):
    """Оформление заказа из корзины."""
    cart = Cart(request)
    if cart.is_empty():
        messages.warning(request, 'Ваша корзина пуста.')
        return redirect('catalog:list')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = _create_order(cart, request.user, form)
            except ValueError as exc:
                messages.error(request, str(exc))
                return redirect('orders:cart')
            cart.clear()
            messages.success(request, f'Заказ №{order.pk} оформлен. Спасибо!')
            return redirect('orders:detail', pk=order.pk)
    else:
        form = CheckoutForm()

    return render(request, 'orders/checkout.html', {
        'form': form,
        'component_lines': cart.component_lines(),
        'build_lines': cart.build_lines(),
        'total': cart.total(),
    })


def _create_order(cart: Cart, user, form: CheckoutForm) -> Order:
    """Создаёт Order + OrderItem'ы атомарно, уменьшая остатки."""
    new_status = OrderStatus.objects.filter(code='new').first()
    if not new_status:
        new_status, _ = OrderStatus.objects.get_or_create(
            code='new',
            defaults={'title': 'Новый', 'color': '#1F3B73', 'sort_order': 10},
        )

    component_lines = cart.component_lines()
    build_lines = cart.build_lines()

    with transaction.atomic():
        # Проверка остатков
        stock_needs = {}
        for line in component_lines:
            stock_needs[line['component'].pk] = (
                stock_needs.get(line['component'].pk, 0) + line['quantity']
            )
        for line in build_lines:
            for item in line['build'].items.all():
                stock_needs[item.component.pk] = (
                    stock_needs.get(item.component.pk, 0)
                    + item.quantity * line['quantity']
                )

        for pk, need in stock_needs.items():
            comp = Component.objects.select_for_update().get(pk=pk)
            if comp.stock < need:
                raise ValueError(
                    f'Недостаточно товара «{comp}» на складе ({comp.stock} из {need}).'
                )

        # Создание заказа
        order = form.save(commit=False)
        order.client = user
        order.status = new_status
        order.total_sum = Decimal('0.00')
        # Если в корзине ровно одна сборка и нет отдельных товаров, сохраняем привязку
        if len(build_lines) == 1 and not component_lines:
            order.build = build_lines[0]['build']
        order.save()

        # Позиции заказа из комплектующих
        items_to_create = []
        for line in component_lines:
            items_to_create.append(OrderItem(
                order=order,
                component=line['component'],
                quantity=line['quantity'],
                unit_price=line['component'].sale_price,
            ))

        # Позиции заказа из состава сборок
        for line in build_lines:
            for item in line['build'].items.all():
                items_to_create.append(OrderItem(
                    order=order,
                    component=item.component,
                    quantity=item.quantity * line['quantity'],
                    unit_price=item.component.sale_price,
                ))

        OrderItem.objects.bulk_create(items_to_create)

        # Уменьшение остатков через F() — атомарная операция без race condition
        for pk, need in stock_needs.items():
            Component.objects.filter(pk=pk).update(stock=F('stock') - need)

        order.recalculate_total()
    return order


# ---------------------------------------------------------------------------
# Просмотр заказов
# ---------------------------------------------------------------------------

class OrderListView(LoginRequiredMixin, ListView):
    """Список заказов клиента (свои заказы)."""

    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        return (
            Order.objects.filter(client=self.request.user)
            .select_related('status', 'build')
            .order_by('-created_at')
        )


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Подробная информация о заказе."""

    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    model = Order

    def get_queryset(self):
        qs = Order.objects.select_related('status', 'client', 'build').prefetch_related('items__component')
        user = self.request.user
        if user.is_authenticated and (user.is_staff or user.is_manager or user.is_admin_role):
            return qs
        return qs.filter(client=user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['all_statuses'] = OrderStatus.objects.all()
        return ctx


# ---------------------------------------------------------------------------
# Менеджерский список заказов
# ---------------------------------------------------------------------------

class OrderManageListView(StaffRequiredMixin, ListView):
    template_name = 'orders/manage_orders.html'
    context_object_name = 'orders'
    paginate_by = 30

    def get_queryset(self):
        qs = (
            Order.objects.select_related('status', 'client', 'build')
            .order_by('-created_at')
        )
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status_id=status)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(client__email__icontains=q)
                | Q(client__full_name__icontains=q)
                | Q(pk__iexact=q if q.isdigit() else 0)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['statuses'] = OrderStatus.objects.all()
        return ctx


@require_POST
def manage_change_status(request, pk):
    """Менеджер меняет статус заказа."""
    user = request.user
    if not (user.is_authenticated and (user.is_superuser or user.is_staff or user.is_manager or user.is_admin_role)):
        return HttpResponse(status=403)
    order = get_object_or_404(Order, pk=pk)
    form = OrderStatusForm(request.POST, instance=order)
    if form.is_valid():
        form.save()
        messages.success(request, f'Статус заказа №{order.pk} изменён на «{order.status}».')
    return redirect('orders:manage')


# ---------------------------------------------------------------------------
# Выгрузка отчёта в CSV
# ---------------------------------------------------------------------------

class OrderExportView(StaffRequiredMixin, View):
    """Выгрузка заказов за период в CSV."""

    HEADERS = ['order_id', 'date', 'client_email', 'status',
               'total_sum', 'payment_method', 'delivery_method']

    def get(self, request):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="orders.csv"'
        response.write('﻿')  # BOM
        writer = csv.writer(response, delimiter=';')
        writer.writerow(self.HEADERS)
        qs = Order.objects.select_related('status', 'client').order_by('-created_at')
        date_from = request.GET.get('from')
        date_to = request.GET.get('to')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        for o in qs:
            writer.writerow([
                o.pk, o.created_at.strftime('%Y-%m-%d %H:%M'),
                o.client.email, o.status.title, o.total_sum,
                o.get_payment_method_display(), o.get_delivery_method_display(),
            ])
        return response
