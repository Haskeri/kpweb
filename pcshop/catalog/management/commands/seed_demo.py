"""
Management command: заполнение БД демонстрационными данными.

Запуск:
    python manage.py seed_demo
    python manage.py seed_demo --clear   # очистить перед загрузкой
"""

import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from catalog.models import Category, Component
from builds.models import Build, BuildItem
from orders.models import Order, OrderItem, OrderStatus

User = get_user_model()


class Command(BaseCommand):
    help = "Заполнить БД демонстрационными данными (категории, комплектующие, сборки, заказы)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear", action="store_true",
            help="Удалить существующие данные перед загрузкой"
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Очистка данных...")
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            BuildItem.objects.all().delete()
            Build.objects.all().delete()
            Component.objects.all().delete()
            Category.objects.all().delete()
            OrderStatus.objects.all().delete()
            self.stdout.write(self.style.WARNING("Данные удалены."))

        with transaction.atomic():
            self._create_statuses()
            cats = self._create_categories()
            comps = self._create_components(cats)
            builds = self._create_builds(comps)
            self._create_users_and_orders(comps, builds)

        self.stdout.write(self.style.SUCCESS("Демо-данные успешно загружены!"))

    # ------------------------------------------------------------------
    def _create_statuses(self):
        statuses = [
            ("new",         "Новый",           "#1F3B73", 10, False),
            ("in_progress", "В работе",         "#FF7A00", 20, False),
            ("ready",       "Готов к выдаче",   "#2E8B57", 30, False),
            ("completed",   "Выполнен",         "#198754", 40, True),
            ("cancelled",   "Отменён",          "#D9534F", 50, True),
        ]
        for code, title, color, sort_order, is_terminal in statuses:
            OrderStatus.objects.get_or_create(
                code=code,
                defaults=dict(title=title, color=color,
                              sort_order=sort_order, is_terminal=is_terminal)
            )
        self.stdout.write("  ✓ Статусы заказов")

    def _create_categories(self):
        data = [
            ("Процессоры",         "cpu",          "Центральные процессоры (CPU) Intel и AMD"),
            ("Материнские платы",  "motherboards", "Материнские платы для разных сокетов"),
            ("Оперативная память", "ram",          "Модули DDR4 / DDR5"),
            ("Видеокарты",         "gpu",          "Дискретные GPU NVIDIA и AMD"),
            ("Накопители",         "storage",      "SSD и HDD для хранения данных"),
            ("Блоки питания",      "psu",          "Блоки питания 80+ Bronze/Gold"),
            ("Корпуса",            "cases",        "Корпуса форм-фактора ATX / mATX"),
            ("Системы охлаждения", "cooling",      "Воздушные и жидкостные кулеры"),
        ]
        cats = {}
        for title, slug, desc in data:
            obj, _ = Category.objects.get_or_create(
                slug=slug, defaults=dict(title=title, description=desc)
            )
            cats[slug] = obj
        self.stdout.write("  ✓ Категории")
        return cats

    def _create_components(self, cats):
        items = [
            # (category_slug, title, brand, model, specs, purchase, sale, stock)
            ("cpu", "Core i5-13600K", "Intel", "i5-13600K",
             {"sockets": "LGA1700", "cores": 14, "threads": 20,
              "base_clock_ghz": 3.5, "tdp_w": 125}, 19500, 24990, 12),
            ("cpu", "Core i7-13700K", "Intel", "i7-13700K",
             {"sockets": "LGA1700", "cores": 16, "threads": 24,
              "base_clock_ghz": 3.4, "tdp_w": 125}, 29000, 36990, 7),
            ("cpu", "Ryzen 7 7700X", "AMD", "7700X",
             {"sockets": "AM5", "cores": 8, "threads": 16,
              "base_clock_ghz": 4.5, "tdp_w": 105}, 22000, 27990, 8),
            ("cpu", "Ryzen 5 7600X", "AMD", "7600X",
             {"sockets": "AM5", "cores": 6, "threads": 12,
              "base_clock_ghz": 4.7, "tdp_w": 105}, 15000, 18990, 15),

            ("motherboards", "ROG Strix Z790-F", "ASUS", "Z790-F Gaming",
             {"socket": "LGA1700", "memory_type": "DDR5", "form_factor": "ATX"}, 28000, 34990, 5),
            ("motherboards", "MAG Z790 Tomahawk", "MSI", "Z790 Tomahawk",
             {"socket": "LGA1700", "memory_type": "DDR5", "form_factor": "ATX"}, 22000, 27990, 6),
            ("motherboards", "X670E Aorus Master", "Gigabyte", "X670E Aorus",
             {"socket": "AM5", "memory_type": "DDR5", "form_factor": "ATX"}, 30000, 37990, 4),
            ("motherboards", "B650M DS3H", "Gigabyte", "B650M DS3H",
             {"socket": "AM5", "memory_type": "DDR5", "form_factor": "mATX"}, 12000, 14990, 10),

            ("ram", "Corsair Vengeance DDR5-5600 32GB", "Corsair", "CMK32GX5M2B5600C36",
             {"type": "DDR5", "capacity_gb": 32, "speed_mhz": 5600}, 8500, 10990, 20),
            ("ram", "Kingston Fury Beast DDR5-4800 16GB", "Kingston", "KF548C38BB-16",
             {"type": "DDR5", "capacity_gb": 16, "speed_mhz": 4800}, 4500, 5990, 30),
            ("ram", "G.Skill Trident Z5 DDR5-6000 32GB", "G.Skill", "F5-6000J3636F16GX2-TZ5K",
             {"type": "DDR5", "capacity_gb": 32, "speed_mhz": 6000}, 10000, 12990, 15),

            ("gpu", "GeForce RTX 4070 Super", "NVIDIA", "RTX 4070 Super",
             {"vram_gb": 12, "tdp_w": 220, "connector": "PCIe 4.0 x16"}, 52000, 64990, 8),
            ("gpu", "GeForce RTX 4080 Super", "NVIDIA", "RTX 4080 Super",
             {"vram_gb": 16, "tdp_w": 320, "connector": "PCIe 4.0 x16"}, 90000, 109990, 4),
            ("gpu", "Radeon RX 7700 XT", "AMD", "RX 7700 XT",
             {"vram_gb": 12, "tdp_w": 245, "connector": "PCIe 4.0 x16"}, 35000, 43990, 10),
            ("gpu", "Radeon RX 7900 XTX", "AMD", "RX 7900 XTX",
             {"vram_gb": 24, "tdp_w": 355, "connector": "PCIe 4.0 x16"}, 80000, 96990, 3),

            ("storage", "Samsung 980 Pro 1TB", "Samsung", "MZ-V8P1T0BW",
             {"type": "NVMe SSD", "capacity_gb": 1000, "read_mbps": 7000, "write_mbps": 5000}, 7000, 8990, 25),
            ("storage", "WD Black SN850X 2TB", "WD", "WDS200T2X0E",
             {"type": "NVMe SSD", "capacity_gb": 2000, "read_mbps": 7300, "write_mbps": 6600}, 13000, 16990, 12),
            ("storage", "Seagate Barracuda 4TB HDD", "Seagate", "ST4000DM004",
             {"type": "HDD", "capacity_gb": 4000, "rpm": 5400}, 6000, 7490, 20),

            ("psu", "Corsair RM850x 850W", "Corsair", "CP-9020200-EU",
             {"wattage": 850, "efficiency": "80+ Gold", "modular": True}, 9500, 11990, 15),
            ("psu", "be quiet! Straight Power 11 750W", "be quiet!", "BN284",
             {"wattage": 750, "efficiency": "80+ Gold", "modular": True}, 8500, 10490, 10),
            ("psu", "EVGA SuperNOVA 1000 G6", "EVGA", "220-G6-1000-X1",
             {"wattage": 1000, "efficiency": "80+ Gold", "modular": True}, 13000, 15990, 6),

            ("cases", "NZXT H7 Flow", "NZXT", "CM-H71FG-01",
             {"form_factor": "ATX", "color": "Black", "max_gpu_length_mm": 400}, 7500, 9490, 8),
            ("cases", "Fractal Design Meshify 2", "Fractal Design", "FD-C-MES2A-01",
             {"form_factor": "ATX", "color": "Black", "max_gpu_length_mm": 467}, 8500, 10490, 6),
            ("cases", "Lian Li O11 Dynamic EVO", "Lian Li", "G99.O11DE-1B.00",
             {"form_factor": "ATX", "color": "Black", "max_gpu_length_mm": 420}, 10000, 12490, 5),

            ("cooling", "Noctua NH-D15", "Noctua", "NH-D15",
             {"type": "air", "tdp_support_w": 250, "socket": "LGA1700/AM5"}, 6000, 7490, 10),
            ("cooling", "be quiet! Dark Rock Pro 4", "be quiet!", "BK022",
             {"type": "air", "tdp_support_w": 250, "socket": "LGA1700/AM5"}, 5500, 6990, 8),
            ("cooling", "Corsair H150i Elite", "Corsair", "CW-9060062-WW",
             {"type": "liquid", "radiator_mm": 360, "tdp_support_w": 350}, 11000, 13990, 7),
        ]

        comps = {}
        for (slug, title, brand, model, specs,
             purchase, sale, stock) in items:
            obj, created = Component.objects.get_or_create(
                title=title,
                defaults=dict(
                    category=cats[slug],
                    brand=brand,
                    model=model,
                    specs=specs,
                    purchase_price=Decimal(str(purchase)),
                    sale_price=Decimal(str(sale)),
                    stock=stock,
                    is_active=True,
                )
            )
            comps[title] = obj
        self.stdout.write(f"  ✓ Комплектующие ({len(comps)} шт.)")
        return comps

    def _create_builds(self, comps):
        def c(name):
            return comps.get(name)

        builds_data = [
            {
                "title": "Игровой ПК «Старт»",
                "description": "Отличный выбор для игр в Full HD. Тянет все актуальные игры в высоком качестве.",
                "items": [
                    (c("Ryzen 5 7600X"), 1),
                    (c("B650M DS3H"), 1),
                    (c("Kingston Fury Beast DDR5-4800 16GB"), 2),
                    (c("Radeon RX 7700 XT"), 1),
                    (c("Samsung 980 Pro 1TB"), 1),
                    (c("be quiet! Straight Power 11 750W"), 1),
                    (c("NZXT H7 Flow"), 1),
                    (c("Noctua NH-D15"), 1),
                ],
            },
            {
                "title": "Рабочая станция «Профи»",
                "description": "Для разработчиков, дизайнеров и создателей контента. Быстрый процессор и 32 ГБ ОЗУ.",
                "items": [
                    (c("Core i7-13700K"), 1),
                    (c("MAG Z790 Tomahawk"), 1),
                    (c("Corsair Vengeance DDR5-5600 32GB"), 1),
                    (c("GeForce RTX 4070 Super"), 1),
                    (c("WD Black SN850X 2TB"), 1),
                    (c("Corsair RM850x 850W"), 1),
                    (c("Fractal Design Meshify 2"), 1),
                    (c("be quiet! Dark Rock Pro 4"), 1),
                ],
            },
            {
                "title": "Топовый Gaming PC «Ультра»",
                "description": "Максимальная производительность для 4K-гейминга и стриминга. Никаких компромиссов.",
                "items": [
                    (c("Core i7-13700K"), 1),
                    (c("ROG Strix Z790-F"), 1),
                    (c("G.Skill Trident Z5 DDR5-6000 32GB"), 1),
                    (c("GeForce RTX 4080 Super"), 1),
                    (c("WD Black SN850X 2TB"), 1),
                    (c("Seagate Barracuda 4TB HDD"), 1),
                    (c("EVGA SuperNOVA 1000 G6"), 1),
                    (c("Lian Li O11 Dynamic EVO"), 1),
                    (c("Corsair H150i Elite"), 1),
                ],
            },
        ]

        builds = []
        for bd in builds_data:
            build, created = Build.objects.get_or_create(
                title=bd["title"],
                defaults=dict(
                    description=bd["description"],
                    is_template=True,
                    is_active=True,
                )
            )
            if created:
                for comp, qty in bd["items"]:
                    if comp:
                        BuildItem.objects.create(build=build, component=comp, quantity=qty)
            builds.append(build)

        self.stdout.write(f"  ✓ Сборки ({len(builds)} шт.)")
        return builds

    def _create_users_and_orders(self, comps, builds):
        # Менеджер
        manager, _ = User.objects.get_or_create(
            email="manager@pcshop.ru",
            defaults=dict(
                full_name="Иванов Алексей Сергеевич",
                role="manager",
                is_staff=True,
            )
        )
        if _:
            manager.set_password("manager123")
            manager.save()

        # Клиенты
        clients_data = [
            ("client1@example.com", "Петров Дмитрий Олегович"),
            ("client2@example.com", "Сидорова Анна Витальевна"),
            ("client3@example.com", "Козлов Артём Николаевич"),
        ]
        clients = []
        for email, name in clients_data:
            u, created = User.objects.get_or_create(
                email=email,
                defaults=dict(full_name=name, role="client")
            )
            if created:
                u.set_password("client123")
                u.save()
            clients.append(u)

        # Статусы
        status_new  = OrderStatus.objects.filter(code="new").first()
        status_prog = OrderStatus.objects.filter(code="in_progress").first()
        status_comp = OrderStatus.objects.filter(code="completed").first()
        status_canc = OrderStatus.objects.filter(code="cancelled").first()

        comp_list = list(comps.values())

        orders_data = [
            # (client_idx, status, payment, delivery, items[(comp,qty),...], build_idx)
            (0, status_comp, "card",  "pickup",   [(comp_list[0], 1), (comp_list[8], 2)], None),
            (0, status_prog, "card",  "delivery", [(comp_list[3], 1), (comp_list[10], 1)], None),
            (1, status_new,  "cash",  "pickup",   [], 0),          # сборка «Старт»
            (1, status_comp, "card",  "delivery", [(comp_list[11], 1), (comp_list[15], 1)], None),
            (2, status_new,  "card",  "pickup",   [(comp_list[0], 1), (comp_list[4], 1), (comp_list[8], 2)], None),
            (2, status_comp, "cash",  "delivery", [], 1),          # сборка «Профи»
            (0, status_canc, "card",  "pickup",   [(comp_list[6], 1)], None),
        ]

        for idx, (ci, status, payment, delivery, items, build_idx) in enumerate(orders_data):
            if not status:
                continue
            client = clients[ci]

            total = Decimal("0.00")
            order_items = []
            for comp, qty in items:
                subtotal = comp.sale_price * qty
                total += subtotal
                order_items.append((comp, qty, comp.sale_price))

            build = builds[build_idx] if build_idx is not None else None
            if build:
                total += build.total_price

            if total == Decimal("0") and build:
                total = build.total_price

            order, created = Order.objects.get_or_create(
                client=client,
                status=status,
                payment_method=payment,
                delivery_method=delivery,
                total_sum=total if total > 0 else Decimal("1"),
                defaults=dict(build=build),
            )

            if created:
                for comp, qty, price in order_items:
                    OrderItem.objects.create(
                        order=order, component=comp,
                        quantity=qty, unit_price=price
                    )

        self.stdout.write(f"  ✓ Пользователи и заказы")
