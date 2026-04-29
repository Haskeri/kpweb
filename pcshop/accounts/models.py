"""Модели приложения accounts.

Реализует кастомного пользователя с ролевой моделью доступа,
описанной в подразделе 2.1 пояснительной записки.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Менеджер пользователей с email вместо username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email обязателен для создания учётной записи.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('role', User.Role.CLIENT)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Пользователь системы с ролевой моделью доступа."""

    class Role(models.TextChoices):
        CLIENT = 'client', 'Клиент'
        MANAGER = 'manager', 'Менеджер'
        ADMIN = 'admin', 'Администратор'

    # Логин — email, поле username не используется.
    username = None
    email = models.EmailField('Email', unique=True)

    role = models.CharField(
        'Роль',
        max_length=16,
        choices=Role.choices,
        default=Role.CLIENT,
    )
    full_name = models.CharField('Полное имя', max_length=150, blank=True)
    phone = models.CharField('Контактный телефон', max_length=20, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['email']

    def __str__(self):
        return self.full_name or self.email

    # ----- Удобные ролевые свойства для использования в шаблонах и views -----

    @property
    def is_client(self) -> bool:
        return self.role == self.Role.CLIENT

    @property
    def is_manager(self) -> bool:
        return self.role == self.Role.MANAGER

    @property
    def is_admin_role(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser
