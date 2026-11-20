from .models import Restaurant


def get_active_restaurant(request_or_user):
    """
    Returns the active restaurant for the given request or user.
    - For Admins and Staff: returns user.profile.restaurant.
    - For Developers: returns the restaurant selected via the header toggle
      (stored in session as 'developer_active_restaurant_id'). If 'all' or not selected,
      returns None (Global Platform Overview).
    """
    request = None
    user = None

    if hasattr(request_or_user, 'user'):
        request = request_or_user
        user = request.user
    elif hasattr(request_or_user, 'profile'):
        user = request_or_user
    else:
        return None

    if request is None:
        try:
            from .middleware import get_current_request
            request = get_current_request()
        except Exception:
            request = None

    if not user or not user.is_authenticated:
        return None

    profile = getattr(user, 'profile', None)
    if not profile:
        return None

    if profile.is_developer:
        if request and hasattr(request, 'session'):
            active_id = request.session.get('developer_active_restaurant_id')
            if active_id and active_id != 'all':
                rest = Restaurant.objects.filter(restaurant_id=active_id).first()
                if rest:
                    return rest
        # Developer defaults to first available restaurant
        first_rest = Restaurant.objects.order_by('id').first()
        if first_rest and request and hasattr(request, 'session'):
            request.session['developer_active_restaurant_id'] = first_rest.restaurant_id
        return first_rest

    return profile.restaurant


def get_user_restaurant(user_or_request):
    """
    Backward-compatible alias for get_active_restaurant.
    """
    return get_active_restaurant(user_or_request)


def scope_queryset(request, queryset, restaurant_field='restaurant'):
    """
    Restricts a queryset strictly to the active restaurant tenant.
    - For Admins and Staff: strictly locked to their own restaurant (zero data leakage).
    - For Developers:
      - If a specific restaurant is selected in the header dropdown, scopes to that restaurant!
      - If 'all' or global view is selected, returns all records across all restaurants.
    """
    if not request.user.is_authenticated:
        return queryset.none()

    profile = getattr(request.user, 'profile', None)
    if not profile:
        return queryset.none()

    # Developer view: driven by session toggle (defaults to first restaurant)
    if profile.is_developer:
        active_id = request.session.get('developer_active_restaurant_id')
        if active_id and active_id != 'all':
            return queryset.filter(**{f"{restaurant_field}__restaurant_id": active_id})
        first_rest = Restaurant.objects.order_by('id').first()
        if first_rest:
            request.session['developer_active_restaurant_id'] = first_rest.restaurant_id
            return queryset.filter(**{f"{restaurant_field}__restaurant_id": first_rest.restaurant_id})
        return queryset

    # Admins and Staff: strictly locked to their own restaurant
    if profile.restaurant:
        return queryset.filter(**{restaurant_field: profile.restaurant})

    return queryset.none()


def seed_restaurant_starter_pack(restaurant, user=None, with_products=True):
    """
    Seeds a complete restaurant starter pack for a new or existing restaurant:
    - 10 Food-Service Categories
    - 9 Commercial Food & Hospitality Suppliers
    - 49 Core Restaurant Inventory Items with default units, pricing, stock and thresholds.
    """
    from decimal import Decimal
    from inventory.models import Category, Supplier, Product
    from transactions.models import StockTransaction

    CATEGORIES_DATA = [
        ('Grains & Flours', 'Bulk rice, flour, and core staple grain provisions'),
        ('Cooking Oils & Fats', 'Cooking oils, deep frying mediums, and culinary fats'),
        ('Whole Spices', 'Aromatic whole spices and seeds for tempering and biryani prep'),
        ('Powdered Spices & Masalas', 'Ground spices, signature curry blends, and gravy masalas'),
        ('Seasonings & Sauces', 'Flavor enhancers, salts, vinegars, and condiments'),
        ('Beverages & Drinks', 'Packaged mineral water and chilled carbonated soft drinks'),
        ('Coconut & Produce', 'Fresh coconuts and dehydrated coconut powder for gravies'),
        ('Packaging & Disposables', 'Food-grade packing covers, take-away carry bags, and meal containers'),
        ('Kitchen Hygiene & PPE', 'Chef apparel, food-grade sanitary gloves, and kitchen safety gear'),
        ('Crockery & Tableware', 'Dining serveware, juice glasses, and presentation plates'),
    ]

    SUPPLIERS_DATA = [
        {
            'name': 'Malabar Rice & Agro Traders',
            'phone': '+91 98470 12345',
            'email': 'orders@malabaragrotraders.com',
            'address': 'Grain Market Yard, Wholesale Complex, Kozhikode, Kerala 673001'
        },
        {
            'name': 'Golden Drop Edible Oils & Ghee Ltd.',
            'phone': '+91 94460 54321',
            'email': 'sales@goldendropoil.com',
            'address': 'Plot 14, Industrial Estate, Ernakulam, Kerala 682024'
        },
        {
            'name': 'Royal Spice Guild & Plantation Co.',
            'phone': '+91 97451 98765',
            'email': 'supplies@royalspiceguild.in',
            'address': 'Plantation Road, Kumily, Idukki District, Kerala 685509'
        },
        {
            'name': 'Eastern & Kitchen Masala Hub',
            'phone': '+91 98950 67890',
            'email': 'orders@easternmasalahub.com',
            'address': 'NH By-pass, Palarivattom, Kochi, Kerala 682025'
        },
        {
            'name': 'Metro Provisions & Condiments Wholesale',
            'phone': '+91 94970 11223',
            'email': 'accounts@metroprovisions.com',
            'address': 'Big Bazaar Street, Market Road, Thrissur, Kerala 680001'
        },
        {
            'name': 'Apex Beverage Bottlers & Distributors',
            'phone': '+91 98460 33445',
            'email': 'distribution@apexbeverages.in',
            'address': 'Beverage Logistics Hub, Kinfra Park, Kalamassery 683503'
        },
        {
            'name': 'Green Farm Fresh Coconuts Supply',
            'phone': '+91 97440 55667',
            'email': 'farmfresh@greencoconutsupply.com',
            'address': 'Coconut Canal Road, Vadakara, Calicut 673104'
        },
        {
            'name': 'PrimePack Disposables & Containers Co.',
            'phone': '+91 98951 77889',
            'email': 'sales@primepackdisposables.com',
            'address': 'Packaging City Complex, Broadway, Ernakulam 682031'
        },
        {
            'name': 'ChefWare Hospitality & Hygiene Solutions',
            'phone': '+91 94471 99001',
            'email': 'info@chefwarehospitality.com',
            'address': 'Hospitality Tower, M.G. Road, Trivandrum 695001'
        },
    ]

    PRODUCTS_DATA = [
        # Grains & Flours
        ('Basmati Rice', 'Grains & Flours', 'kg', Decimal('110.00'), Decimal('60.00'), Decimal('15.00')),
        ('Kayama Rice', 'Grains & Flours', 'kg', Decimal('95.00'), Decimal('45.00'), Decimal('12.00')),
        ('Maida', 'Grains & Flours', 'kg', Decimal('42.00'), Decimal('35.00'), Decimal('10.00')),

        # Cooking Oils & Fats
        ('Sunflower Oil', 'Cooking Oils & Fats', 'litre', Decimal('135.00'), Decimal('30.00'), Decimal('8.00')),
        ('Palm Oil', 'Cooking Oils & Fats', 'litre', Decimal('98.00'), Decimal('25.00'), Decimal('6.00')),
        ('Dalda', 'Cooking Oils & Fats', 'kg', Decimal('120.00'), Decimal('20.00'), Decimal('5.00')),

        # Whole Spices
        ('Star Aniece', 'Whole Spices', 'kg', Decimal('850.00'), Decimal('3.50'), Decimal('1.00')),
        ('Cinnamon', 'Whole Spices', 'kg', Decimal('420.00'), Decimal('4.00'), Decimal('1.00')),
        ('Cardamom', 'Whole Spices', 'kg', Decimal('2400.00'), Decimal('2.00'), Decimal('0.50')),
        ('Cloves', 'Whole Spices', 'kg', Decimal('950.00'), Decimal('3.00'), Decimal('0.50')),
        ('Nutmug', 'Whole Spices', 'kg', Decimal('1200.00'), Decimal('2.00'), Decimal('0.50')),
        ('Black Pepper', 'Whole Spices', 'kg', Decimal('650.00'), Decimal('6.00'), Decimal('1.50')),
        ('Dry Red Chilli', 'Whole Spices', 'kg', Decimal('280.00'), Decimal('12.00'), Decimal('3.00')),
        ('Bay Leafs', 'Whole Spices', 'kg', Decimal('320.00'), Decimal('4.00'), Decimal('1.00')),

        # Powdered Spices & Masalas
        ('Chicken masala', 'Powdered Spices & Masalas', 'pkt', Decimal('65.00'), Decimal('30.00'), Decimal('8.00')),
        ('Meat masala', 'Powdered Spices & Masalas', 'pkt', Decimal('75.00'), Decimal('25.00'), Decimal('6.00')),
        ('Garam Masala', 'Powdered Spices & Masalas', 'kg', Decimal('380.00'), Decimal('6.00'), Decimal('2.00')),
        ('Pepper Powder', 'Powdered Spices & Masalas', 'kg', Decimal('550.00'), Decimal('5.00'), Decimal('1.50')),
        ('Coriander Powder', 'Powdered Spices & Masalas', 'kg', Decimal('220.00'), Decimal('10.00'), Decimal('3.00')),
        ('Turmeric Powder', 'Powdered Spices & Masalas', 'kg', Decimal('190.00'), Decimal('8.00'), Decimal('2.00')),
        ('Red Chilli Powder', 'Powdered Spices & Masalas', 'kg', Decimal('310.00'), Decimal('12.00'), Decimal('3.00')),
        ('Black Pepper Powder', 'Powdered Spices & Masalas', 'kg', Decimal('580.00'), Decimal('5.00'), Decimal('1.50')),

        # Seasonings & Sauces
        ('Maggi cube', 'Seasonings & Sauces', 'box', Decimal('140.00'), Decimal('15.00'), Decimal('4.00')),
        ('Ajnamotto', 'Seasonings & Sauces', 'kg', Decimal('180.00'), Decimal('6.00'), Decimal('2.00')),
        ('Vinegar', 'Seasonings & Sauces', 'bottle', Decimal('55.00'), Decimal('18.00'), Decimal('5.00')),
        ('Honey', 'Seasonings & Sauces', 'bottle', Decimal('240.00'), Decimal('8.00'), Decimal('2.00')),
        ('Salt', 'Seasonings & Sauces', 'kg', Decimal('25.00'), Decimal('40.00'), Decimal('10.00')),
        ('Sugar', 'Seasonings & Sauces', 'kg', Decimal('48.00'), Decimal('35.00'), Decimal('8.00')),

        # Beverages & Drinks
        ('Water', 'Beverages & Drinks', 'bottle', Decimal('14.00'), Decimal('120.00'), Decimal('30.00')),
        ('Coke', 'Beverages & Drinks', 'bottle', Decimal('35.00'), Decimal('48.00'), Decimal('12.00')),
        ('Sprite', 'Beverages & Drinks', 'bottle', Decimal('35.00'), Decimal('48.00'), Decimal('12.00')),
        ('Fanta', 'Beverages & Drinks', 'bottle', Decimal('35.00'), Decimal('36.00'), Decimal('10.00')),
        ('Diet Coke', 'Beverages & Drinks', 'can', Decimal('45.00'), Decimal('24.00'), Decimal('8.00')),

        # Coconut & Produce
        ('Coconut', 'Coconut & Produce', 'pcs', Decimal('32.00'), Decimal('60.00'), Decimal('15.00')),
        ('Coconut Powder', 'Coconut & Produce', 'kg', Decimal('210.00'), Decimal('10.00'), Decimal('3.00')),

        # Packaging & Disposables
        ('Packing cover 5-7', 'Packaging & Disposables', 'pkt', Decimal('45.00'), Decimal('30.00'), Decimal('10.00')),
        ('Packing cover 6-8', 'Packaging & Disposables', 'pkt', Decimal('55.00'), Decimal('30.00'), Decimal('10.00')),
        ('Packing cover 8-10', 'Packaging & Disposables', 'pkt', Decimal('68.00'), Decimal('25.00'), Decimal('8.00')),
        ('Packing cover 9-12', 'Packaging & Disposables', 'pkt', Decimal('85.00'), Decimal('25.00'), Decimal('8.00')),
        ('Carry Bag 11-14', 'Packaging & Disposables', 'pkt', Decimal('75.00'), Decimal('35.00'), Decimal('10.00')),
        ('Carry Bag 13-16', 'Packaging & Disposables', 'pkt', Decimal('95.00'), Decimal('30.00'), Decimal('10.00')),
        ('Carry Bag 16-20', 'Packaging & Disposables', 'pkt', Decimal('130.00'), Decimal('25.00'), Decimal('8.00')),
        ('Container 650g', 'Packaging & Disposables', 'box', Decimal('190.00'), Decimal('20.00'), Decimal('6.00')),
        ('Container 750g', 'Packaging & Disposables', 'box', Decimal('220.00'), Decimal('20.00'), Decimal('6.00')),

        # Kitchen Hygiene & PPE
        ('Kitchen Hat', 'Kitchen Hygiene & PPE', 'pcs', Decimal('45.00'), Decimal('40.00'), Decimal('10.00')),
        ('Kitchen Gloves', 'Kitchen Hygiene & PPE', 'box', Decimal('160.00'), Decimal('15.00'), Decimal('5.00')),

        # Crockery & Tableware
        ('Juice Glass', 'Crockery & Tableware', 'pcs', Decimal('35.00'), Decimal('60.00'), Decimal('15.00')),
        ('Biriyani Plate', 'Crockery & Tableware', 'pcs', Decimal('110.00'), Decimal('48.00'), Decimal('12.00')),
        ('Dosa Plate', 'Crockery & Tableware', 'pcs', Decimal('95.00'), Decimal('48.00'), Decimal('12.00')),
    ]

    # 1. Create / Get Categories
    cat_map = {}
    for cat_name, desc in CATEGORIES_DATA:
        c, _ = Category.objects.get_or_create(restaurant=restaurant, name=cat_name, defaults={'description': desc})
        cat_map[cat_name] = c

    # 2. Create / Get Suppliers
    for sup in SUPPLIERS_DATA:
        Supplier.objects.get_or_create(
            restaurant=restaurant,
            name=sup['name'],
            defaults={
                'phone': sup['phone'],
                'email': sup['email'],
                'address': sup['address']
            }
        )

    # 3. Create / Get Products
    if with_products:
        for name, cat_name, unit, price, stock, min_stock in PRODUCTS_DATA:
            cat = cat_map[cat_name]
            p, created = Product.objects.get_or_create(
                restaurant=restaurant,
                name=name,
                defaults={
                    'category': cat,
                    'unit': unit,
                    'purchase_price': price,
                    'current_stock': stock,
                    'minimum_stock': min_stock
                }
            )
            if created and stock > 0 and user:
                StockTransaction.objects.create(
                    restaurant=restaurant,
                    product=p,
                    transaction_type='IN',
                    quantity=stock,
                    unit_price=price,
                    total_amount=stock * price,
                    user=user,
                    notes='Initial stock batch receipt from vendor'
                )
