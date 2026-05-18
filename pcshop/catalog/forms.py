"""Формы приложения catalog: фильтр каталога и форма редактирования товара."""

from django import forms

from .models import Category, Component


class CatalogFilterForm(forms.Form):
    """Фильтры для публичной страницы каталога."""

    q = forms.CharField(label='Поиск', required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Поиск по названию или бренду'}))
    category = forms.ModelChoiceField(
        label='Категория',
        queryset=Category.objects.all(),
        required=False,
        empty_label='Все категории',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    brand = forms.CharField(label='Бренд', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    min_price = forms.DecimalField(label='Цена от', required=False, min_value=0,
                                    widget=forms.NumberInput(attrs={'class': 'form-control'}))
    max_price = forms.DecimalField(label='Цена до', required=False, min_value=0,
                                    widget=forms.NumberInput(attrs={'class': 'form-control'}))
    only_in_stock = forms.BooleanField(label='Только в наличии', required=False,
                                        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))


class ComponentForm(forms.ModelForm):
    """Форма создания/редактирования комплектующего (для менеджера)."""

    class Meta:
        model = Component
        fields = (
            'category', 'title', 'brand', 'model', 'specs',
            'purchase_price', 'sale_price', 'stock', 'image', 'is_active',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = (existing + ' form-check-input').strip()
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = (existing + ' form-select').strip()
            else:
                field.widget.attrs['class'] = (existing + ' form-control').strip()
        self.fields['specs'].help_text = 'JSON-объект, например {"cores": 8, "tdp": 105}'
