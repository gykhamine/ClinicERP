from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles and not request.user.is_superuser:
                messages.error(request, "Accès refusé : vous n'avez pas les droits nécessaires.")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

def personnel_only(view_func):
    return role_required('chef','medecin','infirmier','pharmacien','laborantin','receptionniste','comptable')(view_func)

def chef_only(view_func):
    return role_required('chef')(view_func)

def medecin_only(view_func):
    return role_required('chef','medecin')(view_func)

def pharmacien_only(view_func):
    return role_required('chef','pharmacien')(view_func)

def laborantin_only(view_func):
    return role_required('chef','laborantin')(view_func)

def comptable_only(view_func):
    return role_required('chef','comptable','receptionniste')(view_func)
