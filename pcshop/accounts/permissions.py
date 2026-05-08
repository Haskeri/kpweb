"""Миксины и декораторы для проверки роли пользователя.

Реализует матрицу прав доступа из подраздела 2.1 пояснительной записки.
"""

from functools import wraps

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Базовый миксин: проверяет, что роль пользователя в `allowed_roles`."""

    allowed_roles: tuple = ()
    raise_exception = True  # 403 вместо редиректа на login для уже авторизованных

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        # Суперпользователь и админ-роль имеют доступ всегда.
        if user.is_superuser or user.is_admin_role:
            return True
        return user.role in self.allowed_roles


class ClientRequiredMixin(RoleRequiredMixin):
    allowed_roles = ('client',)


class ManagerRequiredMixin(RoleRequiredMixin):
    allowed_roles = ('manager',)


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ('admin',)


class StaffRequiredMixin(RoleRequiredMixin):
    """Доступ для менеджеров и администраторов."""

    allowed_roles = ('manager', 'admin')


# ---------------------------------------------------------------------------
# Декораторы для функциональных view
# ---------------------------------------------------------------------------

def role_required(*roles):
    """Декоратор, разрешающий доступ только указанным ролям."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                raise PermissionDenied('Требуется авторизация.')
            if user.is_superuser or user.is_admin_role or user.role in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied('Недостаточно прав.')

        return _wrapped

    return decorator


client_required = role_required('client')
manager_required = role_required('manager')
admin_required = role_required('admin')
staff_required = role_required('manager', 'admin')
