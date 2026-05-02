"""Модели приложения orders: заказы, позиции и справочник статусов.

Соответствует таблицам orders, order_items и order_statuses
из подраздела 2.3 пояснительной записки.
"""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from builds.models import Build
from catalog.models import Component


class OrderStatus(models.Model):
    """Справочник статусов заказа (новый, в работе, выполнен и т. д.)."""

    code = models.CharField('Код', max_length=20, unique=True)
    title = models.CharField('Название', max_length=100)
    color = models.CharField(
        'Цвет (hex)',
        max_length=7,
        default='#6c757d',
        help_text='Используется для подсветки бейджа статуса в интерфейсе.',
    )
    sort_order = models.PositiveSmallIntegerField('Порядок', default=0)
    is_terminal = models.BooleanField(
        'Финальный',
        default=False,
        help_text='Если True — заказ в этом статусе считается завершённым.',
    )

    class Meta:
        verbose_name = 'Статус заказа'
        verbose_name_plural = 'Статусы заказов'
        ordering = ['sort_order', 'title']

    def __str__(self) -> str:
        return self.title


class Order(models.Model):
    """Заказ клиента."""

    class PaymentMethod(models.TextChoices):
        CARD = 'card', 'Картой онлайн'
        CASH = 'cash', 'Наличные'
        SBP = 'sbp', 'СБП'

    class DeliveryMethod(models.TextChoices):
        PICKUP = 'pickup', 'Самовывоз'
        COURIER = 'courier', 'Курьер'

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Клиент',
    )
    build = models.ForeignKey(
        Build,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Сборка',
    )
    status = models.ForeignKey(
        OrderStatus,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Статус',
    )
    total_sum = models.DecimalField(
        'Сумма заказа, ₽',
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    payment_method = models.CharField(
        'Способ оплаты',
        max_length=20,
        choices=PaymentMethod.choices,
    )
    delivery_method = models.CharField(
        'Способ получения',
        max_length=20,
        choices=DeliveryMethod.choices,
        default=DeliveryMethod.PICKUP,
    )
    delivery_address = models.CharField('Адрес доставки', max_length=255, blank=True)
    comment = models.TextField('Комментарий клиента', blank=True)
    created_at = models.DateTimeField('Оформлен', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self) -> str:
        return f'Заказ №{self.pk} от {self.client}'

    def recalculate_total(self, save: bool = True) -> Decimal:
        """Пересчитывает total_sum по позициям заказа."""
        total = sum((item.subtotal for item in self.items.all()), Decimal('0.00'))
        self.total_sum = total
        if save:
            self.save(update_fields=['total_sum', 'updated_at'])
        return total


class OrderItem(models.Model):
    """Отдельная позиция заказа (комплектующее с количеством и ценой на момент покупки)."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ',
    )
    component = models.ForeignKey(
        Component,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='Комплектующее',
    )
    quantity = models.PositiveIntegerField('Количество', default=1)
    unit_price = models.DecimalField(
        'Цена за единицу, ₽',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказов'

    def __str__(self) -> str:
        return f'{self.component} × {self.quantity}'

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity
