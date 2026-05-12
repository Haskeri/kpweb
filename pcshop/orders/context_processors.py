CART_SESSION_KEY = 'cart'


def cart_count(request):
    """Число позиций в корзине — читается только из сессии, без SQL-запросов."""
    cart = request.session.get(CART_SESSION_KEY, {})
    components = cart.get('components', {})
    builds = cart.get('builds', {})
    total = sum(components.values()) + sum(builds.values())
    return {'cart_count': total}
