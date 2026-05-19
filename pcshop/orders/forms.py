"""Формы приложения orders."""

from django import forms

from .models import Order


class CheckoutForm(forms.ModelForm):
    """Форма оформления заказа клиентом."""

    class Meta:
        model = Order
        fields = ('payment_method', 'delivery_method', 'delivery_address', 'comment')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = (existing + ' form-select').strip()
            else:
                field.widget.attrs['class'] = (existing + ' form-control').strip()
        self.fields['delivery_address'].widget = forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})
        self.fields['comment'].widget = forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})
        self.fields['delivery_address'].required = False
        self.fields['comment'].required = False

    def clean(self):
        cd = super().clean()
        if cd.get('delivery_method') == Order.DeliveryMethod.COURIER and not cd.get('delivery_address'):
            self.add_error('delivery_address', 'Укажите адрес доставки для курьера.')
        return cd


class OrderStatusForm(forms.ModelForm):
    """Менеджерская форма смены статуса заказа."""

    class Meta:
        model = Order
        fields = ('status',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].widget.attrs['class'] = 'form-select form-select-sm'
