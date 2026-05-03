from django.contrib import admin

from .models import Build, BuildItem


class BuildItemInline(admin.TabularInline):
    model = BuildItem
    extra = 1
    autocomplete_fields = ('component',)
    fields = ('component', 'quantity', 'subtotal_display')
    readonly_fields = ('subtotal_display',)

    @admin.display(description='Подытог, ₽')
    def subtotal_display(self, obj: BuildItem) -> str:
        if obj.pk:
            return f'{obj.subtotal:.2f}'
        return '—'


@admin.register(Build)
class BuildAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_template', 'is_active', 'items_count', 'total_price_display', 'created_at')
    list_filter = ('is_template', 'is_active')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at', 'total_price_display')
    inlines = [BuildItemInline]
    fieldsets = (
        (None, {'fields': ('title', 'description')}),
        ('Публикация', {'fields': ('is_template', 'is_active', 'created_by')}),
        ('Цена', {'fields': ('total_price_display',)}),
        ('Служебное', {'fields': ('created_at', 'updated_at')}),
    )

    @admin.display(description='Итого, ₽')
    def total_price_display(self, obj: Build) -> str:
        if obj.pk:
            return f'{obj.total_price:.2f}'
        return '—'
