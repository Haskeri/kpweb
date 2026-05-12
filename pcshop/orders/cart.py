"""Session-based корзина для приложения orders.

Хранит товары и сборки в сессии пользователя:
    request.session['cart'] = {
        'components': {'<id>': <qty>, ...},
        'builds':     {'<id>': <qty>, ...},
    }
"""

from decimal import Decimal

from builds.models import Build
from catalog.models import Component

CART_SESSION_KEY = 'cart'


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if not cart:
            cart = {'components': {}, 'builds': {}}
            self.session[CART_SESSION_KEY] = cart
        self.cart = cart

    # ---- mutations ------------------------------------------------------
    def add_component(self, component_id: int, qty: int = 1):
        key = str(component_id)
        self.cart['components'][key] = self.cart['components'].get(key, 0) + qty
        self._save()

    def set_component_qty(self, component_id: int, qty: int):
        key = str(component_id)
        if qty <= 0:
            self.cart['components'].pop(key, None)
        else:
            self.cart['components'][key] = qty
        self._save()

    def remove_component(self, component_id: int):
        self.cart['components'].pop(str(component_id), None)
        self._save()

    def add_build(self, build_id: int, qty: int = 1):
        key = str(build_id)
        self.cart['builds'][key] = self.cart['builds'].get(key, 0) + qty
        self._save()

    def remove_build(self, build_id: int):
        self.cart['builds'].pop(str(build_id), None)
        self._save()

    def clear(self):
        self.cart = {'components': {}, 'builds': {}}
        self.session[CART_SESSION_KEY] = self.cart
        self.session.modified = True

    # ---- queries --------------------------------------------------------
    def is_empty(self) -> bool:
        return not self.cart['components'] and not self.cart['builds']

    def total_items(self) -> int:
        return (
            sum(self.cart['components'].values())
            + sum(self.cart['builds'].values())
        )

    def component_lines(self):
        ids = [int(k) for k in self.cart['components'].keys()]
        components = {c.pk: c for c in Component.objects.filter(pk__in=ids)}
        lines = []
        for pk, qty in self.cart['components'].items():
            comp = components.get(int(pk))
            if comp is None:
                continue
            lines.append({
                'component': comp,
                'quantity': qty,
                'subtotal': comp.sale_price * qty,
            })
        return lines

    def build_lines(self):
        ids = [int(k) for k in self.cart['builds'].keys()]
        builds = {b.pk: b for b in Build.objects.filter(pk__in=ids).prefetch_related('items__component')}
        lines = []
        for pk, qty in self.cart['builds'].items():
            b = builds.get(int(pk))
            if b is None:
                continue
            lines.append({
                'build': b,
                'quantity': qty,
                'subtotal': b.total_price * qty,
            })
        return lines

    def total(self) -> Decimal:
        total = Decimal('0.00')
        for line in self.component_lines():
            total += line['subtotal']
        for line in self.build_lines():
            total += line['subtotal']
        return total

    def _save(self):
        self.session[CART_SESSION_KEY] = self.cart
        self.session.modified = True
