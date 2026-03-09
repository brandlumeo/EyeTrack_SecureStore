from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.db.models import Count, Sum
from orders.models import Order


def _apply_form_styles(form):
    for _, field in form.fields.items():
        base_class = field.widget.attrs.get('class', '')
        field.widget.attrs['class'] = f"{base_class} form-control premium-input".strip()
    return form


def register_view(request):
    if request.method == 'POST':
        form = _apply_form_styles(UserCreationForm(request.POST))
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful.')
            return redirect('product_list')
    else:
        form = _apply_form_styles(UserCreationForm())
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = _apply_form_styles(AuthenticationForm(request, data=request.POST))
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f'You are now logged in as {username}.')
                return redirect('product_list')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = _apply_form_styles(AuthenticationForm())
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have successfully logged out.')
    return redirect('product_list')

def order_history(request):
    if not request.user.is_authenticated:
        return redirect('login')

    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    order_summary = orders.aggregate(
        total_orders=Count('id'),
        total_spend=Sum('total'),
    )
    status_counts = {
        'pending': orders.filter(status='Pending').count(),
        'processing': orders.filter(status='Processing').count(),
        'completed': orders.filter(status='Completed').count(),
        'cancelled': orders.filter(status='Cancelled').count(),
    }
    context = {
        'orders': orders,
        'order_summary': order_summary,
        'status_counts': status_counts,
        'latest_order': orders.first(),
    }
    return render(request, 'accounts/order_history.html', context)
