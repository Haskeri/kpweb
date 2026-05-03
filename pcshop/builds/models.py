"""Модели приложения builds: сборки ПК и их состав.

Соответствует таблицам builds и build_items из подраздела 2.3
пояснительной записки.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models

from catalog.models import Component


class Build(models.Model):
    """Сборка ПК — готовая (template) или клиентская конфигурация."""

    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    is_template = models.BooleanField(
        'Готовая сборка',
        default=False,
        help_text='Если True — сборка отображается в публичном каталоге.',
    )
    is_active = models.BooleanField('Опубликована', default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='builds',
        verbose_name='Создал',
    )
    components = models.ManyToManyField(
        Component,
        through='BuildItem',
        related_name='builds',
        verbose_name='Комплектующие',
    )
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        verbose_name = 'Сборка ПК'
        verbose_name_plural = 'Сборки ПК'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title

    @property
    def total_price(self) -> Decimal:
        """Сумма стоимости всех позиций сборки по продажным ценам."""
        return sum(
            (item.subtotal for item in self.items.select_related('component').all()),
            Decimal('0.00'),
        )

    @property
    def items_count(self) -> int:
        return self.items.count()


class BuildItem(models.Model):
    """Состав сборки: связь Build ↔ Component с количеством."""

    build = models.ForeignKey(
        Build,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Сборка',
    )
    component = models.ForeignKey(
        Component,
        on_delete=models.PROTECT,
        related_name='build_items',
        verbose_name='Комплектующее',
    )
    quantity = models.PositiveIntegerField('Количество', default=1)

    class Meta:
        verbose_name = 'Позиция сборки'
        verbose_name_plural = 'Позиции сборок'
        constraints = [
            models.UniqueConstraint(
                fields=['build', 'component'],
                name='unique_component_per_build',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.component} × {self.quantity}'

    @property
    def subtotal(self) -> Decimal:
        return self.component.sale_price * self.quantity
