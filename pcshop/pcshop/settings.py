"""
Настройки Django-проекта pcshop.

По умолчанию проект работает на SQLite — никакой подготовки не требуется.
Для переключения на PostgreSQL заполните DB_* в файле .env.
"""

from pathlib import Path

try:
    from decouple import config, Csv
except ImportError:  # для запуска без python-decouple
    import os

    def config(name, default=None, cast=str):
        value = os.environ.get(name, default)
        if value is None or callable(cast) and cast is bool:
            if isinstance(value, str):
                return value.lower() in ('1', 'true', 'yes', 'y', 'on')
            return bool(value)
        if cast is str or value is None:
            return value
        return cast(value)

    def Csv():
        def _cast(value):
            if not value:
                return []
            return [item.strip() for item in str(value).split(',') if item.strip()]
        return _cast

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-only-change-me')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# Доверенные источники для CSRF — обязательно при работе за HTTPS / reverse-proxy
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://127.0.0.1,http://localhost,https://cp.anufriev.pvpcult.ru,https://exam.anufriev.pvpcult.ru',
    cast=Csv(),
)

# ---------------------------------------------------------------------------
# Приложения и middleware
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Локальные приложения проекта
    'accounts.apps.AccountsConfig',
    'catalog.apps.CatalogConfig',
    'builds.apps.BuildsConfig',
    'orders.apps.OrdersConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pcshop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'orders.context_processors.cart_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'pcshop.wsgi.application'
ASGI_APPLICATION = 'pcshop.asgi.application'

# ---------------------------------------------------------------------------
# База данных
# ---------------------------------------------------------------------------
DB_ENGINE = config('DB_ENGINE', default='django.db.backends.sqlite3')

if DB_ENGINE == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': config('DB_NAME', default='pcshop'),
            'USER': config('DB_USER', default='pcshop'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='127.0.0.1'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# ---------------------------------------------------------------------------
# Модель пользователя и авторизация
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'home'

# ---------------------------------------------------------------------------
# Локализация
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Статика и медиа
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
