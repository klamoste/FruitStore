from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum
from .forms import RegisterForm, LoginForm, ProfileEditForm
from .models import Profile


def get_profile_completion_data(user, profile):
    summary_fields = [
        ('Full Name', user.get_full_name()),
        ('Username', user.username),
        ('Email', user.email),
        ('Phone', profile.contact_number),
        ('Address', profile.address),
        ('City', profile.city),
    ]
    missing_fields = [label for label, value in summary_fields if not (value and str(value).strip())]
    completed_fields = len(summary_fields) - len(missing_fields)
    completion_percent = int((completed_fields / len(summary_fields)) * 100)
    return {
        'missing_fields': missing_fields,
        'completed_fields': completed_fields,
        'total_fields': len(summary_fields),
        'completion_percent': completion_percent,
        'is_complete': not missing_fields,
    }


def register(request):
    if request.user.is_authenticated:
        return redirect('products:home')
    
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
        return redirect('products:home')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'products:home')
            return redirect(next_url)
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.method != 'POST':
        return redirect('accounts:profile' if request.user.is_authenticated else 'accounts:login')
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required(login_url='accounts:login')
def profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'role': 'customer'})
    completion = get_profile_completion_data(request.user, profile)
    
    orders = request.user.order_set.all()
    order_count = orders.count()
    total_spent = orders.aggregate(total=Sum('total_price'))['total'] or 0

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, user=request.user)
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
            profile.avatar_template = form.cleaned_data.get('avatar_template') or profile.avatar_template
            uploaded_image = form.cleaned_data.get('profile_image')
            if uploaded_image:
                profile.avatar_mode = 'upload'
                profile.profile_image = uploaded_image
            else:
                profile.avatar_mode = form.cleaned_data.get('avatar_mode') or profile.avatar_mode
            profile.save()

            if password:
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)

            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileEditForm(user=request.user, initial={
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'address': profile.address,
            'contact_number': profile.contact_number,
            'city': profile.city,
            'state': profile.state,
            'avatar_mode': profile.avatar_mode,
            'avatar_template': profile.avatar_template,
        })
    
    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile,
        'order_count': order_count,
        'total_spent': total_spent,
        'profile_completion': completion,
    })


@login_required(login_url='accounts:login')
def delete_account(request):
    if request.method == 'POST':
        if request.POST.get('confirm') == 'yes':
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, 'Your account has been deleted.')
            return redirect('products:home')
        messages.error(request, 'Please confirm account deletion.')
    return redirect('accounts:profile')
