from inventory.models import Product
from accounts.models import Restaurant
from decimal import Decimal
from django.db.models import F


def stock_alert_context(request):
    """
    Context processor providing:
    - active currency symbol and theme mode
    - all_restaurants list for developer dropdown toggle
    - user_restaurant: active restaurant (or None for global overview)
    - role flags: is_developer, is_restaurant_admin, user_role
    - alert counts dynamically scoped to the active tenant
    """
    if not request.user.is_authenticated:
        guest_theme = request.session.get('guest_theme_mode', 'light') if hasattr(request, 'session') else 'light'
        return {
            'currency_symbol': '₹',
            'theme_mode': guest_theme,
            'user_restaurant': None,
            'is_developer': False,
            'is_restaurant_admin': False,
            'all_restaurants': [],
        }

    try:
        profile = getattr(request.user, 'profile', None)
        currency_symbol = profile.currency_symbol if profile else '₹'
        theme_mode = profile.theme_mode if profile else 'light'
        enable_alerts = profile.enable_stock_alerts if profile else True
        is_dev = profile.is_developer if profile else request.user.is_superuser
        is_admin = profile.is_restaurant_admin if profile else False
        all_restaurants = list(Restaurant.objects.all().order_by('name')) if is_dev else []

        if is_dev:
            active_id = request.session.get('developer_active_restaurant_id')
            if active_id and active_id != 'all':
                restaurant = Restaurant.objects.filter(restaurant_id=active_id).first()
            else:
                restaurant = Restaurant.objects.order_by('id').first()
                if restaurant and hasattr(request, 'session'):
                    request.session['developer_active_restaurant_id'] = restaurant.restaurant_id
        else:
            restaurant = profile.restaurant if profile else None

        # Queryset scoped strictly to active restaurant
        if restaurant:
            prod_qs = Product.objects.filter(restaurant=restaurant)
        elif is_dev:
            prod_qs = Product.objects.all()
        else:
            prod_qs = Product.objects.none()

        out_of_stock_count = prod_qs.filter(current_stock__lte=Decimal('0')).count()
        low_stock_count = prod_qs.filter(
            current_stock__gt=Decimal('0'),
            current_stock__lte=F('minimum_stock')
        ).count()
        total_stock_alerts = out_of_stock_count + low_stock_count if enable_alerts else 0

        return {
            'currency_symbol': currency_symbol,
            'theme_mode': theme_mode,
            'enable_stock_alerts': enable_alerts,
            'global_out_of_stock_count': out_of_stock_count,
            'global_low_stock_count': low_stock_count,
            'global_stock_alerts': total_stock_alerts,
            'user_restaurant': restaurant,
            'is_developer': is_dev,
            'is_restaurant_admin': is_admin and not is_dev,
            'user_role': 'developer' if is_dev else (profile.role if profile else 'staff'),
            'all_restaurants': all_restaurants,
        }
    except Exception:
        return {
            'currency_symbol': '₹',
            'theme_mode': 'light',
            'enable_stock_alerts': True,
            'user_restaurant': None,
            'is_developer': False,
            'is_restaurant_admin': False,
            'all_restaurants': [],
        }
