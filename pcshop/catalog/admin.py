from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Component


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'components_count')
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}

    @admin.display(description='Товаров')
    def components_count(self, obj: Category) -> int:
        return obj.components.count()


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'brand',
        'category',
        'sale_price',
        'stock_badge',
        'is_active',
    )
    list_filter = ('category', 'brand', 'is_active')
    search_fields = ('title', 'brand', 'model')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('category',)
    fieldsets = (
        (None, {'fields': ('category', 'title', 'brand', 'model', 'is_active')}),
        ('Характеристики', {'fields': ('specs', 'image')}),
        ('Цена и склад', {'fields': ('purchase_price', 'sale_price', 'stock')}),
        ('Служебное', {'fields': ('created_at', 'updated_at')}),
    )

    @admin.display(description='Остаток', ordering='stock')
    def stock_badge(self, obj: Component) -> str:
        if obj.stock == 0:
            color = '#D9534F'
            text = 'нет'
        elif obj.is_low_stock:
            color = '#FF7A00'
            text = f'низкий ({obj.stock})'
        else:
            color = '#2E8B57'
            text = str(obj.stock)
        return format_html(
            '<span style="color: white; background: {}; padding: 2px 8px; border-radius: 4px;">{}</span>',
            color,
            text,
        )
