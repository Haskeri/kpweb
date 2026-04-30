"""Модели приложения catalog: категории и комплектующие.

Соответствует словарю данных таблиц categories и components,
описанному в подразделе 2.3 пояснительной записки.
"""

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """Категория комплектующих (например, «Процессоры», «Видеокарты»)."""

    title = models.CharField('Название', max_length=100, unique=True)
    slug = models.SlugField('Слаг', max_length=120, unique=True, blank=True)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['title']

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=False) or f'category-{self.pk or ""}'
        super().save(*args, **kwargs)


class Component(models.Model):
    """Комплектующее (товарная позиция в каталоге)."""

    LOW_STOCK_THRESHOLD = 3

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='components',
        verbose_name='Категория',
    )
    title = models.CharField('Наименование', max_length=200)
    brand = models.CharField('Бренд', max_length=100, blank=True)
    model = models.CharField('Модель', max_length=100, blank=True)
    specs = models.JSONField(
        'Характеристики',
        default=dict,
        blank=True,
        help_text='Произвольные технические параметры в формате «ключ — значение».',
    )
    purchase_price = models.DecimalField(
        'Закупочная цена',
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    sale_price = models.DecimalField(
        'Продажная цена',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    stock = models.PositiveIntegerField('Остаток на складе', default=0)
    image = models.ImageField('Изображение', upload_to='components/', blank=True, null=True)
    is_active = models.BooleanField('Активно', default=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True, null=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True, null=True)

    class Meta:
        verbose_name = 'Комплектующее'
        verbose_name_plural = 'Комплектующие'
        ordering = ['category__title', 'title']
        indexes = [
            models.Index(fields=['category', 'brand']),
            models.Index(fields=['stock']),
        ]

    def __str__(self) -> str:
        parts = [self.brand, self.model, self.title]
        return ' '.join(part for part in parts if part).strip() or 'Комплектующее'

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    @property
    def is_low_stock(self) -> bool:
        return 0 < self.stock <= self.LOW_STOCK_THRESHOLD

    @property
    def margin(self):
        """Маржа в денежном выражении (продажная минус закупочная)."""
        return self.sale_price - self.purchase_price
