import os
import re
import secrets
from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import admin_required, developer_required
from .forms import (
    RestaurantAdminRegistrationForm,
    StaffCreationForm,
    StaffLoginForm,
    StaffPasswordResetForm,
    SystemSettingsForm,
    UserLoginForm,
    UserProfileUpdateForm,
)
from .models import (
    PasswordResetOTP,
    Restaurant,
    StaffPasswordRequest,
    UserProfile,
    cleanup_orphaned_restaurants,
)
from expenses.models import Expense
from inventory.models import Product
from transactions.models import StockTransaction



def register_view(request):
    """
    Restaurant Admin / Owner Registration:
    Registers a new business, creates the Restaurant record with an auto-allotted unique Restaurant ID,
    and creates the primary Admin account. Staff cannot self-register.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RestaurantAdminRegistrationForm(request.POST)
        if form.is_valid():
            user, restaurant = form.save_admin_and_restaurant()
            messages.success(
                request,
                f"🎉 Welcome {user.username}! Your restaurant '{restaurant.name}' has been created with Allotted Restaurant ID: {restaurant.restaurant_id}. You can now manage your staff from the Staff Management page."
            )
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors in the registration form.")
    else:
        form = RestaurantAdminRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    General / Admin Login View.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            res_info = f" ({user.profile.restaurant.name} • {user.profile.restaurant.restaurant_id})" if getattr(user, 'profile', None) and user.profile.restaurant else ""
            messages.success(request, f"Welcome back, {user.username}!{res_info}")
            next_url = request.GET.get('next')
            return redirect(next_url if next_url else 'dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def staff_login_view(request):
    """
    Dedicated Staff Login Portal:
    Allows staff members created by their Restaurant Admin to log in.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = StaffLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            res_name = user.profile.restaurant.name if getattr(user, 'profile', None) and user.profile.restaurant else "your restaurant"
            messages.success(request, f"Welcome {user.username}! Signed in to {res_name}.")
            next_url = request.GET.get('next')
            return redirect(next_url if next_url else 'dashboard')
        else:
            messages.error(request, "Invalid credentials. Please verify your username and password provided by your Restaurant Admin.")
    else:
        form = StaffLoginForm()

    return render(request, 'accounts/staff_login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


# ==============================================================================
# STAFF MANAGEMENT (RESTRICTED TO RESTAURANT ADMINS ONLY)
# ==============================================================================
@admin_required
def staff_management_view(request):
    """
    Staff Management Page:
    Accessible strictly by Restaurant Admins. Staff members are blocked.
    Shows the Restaurant Name, Allotted Restaurant ID, staff member roster,
    and an onboard form to create new staff credentials.
    """
    profile = request.user.profile
    restaurant = profile.restaurant

    # If developer has no restaurant assigned, pick the first or let them view system
    if not restaurant and profile.is_developer:
        restaurant = Restaurant.objects.first()

    if not restaurant:
        messages.warning(request, "Please create or assign a Restaurant first.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            staff_user = form.save_staff(restaurant)
            messages.success(
                request,
                f"✅ Staff account '{staff_user.username}' created successfully for {restaurant.name} (ID: {restaurant.restaurant_id})! Please share their username and password with them."
            )
            return redirect('staff_management')
        else:
            messages.error(request, "Could not create staff member. Please check form errors.")
    else:
        form = StaffCreationForm()

    staff_members = User.objects.filter(
        profile__restaurant=restaurant,
        profile__role='staff'
    ).select_related('profile').order_by('-date_joined')

    pending_password_requests = StaffPasswordRequest.objects.filter(
        restaurant=restaurant,
        is_resolved=False
    ).select_related('staff_user', 'staff_user__profile')

    return render(request, 'accounts/staff_management.html', {
        'restaurant': restaurant,
        'staff_members': staff_members,
        'pending_password_requests': pending_password_requests,
        'form': form,
    })


@admin_required
def reset_staff_password_view(request, staff_id):
    """
    Allows a Restaurant Admin to reset password for a staff member of their own restaurant.
    """
    restaurant = request.user.profile.restaurant
    if request.user.profile.is_developer and not restaurant:
        staff_user = get_object_or_404(User, pk=staff_id, profile__role='staff')
    else:
        staff_user = get_object_or_404(User, pk=staff_id, profile__restaurant=restaurant, profile__role='staff')

    if request.method == 'POST':
        form = StaffPasswordResetForm(request.POST)
        if form.is_valid():
            new_pwd = form.cleaned_data['new_password']
            staff_user.set_password(new_pwd)
            staff_user.save()
            profile, _ = UserProfile.objects.get_or_create(user=staff_user)
            profile.display_password = new_pwd
            profile.save()
            StaffPasswordRequest.objects.filter(staff_user=staff_user, is_resolved=False).update(is_resolved=True)
            messages.success(request, f"Password for staff '{staff_user.username}' updated successfully. Please share the new password with them.")
            return redirect('staff_management')
        else:
            messages.error(request, "Password reset failed. Passwords must match.")
    return redirect('staff_management')


@admin_required
def delete_staff_view(request, staff_id):
    """
    Allows a Restaurant Admin to remove a staff member from their restaurant.
    """
    restaurant = request.user.profile.restaurant
    if request.user.profile.is_developer and not restaurant:
        staff_user = get_object_or_404(User, pk=staff_id, profile__role='staff')
    else:
        staff_user = get_object_or_404(User, pk=staff_id, profile__restaurant=restaurant, profile__role='staff')

    uname = staff_user.username
    staff_user.delete()
    messages.success(request, f"Staff account '{uname}' has been deleted from {restaurant.name if restaurant else 'system'}.")
    return redirect('staff_management')


# ==============================================================================
# ADMIN MANAGEMENT (RESTRICTED TO DEVELOPERS ONLY)
# ==============================================================================
@developer_required
def developer_admin_management_view(request):
    """
    Admin Management Page:
    Accessible ONLY by Developers.
    Displays all registered Restaurants, their Allotted Restaurant IDs, their Admins,
    system-wide metrics, and a Promote to Developer button.
    Automatically purges any restaurants that have 0 admins.
    """
    cleanup_orphaned_restaurants()

    restaurants = Restaurant.objects.all().select_related('owner').annotate(
        member_count=Count('members', distinct=True),
        product_count=Count('products', distinct=True)
    ).order_by('-created_at')

    # All admins and developers across the platform
    admins = User.objects.filter(
        profile__role__in=['admin', 'developer']
    ).select_related('profile', 'profile__restaurant').order_by('id')

    total_restaurants = restaurants.count()
    total_admins = User.objects.filter(profile__role='admin').count()
    total_developers = User.objects.filter(profile__role='developer').count()
    total_staff = User.objects.filter(profile__role='staff').count()
    total_products = Product.objects.count()

    return render(request, 'accounts/admin_management.html', {
        'restaurants': restaurants,
        'admins': admins,
        'total_restaurants': total_restaurants,
        'total_admins': total_admins,
        'total_developers': total_developers,
        'total_staff': total_staff,
        'total_products': total_products,
    })


@developer_required
def developer_edit_admin_view(request, user_id):
    """
    Allows a Developer to edit an admin's details (username, full name, email, phone, active status)
    and optionally change their password directly from the Admin Management page.
    """
    target_user = get_object_or_404(User, pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)

    if request.method == 'POST':
        new_username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        is_active_val = request.POST.get('is_active')

        if not new_username:
            messages.error(request, "Username cannot be empty.")
            return redirect('admin_management')

        if User.objects.filter(username__iexact=new_username).exclude(pk=target_user.pk).exists():
            messages.error(request, f"Username '{new_username}' is already taken by another user.")
            return redirect('admin_management')

        target_user.username = new_username
        target_user.first_name = first_name
        target_user.last_name = last_name
        target_user.email = email

        if target_user != request.user and is_active_val is not None:
            target_user.is_active = (is_active_val == 'true')

        password_changed = False
        if new_password:
            target_user.set_password(new_password)
            profile.display_password = new_password
            password_changed = True

        target_user.save()
        profile.phone = phone
        profile.save()

        if password_changed and target_user == request.user:
            update_session_auth_hash(request, target_user)

        msg = f"✅ Updated details for '{target_user.username}'."
        if password_changed:
            msg += " Password has been changed."
        messages.success(request, msg)

    return redirect('admin_management')


@developer_required
def developer_delete_admin_view(request, user_id):
    """
    Allows a Developer to delete an admin user.
    If this admin is the last admin of their restaurant, the entire restaurant and all its
    associated tenant data (categories, suppliers, products, transactions, expenses, staff)
    are permanently deleted.
    """
    target_user = get_object_or_404(User, pk=user_id)
    if target_user == request.user:
        messages.error(request, "You cannot delete your own developer account.")
        return redirect('admin_management')

    if target_user.is_superuser:
        messages.error(request, "Superuser/Developer accounts cannot be deleted here.")
        return redirect('admin_management')

    username = target_user.username
    profile = getattr(target_user, 'profile', None)
    restaurant = profile.restaurant if profile else None
    res_name = restaurant.name if restaurant else None

    # Check remaining admins for this restaurant
    if restaurant and profile and profile.role == 'admin':
        remaining_admins = UserProfile.objects.filter(
            restaurant=restaurant,
            role='admin'
        ).exclude(user=target_user).count()

        if remaining_admins == 0:
            # Last admin: Delete the restaurant and all its data!
            staff_user_ids = list(
                User.objects.filter(profile__restaurant=restaurant)
                .exclude(pk=target_user.pk)
                .exclude(is_superuser=True)
                .exclude(profile__role='developer')
                .values_list('id', flat=True)
            )
            restaurant.delete()
            if staff_user_ids:
                User.objects.filter(id__in=staff_user_ids).delete()
            target_user.delete()
            messages.success(
                request,
                f"🗑️ Admin '{username}' deleted. Because no admins remained for '{res_name}', the restaurant and all its inventory, transactions, and expenses have been completely deleted."
            )
            return redirect('admin_management')

    # If other admins still exist for this restaurant:
    remaining_admin = UserProfile.objects.filter(
        restaurant=restaurant, 
        role='admin'
    ).exclude(user=target_user).first()
    if remaining_admin:
        StockTransaction.objects.filter(user=target_user).update(user=remaining_admin.user)
        Expense.objects.filter(created_by=target_user).update(created_by=remaining_admin.user)

    target_user.delete()
    messages.success(request, f"🗑️ Admin '{username}' has been deleted successfully.")
    return redirect('admin_management')


@developer_required
def developer_delete_restaurant_view(request, restaurant_id):
    """
    Allows a Developer to directly delete a Restaurant and all of its associated data:
    categories, suppliers, products, transactions, expenses, and staff accounts.
    """
    restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    res_name = restaurant.name
    res_code = restaurant.restaurant_id

    tenant_users = list(
        User.objects.filter(profile__restaurant=restaurant)
        .exclude(is_superuser=True)
        .exclude(profile__role='developer')
        .values_list('id', flat=True)
    )

    restaurant.delete()
    if tenant_users:
        User.objects.filter(id__in=tenant_users).delete()

    if request.session.get('developer_active_restaurant_id') == res_code:
        request.session['developer_active_restaurant_id'] = None

    messages.success(
        request,
        f"🗑️ Restaurant '{res_name}' ({res_code}) and all its data have been permanently deleted."
    )
    return redirect('admin_management')


@developer_required
def promote_to_developer_view(request, user_id):
    """
    Allows a Developer to promote a Restaurant Admin to Developer role (or demote).
    """
    target_user = get_object_or_404(User, pk=user_id)
    if target_user == request.user:
        messages.warning(request, "You cannot alter your own developer status directly.")
        return redirect('admin_management')

    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    if profile.role == 'developer':
        profile.role = 'admin'
        messages.success(request, f"{target_user.username} has been changed from Developer back to Restaurant Admin.")
    else:
        profile.role = 'developer'
        messages.success(request, f"🎉 {target_user.username} has been successfully promoted to Developer!")
    profile.save()

    return redirect('admin_management')


@developer_required
def toggle_user_role_view(request, user_id):
    return promote_to_developer_view(request, user_id)


@developer_required
def developer_switch_restaurant_view(request, restaurant_id):
    """
    Allows a Developer to toggle between restaurants from the header dropdown.
    - 'RES-xxxxx': Specific restaurant tenant workspace.
    """
    if restaurant_id == 'all':
        first_rest = Restaurant.objects.order_by('id').first()
        if first_rest:
            restaurant_id = first_rest.restaurant_id
    rest = get_object_or_404(Restaurant, restaurant_id=restaurant_id)
    request.session['developer_active_restaurant_id'] = rest.restaurant_id
    messages.success(request, f"🏬 Active Workspace toggled to: {rest.name} (ID: {rest.restaurant_id})")

    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'dashboard')


# Backward compatibility redirect
@admin_required
def user_management_view(request):
    profile = request.user.profile
    if profile.is_developer:
        return redirect('admin_management')
    return redirect('staff_management')


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save()
            user = request.user
            user.first_name = form.cleaned_data.get('first_name', '')
            user.last_name = form.cleaned_data.get('last_name', '')
            user.email = form.cleaned_data.get('email', '')
            user.save()
            messages.success(request, "Your profile has been updated.")
            return redirect('profile')
    else:
        form = UserProfileUpdateForm(instance=profile)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile,
    })


@admin_required
def settings_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "System settings updated successfully!")
            return redirect('settings')
    else:
        form = SystemSettingsForm(instance=profile)

    return render(request, 'accounts/settings.html', {
        'form': form,
        'profile': profile,
    })


@login_required
def toggle_theme_quick_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    new_theme = 'dark' if profile.theme_mode == 'light' else 'light'
    profile.theme_mode = new_theme
    profile.save()
    request.session['guest_theme_mode'] = new_theme

    next_url = request.META.get('HTTP_REFERER', 'dashboard')
    return redirect(next_url)


def toggle_guest_theme_view(request):
    """
    Public theme toggle for Login / Register / Staff Login / Forgot Password pages.
    Supports both AJAX JSON requests and standard browser redirects.
    """
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        new_theme = 'dark' if profile.theme_mode == 'light' else 'light'
        profile.theme_mode = new_theme
        profile.save()
        request.session['guest_theme_mode'] = new_theme
    else:
        current = request.session.get('guest_theme_mode', 'light')
        requested = request.GET.get('mode') or request.POST.get('mode')
        if requested in ('light', 'dark'):
            new_theme = requested
        else:
            new_theme = 'dark' if current == 'light' else 'light'
        request.session['guest_theme_mode'] = new_theme

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'theme': new_theme})

    next_url = request.META.get('HTTP_REFERER', 'login')
    return redirect(next_url)


# ==============================================================================
# FORGOT PASSWORD FLOWS
# 1. Admin & Developer Email OTP Recovery
# 2. Staff Password Request (Notifies Restaurant Admin via Email + Staff Portal)
# ==============================================================================
def _mask_email(email):
    if not email or '@' not in email:
        return email or 'Not registered'
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + '***'
    else:
        masked_local = local[:2] + '***' + local[-1]
    return f"{masked_local}@{domain}"


def _create_and_dispatch_otp(user):
    """
    Generates a secure 6-digit OTP valid for 10 minutes and dispatches it via
    live Email SMTP (Gmail). Returns (otp_obj, delivery_meta_dict).
    """
    from .notifications import send_email_otp

    # Invalidate any older unused OTPs for this user
    PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)

    otp_code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = timezone.now() + timedelta(minutes=10)
    raw_dest = user.email.strip()
    masked_dest = _mask_email(raw_dest)

    otp_obj = PasswordResetOTP.objects.create(
        user=user,
        otp_code=otp_code,
        channel='email',
        destination=masked_dest,
        expires_at=expires_at,
    )

    if raw_dest:
        delivery_meta = send_email_otp(user, raw_dest, otp_code)
    else:
        delivery_meta = {'sent_live': False, 'provider': 'Email Not Configured', 'error': 'User has no email address'}

    delivery_meta['channel'] = 'email'
    delivery_meta['masked_destination'] = masked_dest
    return otp_obj, delivery_meta


def forgot_password_request_view(request):
    """
    Step 1 (Admins & Developers): Enter Username or Email to receive a 6-digit OTP via Email.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    identifier = request.POST.get('identifier', '').strip() if request.method == 'POST' else ''

    if request.method == 'POST':
        if not identifier:
            messages.error(request, "Please enter your username or registered email address.")
        else:
            user = User.objects.filter(
                Q(username__iexact=identifier) | Q(email__iexact=identifier)
            ).select_related('profile', 'profile__restaurant').first()

            if not user:
                messages.error(request, "No Admin or Developer account was found matching that username or email.")
            else:
                profile = getattr(user, 'profile', None)
                is_admin_or_dev = user.is_superuser or (profile and profile.role in ('admin', 'developer'))

                if not is_admin_or_dev:
                    messages.info(
                        request,
                        "Staff accounts recover passwords through their Restaurant Admin. Redirected you to Staff Password Recovery."
                    )
                    return redirect(f"/staff-forgot-password/?username={quote(user.username)}")

                if not user.email:
                    messages.error(
                        request,
                        "This account has no registered email address. Please contact your system administrator."
                    )
                else:
                    otp_obj, delivery_meta = _create_and_dispatch_otp(user)
                    request.session['reset_otp_id'] = otp_obj.id
                    request.session['reset_sent_live'] = delivery_meta.get('sent_live', False)
                    request.session['reset_provider'] = delivery_meta.get('provider', '')
                    request.session['reset_delivery_error'] = delivery_meta.get('error', '')

                    if delivery_meta.get('sent_live'):
                        messages.success(
                            request,
                            f"✅ 6-digit verification OTP delivered to your email: {otp_obj.destination}."
                        )
                    elif delivery_meta.get('error'):
                        messages.warning(
                            request,
                            f"Live email gateway returned an error ({delivery_meta['error']}). Local preview OTP generated for testing."
                        )
                    else:
                        messages.success(
                            request,
                            f"A 6-digit OTP has been sent to your registered email: {otp_obj.destination}."
                        )
                    return redirect('forgot_password_verify')

    return render(request, 'accounts/forgot_password.html', {
        'identifier': identifier,
    })


def forgot_password_verify_view(request):
    """
    Step 2 (Admins & Developers): Verify the 6-digit OTP sent via Email.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    otp_id = request.session.get('reset_otp_id')
    if not otp_id:
        messages.warning(request, "Please request an OTP first.")
        return redirect('forgot_password')

    otp_obj = PasswordResetOTP.objects.select_related('user', 'user__profile').filter(pk=otp_id).first()
    if not otp_obj:
        messages.warning(request, "OTP session expired. Please request a new OTP.")
        return redirect('forgot_password')

    if request.method == 'POST':
        action = request.POST.get('action', 'verify')
        if action == 'resend':
            new_otp, delivery_meta = _create_and_dispatch_otp(otp_obj.user)
            request.session['reset_otp_id'] = new_otp.id
            request.session['reset_sent_live'] = delivery_meta.get('sent_live', False)
            request.session['reset_provider'] = delivery_meta.get('provider', '')
            request.session['reset_delivery_error'] = delivery_meta.get('error', '')
            messages.success(request, f"A fresh 6-digit OTP has been sent to your email ({new_otp.destination}).")
            return redirect('forgot_password_verify')

        entered_otp = re.sub(r'\D', '', request.POST.get('otp_code', ''))
        if not otp_obj.is_valid:
            if otp_obj.is_expired:
                messages.error(request, "This OTP has expired. Click 'Resend OTP' to receive a new code.")
            else:
                messages.error(request, "Maximum attempts reached or OTP already used. Please request a new OTP.")
        elif entered_otp == otp_obj.otp_code:
            otp_obj.is_used = True
            otp_obj.save(update_fields=['is_used'])
            request.session['otp_verified_user_id'] = otp_obj.user.id
            for k in ('reset_otp_id', 'reset_sent_live', 'reset_provider', 'reset_delivery_error'):
                request.session.pop(k, None)
            messages.success(request, "✅ OTP verified! Please set your new password below.")
            return redirect('forgot_password_reset')
        else:
            otp_obj.attempts += 1
            otp_obj.save(update_fields=['attempts'])
            remaining = max(0, 5 - otp_obj.attempts)
            messages.error(request, f"Incorrect OTP code. {remaining} attempt(s) remaining.")

    sent_live = bool(request.session.get('reset_sent_live', False))
    show_dev_preview = settings.DEBUG and (not sent_live)

    return render(request, 'accounts/forgot_password_verify.html', {
        'otp_obj': otp_obj,
        'channel_label': 'Email',
        'sent_live': sent_live,
        'provider_name': request.session.get('reset_provider', ''),
        'delivery_error': request.session.get('reset_delivery_error', ''),
        'show_dev_preview': show_dev_preview,
    })


def forgot_password_reset_view(request):
    """
    Step 3 (Admins & Developers): Set a new password after successful OTP verification.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    verified_user_id = request.session.get('otp_verified_user_id')
    if not verified_user_id:
        messages.warning(request, "Please complete OTP verification before resetting your password.")
        return redirect('forgot_password')

    target_user = get_object_or_404(User, pk=verified_user_id)

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
        elif new_password != confirm_password:
            messages.error(request, "Passwords do not match. Please try again.")
        else:
            target_user.set_password(new_password)
            target_user.save()
            profile, _ = UserProfile.objects.get_or_create(user=target_user)
            profile.display_password = new_password
            profile.save()

            request.session.pop('otp_verified_user_id', None)
            messages.success(
                request,
                f"🎉 Password reset successful for '{target_user.username}'! You can now sign in with your new password."
            )
            return redirect('login')

    return render(request, 'accounts/forgot_password_reset.html', {
        'target_user': target_user,
    })


def staff_forgot_password_view(request):
    """
    Staff Forgot Password Flow:
    Sends an email notification to the staff member's Restaurant Admin requesting
    them to reset and share the password, and logs a StaffPasswordRequest alert
    inside the Restaurant Admin's Staff Management page.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    prefill_username = request.GET.get('username', '').strip()
    sent_summary = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        staff_note = request.POST.get('staff_note', '').strip()[:250]
        prefill_username = username

        if not username:
            messages.error(request, "Please enter your staff username.")
        else:
            staff_user = User.objects.filter(username__iexact=username).select_related('profile', 'profile__restaurant').first()
            if not staff_user:
                messages.error(request, f"No staff account found with username '{username}'.")
            else:
                profile = getattr(staff_user, 'profile', None)
                if not profile or profile.role != 'staff':
                    messages.info(
                        request,
                        "This is an Admin or Developer account. Please use OTP Password Recovery instead."
                    )
                    return redirect('forgot_password')

                restaurant = profile.restaurant
                if not restaurant:
                    messages.error(request, "Your staff account is not linked to a restaurant. Please contact support.")
                else:
                    # Collect Restaurant Admin emails (owner + any admins for this restaurant)
                    admin_emails = []
                    primary_admin_name = "Restaurant Admin"
                    if restaurant.owner:
                        primary_admin_name = restaurant.owner.get_full_name() or restaurant.owner.username
                        if restaurant.owner.email:
                            admin_emails.append(restaurant.owner.email.strip())

                    other_admins = UserProfile.objects.filter(
                        restaurant=restaurant,
                        role='admin'
                    ).select_related('user')
                    for ap in other_admins:
                        if ap.user.email and ap.user.email.strip() not in admin_emails:
                            admin_emails.append(ap.user.email.strip())

                    primary_email = admin_emails[0] if admin_emails else ''

                    # Record the request so the Admin sees an immediate alert in Staff Management
                    StaffPasswordRequest.objects.create(
                        staff_user=staff_user,
                        restaurant=restaurant,
                        admin_email=primary_email,
                        staff_note=staff_note,
                    )

                    # Send email notification to the Restaurant Admin(s)
                    if admin_emails:
                        subject = f"[Invenpro] Staff Password Reset Request from @{staff_user.username}"
                        body = (
                            f"Hello {primary_admin_name},\n\n"
                            f"Your staff member has requested password assistance for {restaurant.name} ({restaurant.restaurant_id}):\n\n"
                            f"  • Staff Username: {staff_user.username}\n"
                            f"  • Full Name: {staff_user.get_full_name() or 'Not provided'}\n"
                            f"  • Staff Phone: {profile.phone or 'Not provided'}\n"
                            f"  • Message / Note: {staff_note or 'Forgot login password'}\n\n"
                            f"Please sign in to your Invenpro Staff Management page to reset their password and share the updated credentials with them.\n\n"
                            f"— Invenpro Inventory Management System"
                        )
                        try:
                            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, admin_emails, fail_silently=True)
                        except Exception:
                            pass

                    sent_summary = {
                        'staff_username': staff_user.username,
                        'restaurant_name': restaurant.name,
                        'restaurant_id': restaurant.restaurant_id,
                        'admin_name': primary_admin_name,
                        'masked_admin_email': _mask_email(primary_email) if primary_email else 'Admin Portal Notification',
                        'email_dispatched': bool(admin_emails),
                    }
                    messages.success(
                        request,
                        f"📩 Password request sent to your Restaurant Admin ({primary_admin_name})! They will reset and send you your password shortly."
                    )

    return render(request, 'accounts/staff_forgot_password.html', {
        'prefill_username': prefill_username,
        'sent_summary': sent_summary,
    })
