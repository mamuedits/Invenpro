from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def developer_required(view_func):
    """
    Restricts access strictly to System Developers / SuperUsers.
    Restaurant Admins and Staff are blocked.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        profile = getattr(request.user, 'profile', None)
        if profile and profile.is_developer:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "Access denied: This section is restricted to System Developers only.")
        return redirect('dashboard')
    return _wrapped_view


def admin_required(view_func):
    """
    Restricts access strictly to Restaurant Admins / Owners and Developers.
    Staff members are blocked from staff management, settings, and destructive actions.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        profile = getattr(request.user, 'profile', None)
        if profile and profile.is_admin:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "Access denied: This section is restricted to Restaurant Admins only.")
        return redirect('dashboard')
    return _wrapped_view

