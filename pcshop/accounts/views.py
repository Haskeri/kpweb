"""Представления приложения accounts.

Регистрация, вход, выход, редактирование профиля, смена пароля
и аналитический дашборд для менеджеров и администраторов.
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
)
from django.db.models import Count, F, Sum
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, TemplateView, UpdateView

from .forms import (
    BootstrapPasswordChangeForm,
    EmailAuthenticationForm,
    ProfileForm,
    RegisterForm,
)
from .permissions import StaffRequiredMixin


class RegisterView(CreateView):
    """Регистрация нового клиента."""

    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Регистрация прошла успешно. Добро пожаловать!')
        return response


class EmailLoginView(LoginView):
    """Вход по email + пароль."""

    authentication_form = EmailAuthenticationForm
    template_name = 'registration/login.html'
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    """Выход с сообщением и редиректом на главную."""

    next_page = reverse_lazy('home')


class ProfileView(LoginRequiredMixin, UpdateView):
    """Редактирование собственного профиля."""

    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Профиль успешно обновлён.')
        return super().form_valid(form)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Личный кабинет / рабочее место в зависимости от роли пользователя."""

    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        from django.db.models import Sum
        from orders.models import Order, OrderStatus
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_manager or user.is_admin_role or user.is_staff:
            ctx['recent_orders'] = (
                Order.objects
                .select_related('status', 'client')
                .order_by('-created_at')[:10]
            )
            # Быстрая статистика для рабочего места менеджера
            ctx['total_orders'] = Order.objects.count()
            ctx['new_orders_count'] = Order.objects.filter(status__code='new').count()
            ctx['today_orders_count'] = Order.objects.filter(
                created_at__date=timezone.now().date()
            ).count()
            ctx['total_revenue'] = (
                Order.objects.exclude(status__code='cancelled')
                .aggregate(v=Sum('total_sum'))['v'] or Decimal('0.00')
            )
        elif user.is_authenticated:
            ctx['client_orders'] = (
                user.orders
                .select_related('status')
                .order_by('-created_at')[:5]
            )
            ctx['total_orders_count'] = user.orders.count()
            ctx['total_spent'] = (
                user.orders
                .exclude(status__code='cancelled')
                .aggregate(v=Sum('total_sum'))['v'] or Decimal('0.00')
            )
        return ctx


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    form_class = BootstrapPasswordChangeForm
    template_name = 'registration/password_change_form.html'
    success_url = reverse_lazy('accounts:password_change_done')


class CustomPasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    template_name = 'registration/password_change_done.html'


class AnalyticsView(StaffRequiredMixin, TemplateView):
    """Аналитический дашборд для менеджеров и админов.

    Считает выручку, прибыль и популярные товары за выбранный период
    через агрегирующие методы Django ORM.
    """

    template_name = 'accounts/analytics.html'

    def get_context_data(self, **kwargs):
        # Локальный импорт во избежание циклических зависимостей.
        from catalog.models import Component
        from orders.models import Order, OrderItem

        ctx = super().get_context_data(**kwargs)

        days = int(self.request.GET.get('days', 30))
        days = max(1, min(days, 365))
        period_start = timezone.now() - timedelta(days=days)

        orders_qs = Order.objects.filter(
            created_at__gte=period_start,
        ).exclude(status__code='cancelled')

        items_qs = OrderItem.objects.filter(order__in=orders_qs).select_related('component')

        # Выручка и прибыль
        agg = items_qs.aggregate(
            revenue=Sum(F('unit_price') * F('quantity')),
            cost=Sum(F('component__purchase_price') * F('quantity')),
            count=Count('order', distinct=True),
        )
        revenue = agg['revenue'] or Decimal('0.00')
        cost = agg['cost'] or Decimal('0.00')

        ctx['period_days'] = days
        ctx['orders_count'] = agg['count'] or 0
        ctx['revenue'] = revenue
        ctx['cost'] = cost
        ctx['profit'] = revenue - cost
        ctx['avg_order'] = (revenue / agg['count']) if agg['count'] else Decimal('0.00')

        # Топ-10 товаров
        ctx['top_components'] = (
            items_qs.values('component__title', 'component__brand')
            .annotate(
                qty=Sum('quantity'),
                revenue=Sum(F('unit_price') * F('quantity')),
            )
            .order_by('-qty')[:10]
        )

        # Остатки и низкие остатки
        ctx['low_stock'] = (
            Component.objects.filter(stock__lte=Component.LOW_STOCK_THRESHOLD, is_active=True)
            .select_related('category')
            .order_by('stock')[:15]
        )
        ctx['out_of_stock_count'] = Component.objects.filter(stock=0, is_active=True).count()

        return ctx
