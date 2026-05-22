"""Формы приложения builds."""

from django import forms
from django.forms import inlineformset_factory

from catalog.models import Component

from .models import Build, BuildItem


class BuildForm(forms.ModelForm):
    class Meta:
        model = Build
        fields = ('title', 'description', 'is_template', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' ' + css).strip()


class BuildItemForm(forms.ModelForm):
    class Meta:
        model = BuildItem
        fields = ('component', 'quantity')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['component'].queryset = Component.objects.filter(is_active=True).select_related('category')
        self.fields['component'].widget.attrs['class'] = 'form-select'
        self.fields['quantity'].widget.attrs['class'] = 'form-control'


BuildItemFormSet = inlineformset_factory(
    Build,
    BuildItem,
    form=BuildItemForm,
    extra=1,
    can_delete=True,
)
