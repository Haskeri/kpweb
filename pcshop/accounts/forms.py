"""Формы приложения accounts.

Реализует регистрацию клиента (роль фиксируется как client), вход по email
и редактирование собственного профиля.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    PasswordChangeForm,
)

User = get_user_model()


def _bootstrap(fields, css='form-control'):
    """Помечает поля формы CSS-классом Bootstrap."""
    for field in fields.values():
        widget = field.widget
        existing = widget.attrs.get('class', '')
        classes = f'{existing} {css}'.strip()
        widget.attrs['class'] = classes


class RegisterForm(UserCreationForm):
    """Регистрация нового клиента.

    Поле role не показывается пользователю и всегда выставляется в Role.CLIENT.
    Менеджеров и администраторов создаёт только администратор через /admin/.
    """

    email = forms.EmailField(label='Email', required=True)
    full_name = forms.CharField(label='Полное имя', max_length=150, required=False)
    phone = forms.CharField(label='Телефон', max_length=20, required=False)

    class Meta:
        model = User
        fields = ('email', 'full_name', 'phone', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap(self.fields)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CLIENT
        user.email = self.cleaned_data['email']
        user.full_name = self.cleaned_data.get('full_name', '')
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    """Стандартная форма входа, но с label «Email» и Bootstrap-классами."""

    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'autofocus': True}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap(self.fields)


class ProfileForm(forms.ModelForm):
    """Редактирование собственного профиля пользователем."""

    class Meta:
        model = User
        fields = ('full_name', 'phone', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap(self.fields)


class BootstrapPasswordChangeForm(PasswordChangeForm):
    """Стандартная форма смены пароля с Bootstrap-стилями."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap(self.fields)
