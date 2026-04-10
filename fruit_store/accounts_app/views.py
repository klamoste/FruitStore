from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum
from .forms import RegisterForm, LoginForm, ProfileEditForm
from .models import Profile


def register(request):
    if request.user.is_authenticated:
        return redirect('products:product_list')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user, defaults={'role': 'customer'})
            messages.success(request, 'Registration successful! Please login.')
            return redirect('accounts:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('products:product_list')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'products:product_list')
            return redirect(next_url)
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required(login_url='accounts:login')
def profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'role': 'customer'})
    
    orders = request.user.order_set.all()
    order_count = orders.count()
    total_spent = orders.aggregate(total=Sum('total_price'))['total'] or 0

    if request.method == 'POST':
        form = ProfileEditForm(request.POST)
        if form.is_valid():
            user = request.user
            user.username = form.cleaned_data['username']
            user.email = form.cleaned_data['email']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            user.save()
            
            profile.address = form.cleaned_data['address']
            profile.contact_number = form.cleaned_data['contact_number']
            profile.city = form.cleaned_data['city']
            profile.state = form.cleaned_data['state']
            profile.save()

            if password:
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)

            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileEditForm(initial={
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'address': profile.address,
            'contact_number': profile.contact_number,
            'city': profile.city,
            'state': profile.state,
        })
    
    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile,
        'order_count': order_count,
        'total_spent': total_spent,
    })
