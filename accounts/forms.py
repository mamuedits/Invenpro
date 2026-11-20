from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import UserProfile, Restaurant


class RestaurantAdminRegistrationForm(forms.ModelForm):
    """
    Registration form strictly for Restaurant Admins / Owners.
    On submission, it registers the Restaurant details and auto-allots a unique Restaurant ID.
    Staff members cannot register through this form.
    """
    restaurant_name = forms.CharField(
        max_length=150,
        required=True,
        label="Restaurant / Business Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Gourmet Bistro, Spice Route'})
    )
    restaurant_phone = forms.CharField(
        max_length=30,
        required=False,
        label="Restaurant Phone",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +91 98765 43210'})
    )
    restaurant_address = forms.CharField(
        required=False,
        label="Restaurant Address",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Street address, city, state'})
    )
    gst_number = forms.CharField(
        max_length=50,
        required=False,
        label="GSTIN / Business Tax ID",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 07AAAAA0000A1Z5 (optional)'})
    )

    password = forms.CharField(
        label="Admin Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter secure password'})
    )
    confirm_password = forms.CharField(
        label="Confirm Admin Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose admin username'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'admin@restaurant.com'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get('password')
        cpwd = cleaned_data.get('confirm_password')
        if pwd and cpwd and pwd != cpwd:
            self.add_error('confirm_password', "Passwords do not match!")
        return cleaned_data

    def save_admin_and_restaurant(self):
        cleaned = self.cleaned_data
        # 1. Create User
        user = User.objects.create_user(
            username=cleaned['username'],
            email=cleaned.get('email', ''),
            first_name=cleaned.get('first_name', ''),
            last_name=cleaned.get('last_name', ''),
            password=cleaned['password']
        )
        # 2. Create Restaurant with auto-allotted restaurant_id
        restaurant = Restaurant.objects.create(
            name=cleaned['restaurant_name'],
            owner=user,
            phone=cleaned.get('restaurant_phone', ''),
            address=cleaned.get('restaurant_address', ''),
            gst_number=cleaned.get('gst_number', ''),
            currency='INR'
        )
        # 3. Setup UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = 'admin'
        profile.restaurant = restaurant
        profile.phone = cleaned.get('restaurant_phone', '')
        profile.business_name = restaurant.name
        profile.gst_number = cleaned.get('gst_number', '')
        profile.store_address = cleaned.get('restaurant_address', '')
        profile.currency = 'INR'
        profile.theme_mode = 'light'
        profile.display_password = cleaned['password']
        profile.save()
        user.profile = profile

        # Automatically seed standard restaurant categories, suppliers and inventory
        from .utils import seed_restaurant_starter_pack
        seed_restaurant_starter_pack(restaurant, user=user, with_products=True)

        return user, restaurant


class StaffCreationForm(forms.Form):
    """
    Form used strictly by Restaurant Admins inside the Staff Management page
    to create staff logins for their restaurant.
    """
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. john_chef, cashier1'})
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'staff@restaurant.com'})
    )
    phone = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Assign temporary password'})
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm temporary password'})
    )

    def clean_username(self):
        uname = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=uname).exists():
            raise forms.ValidationError("A user with that username already exists. Please choose a different username.")
        return uname

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get('password')
        cpwd = cleaned_data.get('confirm_password')
        if pwd and cpwd and pwd != cpwd:
            self.add_error('confirm_password', "Passwords do not match!")
        return cleaned_data

    def save_staff(self, restaurant):
        cleaned = self.cleaned_data
        user = User.objects.create_user(
            username=cleaned['username'],
            email=cleaned.get('email', ''),
            first_name=cleaned.get('first_name', ''),
            last_name=cleaned.get('last_name', ''),
            password=cleaned['password']
        )
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = 'staff'
        profile.restaurant = restaurant
        profile.phone = cleaned.get('phone', '')
        profile.business_name = restaurant.name if restaurant else 'Invenpro Store'
        profile.currency = restaurant.currency if restaurant else 'INR'
        profile.theme_mode = 'light'
        profile.display_password = cleaned['password']
        profile.save()
        return user


class StaffPasswordResetForm(forms.Form):
    """
    Form for Restaurant Admins to reset a staff member's password.
    """
    new_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'})
    )
    confirm_new_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('confirm_new_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_new_password', "Passwords do not match!")
        return cleaned_data


# Alias for backward-compatibility if referenced in other modules
UserRegistrationForm = RestaurantAdminRegistrationForm


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


class StaffLoginForm(AuthenticationForm):
    """
    Dedicated login form for Staff members.
    """
    username = forms.CharField(
        label="Staff Username",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your assigned username', 'autofocus': True})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Your assigned password'})
    )


class UserProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = UserProfile
        fields = ['phone', 'business_name']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'business_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'theme_mode',
            'currency',
            'usd_rate',
            'eur_rate',
            'gbp_rate',
            'aed_rate',
            'business_name',
            'phone',
            'gst_number',
            'store_address',
            'default_min_stock',
            'enable_stock_alerts',
        ]
        widgets = {
            'theme_mode': forms.Select(attrs={'class': 'form-select', 'id': 'theme_mode_select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'usd_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'eur_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'gbp_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'aed_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'business_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. My Cafe & Restaurant'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 27ABCDE1234F1Z5'}),
            'store_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'City, State, PIN Code'}),
            'default_min_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'enable_stock_alerts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
