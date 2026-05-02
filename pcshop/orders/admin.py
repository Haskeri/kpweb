from django.contrib import admin
from django.utils.html import format_html

from .models import Order, OrderItem, OrderStatus


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'sort_order', 'is_terminal', 'color_badge')
    list_editable = ('sort_order', 'is_terminal')
    search_fields = ('title', 'code')

    @admin.display(description='Цвет')
    def color_badge(self, obj: OrderStatus) -> str:
        return format_html(
            '<span style="display:inline-block;width:18px;height:18px;background:{};border-radius:3px;border:1px solid #ccc;"></span>'
            ' <code>{}</code>',
            obj.color,
            obj.color,
        )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ('component',)
    fields = ('component', 'quantity', 'unit_price', 'subtotal_display')
    readonly_fields = ('subtotal_display',)

    @admin.display(description='Подытог, ₽')
    def subtotal_display(self, obj: OrderItem) -> str:
        if obj.pk:
            return f'{obj.subtotal:.2f}'
        return '—'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'client',
        'status_badge',
        'total_sum',
        'payment_method',
        'delivery_method',
        'created_at',
    )
    list_filter = ('status', 'payment_method', 'delivery_method', 'created_at')
    search_fields = ('pk', 'client__email', 'client__full_name', 'comment')
    autocomplete_fields = ('client', 'build')
    readonly_fields = ('created_at', 'updated_at', 'total_sum')
    inlines = [OrderItemInline]
    fieldsets = (
        (None, {'fields': ('client', 'build', 'status')}),
        ('Оплата и доставка', {
            'fields': ('payment_method', 'delivery_method', 'delivery_address', 'comment'),
        }),
        ('Итоги', {'fields': ('total_sum',)}),
        ('Служебное', {'fields': ('created_at', 'updated_at')}),
    )

    @admin.display(description='Статус', ordering='status__sort_order')
    def status_badge(self, obj: Order) -> str:
        return format_html(
            '<span style="color: white; background: {}; padding: 2px 8px; border-radius: 4px;">{}</span>',
            obj.status.color,
            obj.status.title,
        )

    def save_related(self, request, form, formsets, change):
        """После сохранения позиций заказа автоматически пересчитываем сумму."""
        super().save_related(request, form, formsets, change)
        form.instance.recalculate_total()
