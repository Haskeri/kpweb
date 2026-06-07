# pcshop

> **Веб-приложение для учёта комплектующих, сборки и продажи персональных компьютеров**

Курсовая работа по дисциплине **«Разработка веб-приложений»**, направление 09.03.01  
Студент: **Ануфриев Платон Дмитриевич**, гр. 241-327  
Преподаватель: Кружалов А.С., Московский Политех

---

## Содержание

- [Обзор](#обзор)
- [Технологический стек](#технологический-стек)
- [Архитектура](#архитектура)
- [Структура проекта](#структура-проекта)
- [Быстрый старт](#быстрый-старт)
- [Переменные окружения](#переменные-окружения)
- [Ролевая модель](#ролевая-модель)
- [Функциональность](#функциональность)
- [API и маршруты](#api-и-маршруты)
- [База данных](#база-данных)
- [Развёртывание](#развёртывание)

---

## Обзор

**pcshop** — полнофункциональный интернет-магазин компонентов для сборки ПК с:

- 🛒 Каталогом комплектующих с фильтрацией и поиском  
- 🖥️ Конфигуратором сборки ПК (пошаговый, Alpine.js)  
- 📦 Корзиной на основе сессий (без регистрации)  
- 🔐 Ролевой системой доступа (клиент / менеджер / администратор)  
- 📊 Аналитическим дашбордом для персонала  
- 📥 Импортом и экспортом каталога и заказов в CSV  

---

## Технологический стек

| Слой | Технология |
|---|---|
| Backend | Python 3.11 · Django 4.2 |
| База данных | SQLite (разработка) · PostgreSQL (продакшн) |
| Frontend | Bootstrap 5.3 · Bootstrap Icons · Alpine.js (CDN) |
| Шрифты | Inter · JetBrains Mono (Google Fonts) |
| ORM | Django ORM · `F()`-выражения · `select_related` · `prefetch_related` |
| Авторизация | `AbstractUser` · email-based login · session auth |
| Файлы | Pillow (изображения) · csv (импорт/экспорт) |

---

## Архитектура

Проект реализован по паттерну **MVT (Model–View–Template)**:

```
Запрос → urls.py → View (CBV/FBV) → Model (ORM) → Template (HTML)
                                  ↑
                          Context Processors
                         (cart_count, categories)
```

**Приложения Django:**

```
accounts  ──→  Пользователи, роли, профиль, аналитика
catalog   ──→  Категории, комплектующие, CRUD, CSV
builds    ──→  Сборки ПК, конфигуратор
orders    ──→  Корзина (сессия), заказы, статусы
```

---

## Структура проекта

```
pcshop/
├── manage.py
├── requirements.txt
├── .env.example
│
├── pcshop/                        # Настройки и корневые маршруты
│   ├── settings.py
│   ├── urls.py
│   ├── views.py                   # HomeView
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/                      # Пользователи и аналитика
│   ├── models.py                  # User (AbstractUser, email-логин, роли)
│   ├── views.py                   # Register, Login, Profile, Dashboard, Analytics
│   ├── forms.py
│   ├── permissions.py             # StaffRequiredMixin и др.
│   └── urls.py
│
├── catalog/                       # Каталог комплектующих
│   ├── models.py                  # Category, Component
│   ├── views.py                   # List, Detail, CRUD, CSV import/export
│   ├── forms.py
│   └── urls.py
│
├── builds/                        # Сборки ПК
│   ├── models.py                  # Build, BuildItem (M2M)
│   ├── views.py                   # BuildList, Detail, CRUD, Configurator
│   ├── forms.py                   # BuildForm, BuildItemFormSet
│   └── urls.py
│
├── orders/                        # Корзина и заказы
│   ├── models.py                  # OrderStatus, Order, OrderItem
│   ├── cart.py                    # Session-based корзина
│   ├── context_processors.py      # cart_count (без SQL-запросов)
│   ├── views.py                   # Cart, Checkout, OrderList/Detail, Manager
│   ├── forms.py
│   └── urls.py
│
├── templates/                     # HTML-шаблоны
│   ├── base.html                  # Общий layout (navbar, footer, messages)
│   ├── home.html
│   ├── accounts/
│   ├── builds/
│   ├── catalog/
│   ├── orders/
│   └── registration/
│
└── fixtures/                      # Начальные данные
    ├── order_statuses.json
    ├── categories.json
    └── components.json
```

---

## Быстрый старт

> Требуется **Python 3.11+**

### 1. Клонировать и установить зависимости

```bash
git clone https://github.com/Haskeri/kpweb.git
cd kpweb/pcshop

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Настроить окружение

```bash
cp .env.example .env
# Отредактируйте .env при необходимости (SECRET_KEY, DEBUG, DB_*)
```

### 3. Инициализировать базу данных

```bash
python manage.py migrate
python manage.py loaddata fixtures/order_statuses.json \
                          fixtures/categories.json \
                          fixtures/components.json
```

### 4. Создать суперпользователя

```bash
python manage.py createsuperuser
# Введите email и пароль
```

### 5. Запустить сервер

```bash
python manage.py runserver
```

### Открыть в браузере

| URL | Описание |
|---|---|
| http://127.0.0.1:8000/ | Главная страница |
| http://127.0.0.1:8000/catalog/ | Каталог комплектующих |
| http://127.0.0.1:8000/builds/ | Готовые сборки |
| http://127.0.0.1:8000/builds/configure/ | Конфигуратор ПК |
| http://127.0.0.1:8000/orders/cart/ | Корзина |
| http://127.0.0.1:8000/accounts/dashboard/ | Личный кабинет |
| http://127.0.0.1:8000/accounts/analytics/ | Аналитика (менеджер) |
| http://127.0.0.1:8000/admin/ | Django-админка |

---

## Переменные окружения

Файл `.env` (шаблон — `.env.example`):

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# SQLite (по умолчанию)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# PostgreSQL (для продакшн)
# DB_ENGINE=django.db.backends.postgresql
# DB_NAME=pcshop
# DB_USER=pcshop
# DB_PASSWORD=strongpassword
# DB_HOST=127.0.0.1
# DB_PORT=5432
```

---

## Ролевая модель

| Роль | Код | Возможности |
|---|---|---|
| **Клиент** | `client` | Просмотр каталога, корзина, оформление заказов, ЛК |
| **Менеджер** | `manager` | + управление каталогом, сборками, заказами, аналитика |
| **Администратор** | `admin` | + управление пользователями, импорт/экспорт, все права |

Роль задаётся в поле `User.role`. Свойства модели:

```python
user.is_client       # role == 'client'
user.is_manager      # role == 'manager'
user.is_admin_role   # role == 'admin' or is_superuser
```

Для защиты представлений используется `StaffRequiredMixin` из `accounts/permissions.py`.

---

## Функциональность

### Каталог (`catalog`)

- Список комплектующих с фильтрами: поиск, категория, бренд, диапазон цен, только в наличии
- Пагинация с сохранением фильтров
- Карточка товара: характеристики (JSON), количество на складе, похожие товары
- **Менеджер:** CRUD-интерфейс, импорт из CSV (Excel-совместимый BOM), экспорт в CSV

### Сборки ПК (`builds`)

- Публичный каталог готовых сборок (шаблоны менеджера)
- Страница сборки с полным составом и стоимостью
- **Конфигуратор:** 8 шагов (CPU → MB → RAM → Storage → GPU → PSU → Case → Cooling), Alpine.js, сохранение в ЛК или сразу в корзину
- **Менеджер:** CRUD сборок с inline-formset позиций

### Корзина (`orders.cart`)

- Хранение в сессии — не требует авторизации
- Поддержка отдельных комплектующих и целых сборок
- Атомарное обновление количества, удаление позиций
- Счётчик в navbar через context processor (без SQL-запросов)

### Заказы (`orders`)

- Оформление с проверкой остатков и атомарным списанием через `F('stock') - need`
- Выбор способа оплаты (карта / наличные / СБП) и доставки (курьер / самовывоз)
- История заказов клиента с фильтрацией по статусу
- **Менеджер:** общий список заказов, поиск по email / имени / номеру, смена статуса, экспорт CSV

### Аналитика (`accounts.AnalyticsView`)

- Выручка, себестоимость, прибыль, средний чек за выбранный период
- Топ-10 товаров по количеству продаж
- Товары с низким остатком и нулевым остатком

### Дашборд (`accounts.DashboardView`)

| Роль | Что показывает |
|---|---|
| Клиент | Кол-во заказов, сумма покупок, последние 5 заказов |
| Менеджер | KPI (всего / новых / сегодня / выручка), последние 10 заказов |
| Администратор | То же + ссылки на пользователей, импорт/экспорт |

---

## API и маршруты

### accounts

| Метод | URL | Описание |
|---|---|---|
| GET/POST | `/accounts/register/` | Регистрация |
| GET/POST | `/accounts/login/` | Вход |
| POST | `/accounts/logout/` | Выход |
| GET/POST | `/accounts/profile/` | Профиль |
| GET | `/accounts/dashboard/` | Личный кабинет |
| GET | `/accounts/analytics/` | Аналитика (менеджер) |

### catalog

| Метод | URL | Описание |
|---|---|---|
| GET | `/catalog/` | Список комплектующих |
| GET | `/catalog/item/<pk>/` | Карточка товара |
| GET/POST | `/catalog/manage/` | Управление каталогом |
| GET/POST | `/catalog/manage/new/` | Создать товар |
| GET | `/catalog/manage/export/` | Экспорт CSV |
| GET/POST | `/catalog/manage/import/` | Импорт CSV |
| GET/POST | `/catalog/manage/<pk>/edit/` | Редактировать |
| POST | `/catalog/manage/<pk>/delete/` | Удалить |

### builds

| Метод | URL | Описание |
|---|---|---|
| GET | `/builds/` | Список сборок |
| GET | `/builds/<pk>/` | Детальная страница |
| GET | `/builds/configure/` | Конфигуратор |
| POST | `/builds/configure/save/` | Сохранить конфигурацию |

### orders

| Метод | URL | Описание |
|---|---|---|
| GET | `/orders/cart/` | Корзина |
| POST | `/orders/cart/add/` | Добавить товар |
| POST | `/orders/cart/add-build/<pk>/` | Добавить сборку |
| POST | `/orders/cart/update/` | Обновить количество |
| GET/POST | `/orders/checkout/` | Оформление заказа |
| GET | `/orders/` | Мои заказы |
| GET | `/orders/<pk>/` | Детали заказа |
| GET/POST | `/orders/manage/` | Заказы (менеджер) |
| GET | `/orders/manage/export/` | Экспорт заказов CSV |

---

## База данных

### Схема основных таблиц

```
accounts_user
  id · email (unique) · role · full_name · phone · is_staff · is_active

catalog_category
  id · title · slug (unique) · description

catalog_component
  id · category_id → catalog_category
     · title · brand · model · specs (JSON)
     · purchase_price · sale_price · stock
     · image · is_active

builds_build
  id · title · description · is_template · is_active
     · created_by_id → accounts_user

builds_builditem  (M2M: Build ↔ Component)
  id · build_id · component_id · quantity

orders_orderstatus
  id · code (unique) · title · color · sort_order · is_terminal

orders_order
  id · client_id → accounts_user
     · build_id  → builds_build (nullable)
     · status_id → orders_orderstatus
     · total_sum · payment_method · delivery_method
     · delivery_address · comment · created_at

orders_orderitem
  id · order_id · component_id · quantity · unit_price
```

### Индексы производительности

```python
# catalog.Component
Index(fields=['category', 'brand'])
Index(fields=['stock'])

# orders.Order
Index(fields=['client', '-created_at'])
Index(fields=['status'])
```

---

## Развёртывание

### Подготовка к продакшн

```bash
# 1. Установить переменные окружения
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
SECRET_KEY=<длинный случайный ключ>

# 2. Собрать статику
python manage.py collectstatic --no-input

# 3. Применить миграции
python manage.py migrate

# 4. Запустить через Gunicorn
pip install gunicorn
gunicorn pcshop.wsgi:application --bind 0.0.0.0:8000 --workers 2
```

### Docker (опционально)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --no-input
CMD ["gunicorn", "pcshop.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Рекомендуемый стек для продакшн

```
Nginx  →  Gunicorn  →  Django  →  PostgreSQL
                   ↓
               Медиафайлы (MEDIA_ROOT)
               Статика (STATIC_ROOT → Nginx)
```

---

## Скриншоты интерфейса

| Страница | Описание |
|---|---|
| Главная | Hero-баннер, категории, популярные сборки, новинки |
| Каталог | Сайдбар категорий, карточки товаров, пагинация |
| Конфигуратор | 8-шаговый мастер сборки ПК |
| Корзина | Список позиций, итоговая сумма, оформление |
| Личный кабинет | KPI-карточки, последние заказы |
| Аналитика | Выручка, прибыль, топ-товары, остатки |

---

## Лицензия

Учебный проект. Все права принадлежат автору.  
© 2026 Ануфриев П.Д., Московский Политех
