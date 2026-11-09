"""
Admin Dashboard Views for EyeTrack_SecureStore
Provides comprehensive admin interface with analytics and management features
"""
from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Avg, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import csv
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.contrib.sessions.models import Session
import decimal

from orders.models import Order, OrderItem, Payment, Shipment, DeliveryAgent, DeliveryAssignment, InstallationBooking, InstallationPhoto, Invoice, ReturnRequest
from orders.utils import render_to_pdf
from store.models import Product, Category, Coupon, Review, ServiceableArea, ReviewMedia
from accounts.models import Profile, Address, Notification
from store.specs import (
    SPEC_TYPE_BIOMETRIC,
    SPEC_TYPE_CCTV,
    SPEC_TYPE_NETWORK,
    SPEC_TYPE_SMART_LOCK,
    SPEC_TYPE_VIDEO_DOOR_PHONE,
    get_product_spec_type,
)
from admin_dashboard.forms import (
    CouponForm, CategoryForm, ProductForm, CameraSpecForm,
    BiometricSpecForm, SmartLockSpecForm, NetworkSpecForm, VideoDoorPhoneSpecForm,
    DeliveryAgentForm, AssignAgentForm,
    ServiceableAreaForm, FAQCategoryForm, FAQForm,
)


def is_admin(user):
    """Check if user is admin or staff"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def _get_related_spec_instance(product, attr_name):
    if not product or not hasattr(product, attr_name):
        return None
    return getattr(product, attr_name)


def _build_spec_form(category_or_product, product=None, data=None):
    spec_type = get_product_spec_type(category_or_product)

    if spec_type == SPEC_TYPE_CCTV:
        return CameraSpecForm(data, instance=product) if data is not None else CameraSpecForm(instance=product)
    if spec_type == SPEC_TYPE_VIDEO_DOOR_PHONE:
        return (
            VideoDoorPhoneSpecForm(data, instance=product)
            if data is not None
            else VideoDoorPhoneSpecForm(instance=product)
        )
    if spec_type == SPEC_TYPE_BIOMETRIC:
        instance = _get_related_spec_instance(product, "biometric_specs")
        return BiometricSpecForm(data, instance=instance) if data is not None else BiometricSpecForm(instance=instance)
    if spec_type == SPEC_TYPE_SMART_LOCK:
        instance = _get_related_spec_instance(product, "smartlock_specs")
        return SmartLockSpecForm(data, instance=instance) if data is not None else SmartLockSpecForm(instance=instance)
    if spec_type == SPEC_TYPE_NETWORK:
        instance = _get_related_spec_instance(product, "network_specs")
        return NetworkSpecForm(data, instance=instance) if data is not None else NetworkSpecForm(instance=instance)

    return None


@login_required
@user_passes_test(is_admin)
def product_edit(request, product_id=None):
    """View to add or edit a product with its specifications"""
    if product_id:
        product = get_object_or_404(Product, id=product_id)
        page_title = f'Edit Product: {product.name}'
    else:
        product = None
        page_title = 'Add New Product'
        
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        
        # Determine which spec form to use based on category
        # NOTE: In a real scenario, this might be better handled via AJAX on the frontend
        # For now, we'll check the category from the POST data
        category_id = request.POST.get('category')
        category = get_object_or_404(Category, id=category_id) if category_id else None
        
        spec_form = _build_spec_form(category, product=form.instance, data=request.POST) if category else None
        
        if form.is_valid() and (spec_form is None or spec_form.is_valid()):
            new_product = form.save(commit=False)
            if spec_form:
                if isinstance(spec_form, (VideoDoorPhoneSpecForm, CameraSpecForm)):
                    for field_name in spec_form.fields:
                        setattr(new_product, field_name, spec_form.cleaned_data.get(field_name))
                    new_product.save()
                else:
                    new_product.save()
                    spec = spec_form.save(commit=False)
                    spec.product = new_product
                    spec.save()
            else:
                new_product.save()
            
            messages.success(request, f"Product '{new_product.name}' saved successfully.")
            return redirect('admin_dashboard:products_overview')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm(instance=product)
        spec_form = _build_spec_form(product.category, product=product) if product and product.category else None

    context = {
        'page_title': page_title,
        'form': form,
        'spec_form': spec_form,
        'product': product,
        'categories': Category.objects.all(),
    }
    return render(request, 'admin_dashboard/product_form.html', context)
from accounts.models import Profile


@login_required
@user_passes_test(is_admin)
def shipments_overview(request):
    """View to list and manage shipments"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    shipments = Shipment.objects.select_related('order').order_by('-created_at')
    
    if search_query:
        shipments = shipments.filter(
            Q(order__id__icontains=search_query) |
            Q(order__tracking_number__icontains=search_query) |
            Q(order__full_name__icontains=search_query) |
            Q(carrier__icontains=search_query)
        )
        
    if status_filter:
        shipments = shipments.filter(order__shipping_status=status_filter)
        
    paginator = Paginator(shipments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Shipments & Logistics',
        'shipments': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'admin_dashboard/shipments_overview.html', context)


@login_required
@user_passes_test(is_admin)
def order_detail(request, order_id):
    """Detailed order management view"""
    order = get_object_or_404(Order, id=order_id)
    items = order.items.select_related('product').all()
    payments = order.payments.all()
    
    try:
        installation = order.installation_booking
    except Exception:
        installation = None

    try:
        shipment = order.shipment
    except Exception:
        shipment = None

    return_requests = order.return_requests.all()

    # Handle status updates
    if request.method == 'POST':
        if 'update_order_status' in request.POST:
            new_status = request.POST.get('order_status')
            if new_status in dict(Order.OrderStatus.choices):
                order.order_status = new_status
                order.save()
                messages.success(request, f"Order status updated to {order.get_order_status_display()}.")
                
        elif 'update_payment_status' in request.POST:
            new_status = request.POST.get('payment_status')
            if new_status in dict(Order.PaymentStatus.choices):
                order.payment_status = new_status
                order.save()
                messages.success(request, f"Payment status updated to {order.get_payment_status_display()}.")
                
        elif 'update_shipping' in request.POST:
            new_status = request.POST.get('shipping_status')
            tracking = request.POST.get('tracking_number')
            if new_status in dict(Order.ShippingStatus.choices):
                order.shipping_status = new_status
                order.tracking_number = tracking
                order.save()
                
                # Update or create Shipment record if it exists
                shipment, created = Shipment.objects.get_or_create(order=order)
                if new_status == Order.ShippingStatus.IN_TRANSIT and not shipment.shipped_at:
                    shipment.shipped_at = timezone.now()
                elif new_status == Order.ShippingStatus.DELIVERED and not shipment.delivered_at:
                    shipment.delivered_at = timezone.now()
                shipment.save()
                
                messages.success(request, f"Shipping details updated successfully.")

        elif 'update_installation' in request.POST and installation:
            from orders.models import InstallationBooking
            new_status = request.POST.get('installation_status')
            if new_status in dict(InstallationBooking.BookingStatus.choices):
                installation.status = new_status
                
                # New: Technician Link
                tech_id = request.POST.get('technician_id')
                if tech_id:
                    from orders.models import Technician
                    installation.technician = Technician.objects.filter(id=tech_id).first()
                
                installation.technician_name = request.POST.get('technician_name', '')
                installation.technician_phone = request.POST.get('technician_phone', '')
                installation.technician_verified = 'technician_verified' in request.POST
                installation.technician_notes = request.POST.get('technician_notes', '')
                installation.save()
                
                # Handle Photo Uploads
                before_photos = request.FILES.getlist('before_photos')
                after_photos = request.FILES.getlist('after_photos')
                
                for photo in before_photos:
                    InstallationPhoto.objects.create(booking=installation, image=photo, label='before')
                for photo in after_photos:
                    InstallationPhoto.objects.create(booking=installation, image=photo, label='after')

                # Auto-generate certificate if marked completed
                if new_status == 'completed' and not installation.completion_certificate:
                    try:
                        context = {
                            'order': order,
                            'installation': installation,
                            'items': order.items.all(),
                            'date': timezone.now()
                        }
                        pdf_content = render_to_pdf('orders/installation_certificate.html', context)
                        if pdf_content:
                            from django.core.files.base import ContentFile
                            filename = f"certificate_{order.id}.pdf"
                            installation.completion_certificate.save(filename, ContentFile(pdf_content))
                            installation.certificate_generated_at = timezone.now()
                            installation.save()
                            messages.info(request, "Installation certificate generated successfully.")
                    except Exception as e:
                        messages.warning(request, f"Certificate generation failed: {str(e)}")

                messages.success(request, f"Installation details and documentation updated successfully.")
                
        return redirect('admin_dashboard:order_detail', order_id=order.id)
        
    context = {
        'page_title': f'Order Detail: {order.formatted_id}',
        'order': order,
        'items': items,
        'payments': payments,
        'shipment': shipment,
        'installation': installation,
        'return_requests': return_requests,
        'order_status_choices': Order.OrderStatus.choices,
        'payment_status_choices': Order.PaymentStatus.choices,
        'shipping_status_choices': Order.ShippingStatus.choices,
    }

    if shipment:
        from orders.models import DeliveryAgent
        context['delivery_agents'] = DeliveryAgent.objects.filter(is_active=True)

    if installation:
        from orders.models import InstallationBooking, Technician
        context['installation_status_choices'] = InstallationBooking.BookingStatus.choices
        context['technicians'] = Technician.objects.filter(is_active=True)

    return render(request, 'admin_dashboard/order_detail.html', context)





@login_required
@user_passes_test(is_admin)
def dashboard(request):
    """Main admin dashboard with overview statistics"""
    
    # Get date ranges for analytics
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    
    # Basic Counts
    total_orders = Order.objects.count()
    total_products = Product.objects.count()
    total_users = User.objects.count()
    total_categories = Category.objects.count()
    
    # Revenue Analytics
    total_revenue = Order.objects.aggregate(
        total=Sum('total')
    )['total'] or Decimal('0.00')
    
    # Last 30 days revenue
    order_activity_30_days = Order.objects.filter(
        created_at__date__gte=last_30_days
    ).aggregate(total=Sum('total'), count=Count('id'))
    revenue_30_days = order_activity_30_days['total'] or Decimal('0.00')
    
    # Last 7 days revenue
    revenue_7_days = Order.objects.filter(
        created_at__date__gte=last_7_days
    ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    
    # Order Status Breakdown
    order_stats = Order.objects.values('order_status').annotate(
        count=Count('id')
    ).order_by('order_status')
    
    order_status_data = {item['order_status']: item['count'] for item in order_stats}
    
    # Recent Orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    # Top Products by Sales
    top_products = OrderItem.objects.values(
        'product__name', 'product__id'
    ).annotate(
        total_sold=Sum('quantity'),
        revenue=Sum('price')
    ).order_by('-total_sold')[:10]
    
    # New Users (Last 30 days)
    new_users_30_days = User.objects.filter(
        date_joined__date__gte=last_30_days
    ).count()
    
    # Active Products (in stock)
    active_products = Product.objects.filter(is_available=True, stock__gt=0).count()
    
    # Calculate product performance threshold
    product_performance_threshold = int(total_products * 0.8)
    product_performance_good = active_products > product_performance_threshold
    
    # Low Stock Alert
    low_stock_qs = Product.objects.filter(
        is_available=True,
        stock__lt=5,
        stock__gt=0
    ).order_by('stock')
    
    low_stock_products = low_stock_qs.count()
    low_stock_items = low_stock_qs[:5]
    
    # Out of Stock Products
    out_of_stock_products = Product.objects.filter(
        is_available=True,
        stock=0
    ).count()

    # Installation stats
    total_installations = InstallationBooking.objects.count()
    pending_installations = InstallationBooking.objects.filter(status='pending').count()
    active_installations = InstallationBooking.objects.filter(status='assigned').count()
    
    # Payment Method Distribution
    payment_stats = Order.objects.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total')
    ).order_by('-count')
    
    # Monthly Sales Trend (Last 6 months)
    monthly_sales = []
    for i in range(6):
        month_start = today.replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_revenue = Order.objects.filter(
            created_at__date__gte=month_start,
            created_at__date__lte=month_end
        ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        
        monthly_sales.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': month_revenue
        })
    
    monthly_sales.reverse()  # Show oldest to newest
    
    # Abandoned Carts Calculation
    abandoned_carts_count = 0
    abandoned_revenue_potential = Decimal('0.00')
    
    # Get all non-expired sessions
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for s in sessions:
        try:
            data = s.get_decoded()
            if 'cart' in data and data['cart']:
                cart = data['cart']
                has_items = False
                cart_total = Decimal('0.00')
                for item_id, item_data in cart.items():
                    if 'price' in item_data and 'quantity' in item_data:
                        has_items = True
                        try:
                            # Using Decimal to handle potential string/float precision issues
                            price = Decimal(str(item_data['price']))
                            quantity = int(item_data['quantity'])
                            cart_total += price * quantity
                        except (ValueError, TypeError, decimal.InvalidOperation):
                            pass
                
                if has_items:
                    # Let's consider a cart abandoned if it hasn't resulted in an order in the last 24 hrs
                    # Since we don't easily know which user maps to which session without auth data or deep parsing,
                    # we'll just count all active carts as "abandoned/active revenue potential"
                    abandoned_carts_count += 1
                    abandoned_revenue_potential += cart_total
        except Exception:
            pass
            
    context = {
        'page_title': 'Admin Dashboard',
        
        # Overview Statistics
        'total_orders': total_orders,
        'orders_30_days': order_activity_30_days['count'],
        'total_installations': total_installations,
        'pending_installations': pending_installations,
        'active_installations': active_installations,
        'total_products': total_products,
        'total_users': total_users,
        'total_categories': total_categories,
        
        # Revenue Analytics
        'total_revenue': total_revenue,
        'revenue_30_days': revenue_30_days,
        'revenue_7_days': revenue_7_days,
        
        # Abandoned Carts
        'abandoned_carts_count': abandoned_carts_count,
        'abandoned_revenue_potential': abandoned_revenue_potential,
        
        # Growth Metrics
        'new_users_30_days': new_users_30_days,
        'active_products': active_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'product_performance_good': product_performance_good,
        
        # Order Analytics
        'order_status_data': order_status_data,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'payment_stats': payment_stats,
        'monthly_sales': monthly_sales,
        
        # Percentages and Calculations
        'revenue_growth_7_days': round((revenue_7_days / max(revenue_30_days - revenue_7_days, 1)) * 100, 1) if revenue_30_days > revenue_7_days else 0,
        'avg_order_value': round(total_revenue / max(total_orders, 1), 2),
        'conversion_rate': round((total_orders / max(total_users, 1)) * 100, 2),
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def orders_overview(request):
    """Detailed orders management view"""
    status_filter = request.GET.get('status', '')
    payment_filter = request.GET.get('payment', '')
    search_query = request.GET.get('search', '')
    export_csv = request.GET.get('export') == 'csv'
    
    orders = Order.objects.select_related('user').order_by('-created_at')
    
    if status_filter:
        orders = orders.filter(order_status=status_filter)
    
    if payment_filter:
        orders = orders.filter(payment_status=payment_filter)
        
    if search_query:
        orders = orders.filter(
            Q(id__icontains=search_query) | 
            Q(full_name__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
        
    if export_csv:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders.csv"'
        writer = csv.writer(response)
        writer.writerow(['Order ID', 'Customer', 'Email', 'Status', 'Payment', 'Total', 'Date'])
        for order in orders:
            customer_name = order.user.get_full_name() if order.user else order.full_name
            writer.writerow([
                order.id, 
                customer_name, 
                order.email, 
                order.get_order_status_display(), 
                order.get_payment_status_display(), 
                order.total, 
                order.created_at.strftime('%b %d, %Y %H:%M')
            ])
        return response

    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Order statistics
    order_stats = Order.objects.values('order_status').annotate(
        count=Count('id')
    ).order_by('order_status')
    
    context = {
        'page_title': 'Orders Management',
        'orders': page_obj,
        'page_obj': page_obj,
        'order_stats': order_stats,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'search_query': search_query,
        'total_orders': orders.count(),
    }
    
    return render(request, 'admin_dashboard/orders_overview.html', context)


@login_required
@user_passes_test(is_admin)
def products_overview(request):
    """Products management overview"""
    category_filter = request.GET.get('category', '')
    availability_filter = request.GET.get('available', '')
    search_query = request.GET.get('search', '')
    export_csv = request.GET.get('export') == 'csv'
    
    products = Product.objects.select_related('category').order_by('-created_at')
    
    if category_filter:
        products = products.filter(category__id=category_filter)
    
    if availability_filter:
        if availability_filter == 'in_stock':
            products = products.filter(stock__gt=0, is_available=True)
        elif availability_filter == 'low_stock':
            products = products.filter(stock__lte=5, stock__gt=0, is_available=True)
        elif availability_filter == 'out_of_stock':
            products = products.filter(stock=0, is_available=True)
            
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(slug__icontains=search_query) |
            Q(description__icontains=search_query)
        )
        
    if export_csv:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Category', 'Price', 'Stock', 'Available', 'Created At'])
        for product in products:
            writer.writerow([
                product.id, 
                product.name, 
                product.category.name if product.category else '', 
                product.price, 
                product.stock, 
                'Yes' if product.is_available else 'No', 
                product.created_at.strftime('%b %d, %Y')
            ])
        return response

    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    # Calculate product statistics
    in_stock_count = Product.objects.filter(stock__gt=0, is_available=True).count()
    low_stock_count = Product.objects.filter(stock__lte=5, stock__gt=0, is_available=True).count()
    
    # Map categories to dictionaries to avoid `==` inside the Django template
    categories_data = []
    for c in Category.objects.all():
        categories_data.append({
            'id': c.id,
            'name': c.name,
            'selected': str(c.id) == category_filter
        })

    # Prepare availability options
    availability_options = [
        {'value': 'in_stock', 'label': 'In Stock', 'selected': availability_filter == 'in_stock'},
        {'value': 'low_stock', 'label': 'Low Stock', 'selected': availability_filter == 'low_stock'},
        {'value': 'out_of_stock', 'label': 'Out of Stock', 'selected': availability_filter == 'out_of_stock'},
    ]
    
    context = {
        'page_title': 'Products Management',
        'products': page_obj,
        'page_obj': page_obj,
        'categories_data': categories_data,
        'availability_options': availability_options,
        'category_filter': category_filter,
        'availability_filter': availability_filter,
        'search_query': search_query,
        'total_products': products.count(),
        'total_categories': Category.objects.count(), # Use direct count for total categories
        'in_stock_count': in_stock_count,
        'low_stock_count': low_stock_count,
    }
    
    return render(request, 'admin_dashboard/products_overview.html', context)


@login_required
@user_passes_test(is_admin)
def users_overview(request):
    """Users management overview"""
    search_query = request.GET.get('search', '')
    export_csv = request.GET.get('export') == 'csv'
    
    users = User.objects.select_related('profile').order_by('-date_joined')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
        
    if export_csv:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Username', 'Email', 'Full Name', 'Verified', 'Role', 'Joined Date'])
        for u in users:
            verified = u.profile.email_verified if hasattr(u, 'profile') else False
            role = 'Superuser' if u.is_superuser else ('Staff' if u.is_staff else 'Customer')
            writer.writerow([
                u.id, 
                u.username, 
                u.email, 
                u.get_full_name(), 
                'Yes' if verified else 'No', 
                role, 
                u.date_joined.strftime('%b %d, %Y')
            ])
        return response

    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # User statistics
    total_users = User.objects.count()
    verified_users = User.objects.filter(profile__email_verified=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    
    # Calculate verified user percentage
    verified_percentage = round((verified_users / max(total_users, 1)) * 100, 1) if total_users > 0 else 0
    
    # Recent users (last 30 days)
    recent_users_count = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    context = {
        'page_title': 'Users Management',
        'users': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'total_users': total_users,
        'verified_users': verified_users,
        'staff_users': staff_users,
        'superusers': superusers,
        'verified_percentage': verified_percentage,
        'recent_users_count': recent_users_count,
    }
    
    return render(request, 'admin_dashboard/users_overview.html', context)


@login_required
@user_passes_test(is_admin)
def analytics(request):
    """Detailed analytics view"""
    # Date range filters
    days = int(request.GET.get('days', 30))
    export_csv = request.GET.get('export') == 'csv'
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Sales Analytics
    orders_in_period = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    daily_sales = []
    for i in range(min(days, 30)):  # Limit to 30 days for performance
        date = end_date - timedelta(days=i)
        daily_orders = orders_in_period.filter(created_at__date=date)
        daily_revenue = daily_orders.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        
        daily_sales.append({
            'date': date.strftime('%b %d, %Y'),
            'orders': daily_orders.count(),
            'revenue': daily_revenue
        })
    
    daily_sales.reverse()  # Show oldest to newest
    
    # Product Performance
    product_performance = OrderItem.objects.filter(
        order__created_at__date__gte=start_date
    ).values(
        'product__name', 'product__category__name'
    ).annotate(
        total_sold=Sum('quantity'),
        revenue=Sum('price'),
        orders=Count('order', distinct=True)
    ).order_by('-revenue')[:20]
    
    # Category Performance
    category_performance = OrderItem.objects.filter(
        order__created_at__date__gte=start_date
    ).values(
        'product__category__name'
    ).annotate(
        total_sold=Sum('quantity'),
        revenue=Sum('price'),
        orders=Count('order', distinct=True)
    ).order_by('-revenue')
    
    if export_csv:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="analytics_{days}days.csv"'
        writer = csv.writer(response)
        
        # Write Overview Stats
        writer.writerow(['Analytics Export', f'Last {days} days'])
        writer.writerow([])
        
        # Write Daily Sales
        writer.writerow(['Daily Sales'])
        writer.writerow(['Date', 'Orders', 'Revenue'])
        for day in daily_sales:
            writer.writerow([day['date'], day['orders'], day['revenue']])
        writer.writerow([])
        
        # Write Product Performance
        writer.writerow(['Top Products'])
        writer.writerow(['Product', 'Category', 'Units Sold', 'Revenue', 'Orders'])
        for p in product_performance:
            writer.writerow([p['product__name'], p['product__category__name'], p['total_sold'], p['revenue'], p['orders']])
            
        return response
    
    # Calculate additional metrics
    total_orders_period = orders_in_period.count()
    orders_per_day = round(total_orders_period / max(days, 1), 1) if days > 0 else 0
    
    context = {
        'page_title': 'Analytics Dashboard',
        'daily_sales': daily_sales,
        'product_performance': product_performance,
        'category_performance': category_performance,
        'period_days': days,
        'total_revenue_period': orders_in_period.aggregate(total=Sum('total'))['total'] or Decimal('0.00'),
        'total_orders_period': total_orders_period,
        'avg_order_value_period': orders_in_period.aggregate(avg=Avg('total'))['avg'] or Decimal('0.00'),
        'orders_per_day': orders_per_day,
    }
    
    return render(request, 'admin_dashboard/analytics.html', context)


@login_required
@user_passes_test(is_admin)
def coupons_overview(request):
    """View to list and manage promotional coupons"""
    search_query = request.GET.get('search', '')
    
    coupons = Coupon.objects.all().order_by('-valid_from')
    
    if search_query:
        coupons = coupons.filter(code__icontains=search_query)
        
    paginator = Paginator(coupons, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Coupons Management',
        'coupons': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'admin_dashboard/coupons_overview.html', context)


@login_required
@user_passes_test(is_admin)
def coupon_edit(request, coupon_id=None):
    """View to add a new coupon or edit an existing one"""
    if coupon_id:
        coupon = get_object_or_404(Coupon, id=coupon_id)
        page_title = f"Edit Coupon: {coupon.code}"
    else:
        coupon = None
        page_title = "Add New Coupon"
        
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            saved_coupon = form.save()
            messages.success(request, f"Coupon '{saved_coupon.code}' successfully saved.")
            return redirect('admin_dashboard:coupons_overview')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CouponForm(instance=coupon)
        
    context = {
        'page_title': page_title,
        'form': form,
        'coupon': coupon,
    }
    return render(request, 'admin_dashboard/coupon_form.html', context)


@login_required
@user_passes_test(is_admin)
def categories_overview(request):
    """View to list and manage categories"""
    search_query = request.GET.get('search', '')
    
    # We annotate each category with the number of products it has
    categories = Category.objects.annotate(product_count=Count('products')).order_by('name')
    
    if search_query:
        categories = categories.filter(name__icontains=search_query)
        
    paginator = Paginator(categories, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Categories Management',
        'categories': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'admin_dashboard/categories_overview.html', context)


@login_required
@user_passes_test(is_admin)
def category_edit(request, category_id=None):
    """View to add or edit a category"""
    if category_id:
        category = get_object_or_404(Category, id=category_id)
        page_title = f"Edit Category: {category.name}"
    else:
        category = None
        page_title = "Add New Category"
        
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            saved_category = form.save()
            messages.success(request, f"Category '{saved_category.name}' successfully saved.")
            return redirect('admin_dashboard:categories_overview')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CategoryForm(instance=category)
        
    context = {
        'page_title': page_title,
        'form': form,
        'category': category,
    }
    return render(request, 'admin_dashboard/category_form.html', context)


@login_required
@user_passes_test(is_admin)
def payments_overview(request):
    """View to list and manage payment transactions"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    payments = Payment.objects.select_related('order', 'order__user').order_by('-created_at')
    
    if search_query:
        payments = payments.filter(
            Q(transaction_id__icontains=search_query) |
            Q(order__id__icontains=search_query) |
            Q(order__full_name__icontains=search_query)
        )
        
    if status_filter:
        payments = payments.filter(status=status_filter)
        
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Payment Transactions',
        'payments': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'admin_dashboard/payments_overview.html', context)


@login_required
@user_passes_test(is_admin)
def get_spec_form(request):
    """AJAX view to get specification form HTML based on category"""
    category_id = request.GET.get('category_id')
    product_id = request.GET.get('product_id')
    
    if not category_id:
        return HttpResponse('')
        
    category = get_object_or_404(Category, id=category_id)
    product = None
    if product_id:
        product = get_object_or_404(Product, id=product_id)
    spec_form = _build_spec_form(category, product=product)
        
    if spec_form:
        html = '<div class="row g-3">'
        for field in spec_form:
            is_checkbox = field.field.widget.input_type == 'checkbox'
            col_class = 'col-md-6'
            html += f'<div class="{col_class} mb-2">'
            html += f'<label class="form-label text-light-70 small fw-medium">{field.label}</label>'
            
            # Add premium classes to the field widget
            field_classes = "form-control bg-dark-soft text-light border-secondary"
            if isinstance(field.field.widget, forms.Select):
                field_classes = field_classes.replace("form-control", "form-select")
            elif isinstance(field.field.widget, forms.CheckboxInput):
                field_classes = "form-check-input"
                
            field.field.widget.attrs.update({"class": field_classes})
            
            html += str(field)
            if field.help_text:
                html += f'<small class="text-light-50 d-block mt-1" style="font-size: 0.7rem; opacity: 0.8;">{field.help_text}</small>'
            html += '</div>'
        html += '</div>'
        return HttpResponse(html)
    
    return HttpResponse('')

@login_required
@user_passes_test(is_admin)
@require_POST
def product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    name = product.name
    product.delete()
    messages.success(request, f'Product "{name}" deleted successfully.')
    return redirect('admin_dashboard:products_overview')

@login_required
@user_passes_test(is_admin)
@require_POST
def category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    name = category.name
    category.delete()
    messages.success(request, f'Category "{name}" deleted successfully.')
    return redirect('admin_dashboard:categories_overview')

@login_required
@user_passes_test(is_admin)
@require_POST
def coupon_delete(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    code = coupon.code
    coupon.delete()
    messages.success(request, f'Coupon "{code}" deleted successfully.')
    return redirect('admin_dashboard:coupons_overview')

@login_required
@user_passes_test(is_admin)
@require_POST
def user_delete(request, user_id):
    user_to_delete = get_object_or_404(User, id=user_id)
    if user_to_delete == request.user:
        messages.error(request, 'You cannot delete yourself.')
    elif user_to_delete.is_superuser and not request.user.is_superuser:
        messages.error(request, 'You cannot delete a superuser.')
    else:
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f'User "{username}" deleted successfully.')
    return redirect('admin_dashboard:users_overview')

@login_required
@user_passes_test(is_admin)
@require_POST
def order_delete(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    # We need the order object to get formatted_id, or just use the ID if deleted
    messages.success(request, f'Order #{order_id} deleted successfully.')
    return redirect('admin_dashboard:orders_overview')

@login_required
@user_passes_test(is_admin)
def reviews_overview(request):
    """View to list and manage product reviews"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    reviews = Review.objects.select_related('product', 'user').order_by('-created_at')
    
    if search_query:
        reviews = reviews.filter(
            Q(product__name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(review__icontains=search_query)
        )
        
    if status_filter:
        if status_filter == 'active':
            reviews = reviews.filter(status=True)
        elif status_filter == 'inactive':
            reviews = reviews.filter(status=False)
            
    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Reviews Management',
        'reviews': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_reviews': reviews.count(),
    }
    return render(request, 'admin_dashboard/reviews_overview.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def review_delete(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.delete()
    messages.success(request, 'Review deleted successfully.')
    return redirect('admin_dashboard:reviews_overview')


@login_required
@user_passes_test(is_admin)
@require_POST
def review_toggle_status(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.status = not review.status
    review.save()
    status_msg = "activated" if review.status else "deactivated"
    messages.success(request, f'Review has been {status_msg}.')
    return redirect('admin_dashboard:reviews_overview')


# ──────────────────────────────────────────────────────────────────────────────
# DELIVERY MANAGEMENT VIEWS
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def delivery_board(request):
    """Daily delivery operations board — shows today's orders by delivery status."""
    today = timezone.now().date()

    # Orders that need assigning (confirmed / processing, no assignment yet)
    unassigned_orders = (
        Order.objects.filter(
            order_status__in=[
                Order.OrderStatus.CONFIRMED,
                Order.OrderStatus.PROCESSING,
            ]
        )
        .exclude(delivery_assignment__isnull=False)
        .select_related('user')
        .prefetch_related('items')
        .order_by('created_at')
    )

    # Orders assigned and out for delivery
    in_transit_orders = (
        Order.objects.filter(
            order_status=Order.OrderStatus.SHIPPED
        )
        .select_related('user', 'delivery_assignment__agent')
        .prefetch_related('items')
        .order_by('created_at')
    )

    # Orders delivered today
    delivered_today = (
        Order.objects.filter(
            order_status=Order.OrderStatus.DELIVERED,
            updated_at__date=today,
        )
        .select_related('user', 'delivery_assignment__agent')
        .order_by('-updated_at')
    )

    active_agents = DeliveryAgent.objects.filter(is_active=True)

    context = {
        'page_title': 'Delivery Board',
        'unassigned_orders': unassigned_orders,
        'in_transit_orders': in_transit_orders,
        'delivered_today': delivered_today,
        'active_agents': active_agents,
        'today': today,
        'unassigned_count': unassigned_orders.count(),
        'in_transit_count': in_transit_orders.count(),
        'delivered_count': delivered_today.count(),
    }
    return render(request, 'admin_dashboard/delivery_board.html', context)


@login_required
@user_passes_test(is_admin)
def delivery_agents_overview(request):
    """List all delivery agents with their active assignment counts."""
    agents = DeliveryAgent.objects.all().order_by('-is_active', 'name')
    context = {
        'page_title': 'Delivery Agents',
        'agents': agents,
        'total_agents': agents.count(),
        'active_agents': agents.filter(is_active=True).count(),
    }
    return render(request, 'admin_dashboard/delivery_agents.html', context)


@login_required
@user_passes_test(is_admin)
def delivery_agent_edit(request, agent_id=None):
    """Add or edit a delivery agent."""
    if agent_id:
        agent = get_object_or_404(DeliveryAgent, id=agent_id)
        page_title = f'Edit Agent: {agent.name}'
    else:
        agent = None
        page_title = 'Add Delivery Agent'

    if request.method == 'POST':
        form = DeliveryAgentForm(request.POST, instance=agent)
        if form.is_valid():
            saved = form.save()
            messages.success(request, f"Agent '{saved.name}' saved successfully.")
            return redirect('admin_dashboard:delivery_agents')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DeliveryAgentForm(instance=agent)

    context = {
        'page_title': page_title,
        'form': form,
        'agent': agent,
    }
    return render(request, 'admin_dashboard/delivery_agent_form.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def delivery_agent_delete(request, agent_id):
    """Delete a delivery agent."""
    agent = get_object_or_404(DeliveryAgent, id=agent_id)
    name = agent.name
    agent.delete()
    messages.success(request, f'Agent "{name}" deleted successfully.')
    return redirect('admin_dashboard:delivery_agents')


@login_required
@user_passes_test(is_admin)
def assign_delivery_agent(request, order_id):
    """Assign or update a delivery agent for an order, and set ETA."""
    order = get_object_or_404(Order, id=order_id)

    # Get existing assignment if any
    assignment = getattr(order, 'delivery_assignment', None)

    if request.method == 'POST':
        form = AssignAgentForm(request.POST, instance=assignment)
        if form.is_valid():
            new_assignment = form.save(commit=False)
            new_assignment.order = order
            new_assignment.save()

            # Sync estimated_delivery_date onto the Order itself for customer visibility
            if new_assignment.estimated_delivery:
                order.estimated_delivery_date = new_assignment.estimated_delivery

            # Auto-advance order to PROCESSING if still in CONFIRMED
            if order.order_status == Order.OrderStatus.CONFIRMED:
                order.order_status = Order.OrderStatus.PROCESSING

            # Advance shipping status to in_transit so the Shipments & Logistics
            # page reflects the assignment immediately
            if order.shipping_status == Order.ShippingStatus.NOT_SHIPPED:
                order.shipping_status = Order.ShippingStatus.IN_TRANSIT

            order.save()

            # Create or update the Shipment record so it appears in the
            # Shipments & Logistics table with the agent's name as carrier
            shipment, _ = Shipment.objects.get_or_create(order=order)
            shipment.carrier = new_assignment.agent.name
            if new_assignment.delivery_notes:
                shipment.shipment_notes = new_assignment.delivery_notes
            if not shipment.shipped_at:
                shipment.shipped_at = timezone.now()
            shipment.save()
            messages.success(
                request,
                f"Order {order.formatted_id} assigned to {new_assignment.agent} "
                + (f"— ETA: {new_assignment.estimated_delivery}" if new_assignment.estimated_delivery else "")
            )
            return redirect('admin_dashboard:order_detail', order_id=order.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AssignAgentForm(instance=assignment)

    context = {
        'page_title': f'Assign Agent — Order {order.formatted_id}',
        'form': form,
        'order': order,
        'assignment': assignment,
    }
    return render(request, 'admin_dashboard/assign_agent_form.html', context)


@login_required
@user_passes_test(is_admin)
def technicians_overview(request):
    """List all verified technicians with their expertise and ratings."""
    from orders.models import Technician
    technicians = Technician.objects.all().order_by('-is_active', 'name')
    context = {
        'page_title': 'Field Technicians',
        'technicians': technicians,
        'total_techs': technicians.count(),
        'active_techs': technicians.filter(is_active=True).count(),
        'verified_techs': technicians.filter(is_verified=True).count(),
    }
    return render(request, 'admin_dashboard/technicians_overview.html', context)


@login_required
@user_passes_test(is_admin)
def technician_edit(request, tech_id=None):
    """Add or edit a verified technician profile."""
    from orders.models import Technician
    from .forms import TechnicianForm
    
    if tech_id:
        technician = get_object_or_404(Technician, id=tech_id)
        page_title = f'Edit Technician: {technician.name}'
    else:
        technician = None
        page_title = 'Add New Technician'

    if request.method == 'POST':
        form = TechnicianForm(request.POST, request.FILES, instance=technician)
        if form.is_valid():
            saved = form.save()
            messages.success(request, f"Profile for '{saved.name}' saved successfully.")
            return redirect('admin_dashboard:technicians_overview')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TechnicianForm(instance=technician)

    context = {
        'page_title': page_title,
        'form': form,
        'technician': technician,
    }
    return render(request, 'admin_dashboard/technician_form.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def technician_delete(request, tech_id):
    """Delete a technician profile."""
    from orders.models import Technician
    technician = get_object_or_404(Technician, id=tech_id)
    name = technician.name
    technician.delete()
    messages.success(request, f'Technician "{name}" deleted successfully.')
    return redirect('admin_dashboard:technicians_overview')


@login_required
@user_passes_test(is_admin)
def trash_overview(request):
    categories = Category.all_objects.filter(is_deleted=True).order_by('-deleted_at')
    products = Product.all_objects.filter(is_deleted=True).select_related('category').order_by('-deleted_at')
    coupons = Coupon.all_objects.filter(is_deleted=True).order_by('-deleted_at')
    context = {'page_title': 'Trash / Recycle Bin', 'trashed_categories': categories, 'trashed_products': products, 'trashed_coupons': coupons}
    return render(request, 'admin_dashboard/trash_overview.html', context)


@login_required
@user_passes_test(is_admin)
def trash_action(request, model_type, item_id, action):
    model_map = {'category': Category, 'product': Product, 'coupon': Coupon}
    ModelClass = model_map.get(model_type)
    if not ModelClass:
        messages.error(request, 'Invalid item type.')
        return redirect('admin_dashboard:trash_overview')
    item = get_object_or_404(ModelClass.all_objects, id=item_id, is_deleted=True)
    if action == 'restore':
        item.restore()
        messages.success(request, f'{item.__class__.__name__} was successfully restored.')
    elif action == 'hard_delete':
        item.hard_delete()
        messages.success(request, f'{item.__class__.__name__} was permanently deleted.')
    return redirect('admin_dashboard:trash_overview')


@login_required
@user_passes_test(is_admin)
def installations_overview(request):
    """Overview of all installation bookings"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    from orders.models import InstallationBooking
    installations = InstallationBooking.objects.select_related('order').all().order_by('-preferred_date')

    if search_query:
        installations = installations.filter(
            Q(order__id__icontains=search_query) |
            Q(technician_name__icontains=search_query) |
            Q(order__full_name__icontains=search_query)
        )

    if status_filter:
        installations = installations.filter(status=status_filter)

    paginator = Paginator(installations, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'Installation Management',
        'installations': page_obj,
        'page_obj': page_obj,
        'status_choices': InstallationBooking.BookingStatus.choices,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'admin_dashboard/installations_overview.html', context)


@login_required
@user_passes_test(is_admin)
def return_requests_overview(request):
    """View to list and filter return requests"""
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    from orders.models import ReturnRequest
    returns = ReturnRequest.objects.select_related('order', 'user').prefetch_related('returned_items__order_item__product').order_by('-created_at')
    
    if status_filter:
        returns = returns.filter(status=status_filter)
        
    if search_query:
        returns = returns.filter(
            Q(order__id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
        
    paginator = Paginator(returns, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Return Requests',
        'returns': page_obj,
        'page_obj': page_obj,
        'status_choices': ReturnRequest.ReturnStatus.choices,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'admin_dashboard/return_requests_overview.html', context)


@login_required
@user_passes_test(is_admin)
def return_request_detail(request, pk):
    """View to manage a specific return request"""
    from orders.models import ReturnRequest, ReturnItem, Order
    return_req = get_object_or_404(ReturnRequest.objects.select_related('order', 'user').prefetch_related('returned_items__order_item__product', 'photos'), pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_comment = request.POST.get('admin_comment', '')
        
        return_req.admin_comment = admin_comment
        
        if action == 'approve':
            return_req.status = ReturnRequest.ReturnStatus.APPROVED
            messages.success(request, f"Return request #{return_req.id} approved.")
        elif action == 'reject':
            return_req.status = ReturnRequest.ReturnStatus.REJECTED
            messages.warning(request, f"Return request #{return_req.id} rejected.")
        elif action == 'picked_up':
            return_req.status = ReturnRequest.ReturnStatus.PICKED_UP
            messages.info(request, f"Return request #{return_req.id} marked as Picked Up.")
        elif action == 'complete':
            from django.db import transaction
            try:
                with transaction.atomic():
                    return_req.status = ReturnRequest.ReturnStatus.COMPLETED
                    # Update Order status
                    order = return_req.order
                    order.order_status = Order.OrderStatus.RETURNED
                    order.payment_status = Order.PaymentStatus.REFUNDED
                    order.save()
                    
                    # Update Payment model
                    latest_payment = order.payments.order_by('-created_at').first()
                    if latest_payment:
                        latest_payment.status = Order.PaymentStatus.REFUNDED
                        latest_payment.save()
                    
                    messages.success(request, f"Return request #{return_req.id} completed and refund processed.")
            except Exception as e:
                messages.error(request, f"Error completing return: {str(e)}")
        
        return_req.save()
        return redirect('admin_dashboard:return_request_detail', pk=return_req.id)
        
    context = {
        'page_title': f'Return Request: #{return_req.id}',
        'return_req': return_req,
        'status_choices': ReturnRequest.ReturnStatus.choices,
    }
    return render(request, 'admin_dashboard/return_request_detail.html', context)


# ─── Serviceable Areas ────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def serviceable_areas_overview(request):
    """List and search all serviceable pincodes."""
    search = request.GET.get('search', '').strip()
    qs = ServiceableArea.objects.all()
    if search:
        qs = qs.filter(pincode__icontains=search)

    paginator = Paginator(qs.order_by('pincode'), 30)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_title': 'Serviceable Areas',
        'areas': page_obj,
        'page_obj': page_obj,
        'search_query': search,
        'total_count': qs.count(),
        'delivery_count': qs.filter(delivery_available=True).count(),
        'installation_count': qs.filter(installation_available=True).count(),
    }
    return render(request, 'admin_dashboard/serviceable_areas.html', context)


@login_required
@user_passes_test(is_admin)
def serviceable_area_edit(request, area_id=None):
    """Add or edit a serviceable pincode."""
    if area_id:
        area = get_object_or_404(ServiceableArea, id=area_id)
        page_title = f'Edit Area: {area.pincode}'
    else:
        area = None
        page_title = 'Add Serviceable Area'

    if request.method == 'POST':
        form = ServiceableAreaForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            messages.success(request, f"Pincode {'updated' if area else 'added'} successfully.")
            return redirect('admin_dashboard:serviceable_areas')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ServiceableAreaForm(instance=area)

    context = {
        'page_title': page_title,
        'form': form,
        'area': area,
    }
    return render(request, 'admin_dashboard/serviceable_area_form.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def serviceable_area_delete(request, area_id):
    """Delete a serviceable area entry."""
    area = get_object_or_404(ServiceableArea, id=area_id)
    area.delete()
    messages.success(request, f'Pincode {area.pincode} removed.')
    return redirect('admin_dashboard:serviceable_areas')


# ─── FAQs ─────────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def faqs_overview(request):
    """List all FAQ entries grouped by category."""
    from support.models import FAQ, FAQCategory
    search = request.GET.get('search', '').strip()
    qs = FAQ.objects.select_related('category').all()
    if search:
        qs = qs.filter(question__icontains=search)

    paginator = Paginator(qs.order_by('category__order', 'order'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    faq_categories = FAQCategory.objects.all()

    context = {
        'page_title': 'FAQ Management',
        'faqs': page_obj,
        'page_obj': page_obj,
        'faq_categories': faq_categories,
        'search_query': search,
        'total_count': FAQ.objects.count(),
        'active_count': FAQ.objects.filter(is_active=True).count(),
    }
    return render(request, 'admin_dashboard/faqs_overview.html', context)


@login_required
@user_passes_test(is_admin)
def faq_edit(request, faq_id=None):
    """Add or edit a single FAQ entry."""
    from support.models import FAQ
    if faq_id:
        faq = get_object_or_404(FAQ, id=faq_id)
        page_title = 'Edit FAQ'
    else:
        faq = None
        page_title = 'Add FAQ'

    if request.method == 'POST':
        form = FAQForm(request.POST, instance=faq)
        if form.is_valid():
            form.save()
            messages.success(request, f"FAQ {'updated' if faq else 'created'} successfully.")
            return redirect('admin_dashboard:faqs_overview')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FAQForm(instance=faq)

    context = {
        'page_title': page_title,
        'form': form,
        'faq': faq,
    }
    return render(request, 'admin_dashboard/faq_form.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def faq_delete(request, faq_id):
    """Delete a FAQ entry."""
    from support.models import FAQ
    faq = get_object_or_404(FAQ, id=faq_id)
    faq.delete()
    messages.success(request, 'FAQ deleted successfully.')
    return redirect('admin_dashboard:faqs_overview')


@login_required
@user_passes_test(is_admin)
def faq_categories_overview(request):
    """List all FAQ categories."""
    from support.models import FAQCategory
    categories = FAQCategory.objects.annotate(faq_count=Count('faqs')).order_by('order', 'name')
    context = {
        'page_title': 'FAQ Categories',
        'categories': categories,
    }
    return render(request, 'admin_dashboard/faq_categories.html', context)


@login_required
@user_passes_test(is_admin)
def faq_category_edit(request, cat_id=None):
    """Add or edit an FAQ category."""
    from support.models import FAQCategory
    if cat_id:
        category = get_object_or_404(FAQCategory, id=cat_id)
        page_title = f'Edit Category: {category.name}'
    else:
        category = None
        page_title = 'Add FAQ Category'

    if request.method == 'POST':
        form = FAQCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f"Category {'updated' if category else 'created'} successfully.")
            return redirect('admin_dashboard:faq_categories')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FAQCategoryForm(instance=category)

    context = {
        'page_title': page_title,
        'form': form,
        'category': category,
    }
    return render(request, 'admin_dashboard/faq_category_form.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def faq_category_delete(request, cat_id):
    """Delete an FAQ category (and cascade-deletes its FAQs)."""
    from support.models import FAQCategory
    category = get_object_or_404(FAQCategory, id=cat_id)
    name = category.name
    category.delete()
    messages.warning(request, f'Category "{name}" and all its FAQs were deleted.')
    return redirect('admin_dashboard:faq_categories')


# ── INVOICES ──────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def invoices_overview(request):
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    qs = Invoice.objects.select_related('order', 'user').order_by('-created_at')
    if search:
        qs = qs.filter(
            Q(invoice_number__icontains=search) |
            Q(order__full_name__icontains=search) |
            Q(user__email__icontains=search)
        )
    if status_filter:
        qs = qs.filter(payment_status=status_filter)
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'page_title': 'Invoices',
        'invoices': page_obj,
        'page_obj': page_obj,
        'search_query': search,
        'status_filter': status_filter,
        'total_count': Invoice.objects.count(),
        'paid_count': Invoice.objects.filter(payment_status='Paid').count(),
        'pending_count': Invoice.objects.filter(payment_status='Pending').count(),
    }
    return render(request, 'admin_dashboard/invoices_overview.html', context)


@login_required
@user_passes_test(is_admin)
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(
        Invoice.objects.select_related('order', 'user').prefetch_related('order__items__product'),
        id=invoice_id
    )
    context = {
        'page_title': f'Invoice {invoice.invoice_number}',
        'invoice': invoice,
    }
    return render(request, 'admin_dashboard/invoice_detail.html', context)


# ── INSTALLATION PHOTOS ───────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def installation_photos_overview(request):
    search = request.GET.get('search', '').strip()
    label_filter = request.GET.get('label', '')
    qs = InstallationPhoto.objects.select_related(
        'booking', 'booking__order'
    ).order_by('-uploaded_at')
    if search:
        qs = qs.filter(
            Q(booking__order__full_name__icontains=search) |
            Q(booking__order__id__icontains=search) |
            Q(booking__technician_name__icontains=search)
        )
    if label_filter:
        qs = qs.filter(label=label_filter)
    paginator = Paginator(qs, 24)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'page_title': 'Installation Photos',
        'photos': page_obj,
        'page_obj': page_obj,
        'search_query': search,
        'label_filter': label_filter,
        'total_count': InstallationPhoto.objects.count(),
        'photo_labels': InstallationPhoto.PhotoLabel.choices,
    }
    return render(request, 'admin_dashboard/installation_photos.html', context)


@login_required
@user_passes_test(is_admin)
def installation_photos_booking(request, booking_id):
    booking = get_object_or_404(
        InstallationBooking.objects.select_related('order').prefetch_related('photos'),
        id=booking_id
    )
    context = {
        'page_title': f'Photos – Order #{booking.order_id}',
        'booking': booking,
        'photos': booking.photos.all(),
    }
    return render(request, 'admin_dashboard/installation_photos_booking.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def installation_photo_delete(request, photo_id):
    photo = get_object_or_404(InstallationPhoto, id=photo_id)
    booking_id = photo.booking_id
    photo.image.delete(save=False)
    photo.delete()
    messages.success(request, 'Photo deleted.')
    return redirect('admin_dashboard:installation_photos_booking', booking_id=booking_id)


# ── CUSTOMER PROFILES ─────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def profiles_overview(request):
    search = request.GET.get('search', '').strip()
    qs = Profile.objects.select_related('user').order_by('-updated_at')
    if search:
        qs = qs.filter(
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(phone_number__icontains=search)
        )
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'page_title': 'Customer Profiles',
        'profiles': page_obj,
        'page_obj': page_obj,
        'search_query': search,
        'total_count': Profile.objects.count(),
        'verified_count': Profile.objects.filter(email_verified=True).count(),
    }
    return render(request, 'admin_dashboard/profiles_overview.html', context)


@login_required
@user_passes_test(is_admin)
def profile_detail(request, profile_id):
    profile = get_object_or_404(Profile.objects.select_related('user'), id=profile_id)
    addresses = Address.objects.filter(user=profile.user)
    recent_orders = Order.objects.filter(user=profile.user).order_by('-created_at')[:5]
    context = {
        'page_title': f'Profile – {profile.user.username}',
        'profile': profile,
        'addresses': addresses,
        'recent_orders': recent_orders,
    }
    return render(request, 'admin_dashboard/profile_detail.html', context)


# ── CUSTOMER ADDRESSES ────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def addresses_overview(request):
    search = request.GET.get('search', '').strip()
    qs = Address.objects.select_related('user').order_by('-created_at')
    if search:
        qs = qs.filter(
            Q(full_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(city__icontains=search) |
            Q(pincode__icontains=search)
        )
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'page_title': 'Customer Addresses',
        'addresses': page_obj,
        'page_obj': page_obj,
        'search_query': search,
        'total_count': Address.objects.count(),
        'default_count': Address.objects.filter(is_default=True).count(),
    }
    return render(request, 'admin_dashboard/addresses_overview.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def address_delete(request, address_id):
    addr = get_object_or_404(Address, id=address_id)
    addr.delete()
    messages.warning(request, 'Address deleted.')
    return redirect('admin_dashboard:addresses_overview')


# ── NOTIFICATIONS ─────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def notifications_overview(request):
    search = request.GET.get('search', '').strip()
    type_filter = request.GET.get('type', '')
    qs = Notification.objects.select_related('user').order_by('-created_at')
    if search:
        qs = qs.filter(
            Q(title__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__username__icontains=search)
        )
    if type_filter:
        qs = qs.filter(notification_type=type_filter)
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    users_list = User.objects.filter(is_active=True).order_by('username')
    context = {
        'page_title': 'Notifications',
        'notifications': page_obj,
        'page_obj': page_obj,
        'search_query': search,
        'type_filter': type_filter,
        'total_count': Notification.objects.count(),
        'unread_count': Notification.objects.filter(is_read=False).count(),
        'notif_types': Notification.NotificationType.choices,
        'users_list': users_list,
    }
    return render(request, 'admin_dashboard/notifications_overview.html', context)


@login_required
@user_passes_test(is_admin)
def notification_send(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        notif_type = request.POST.get('notification_type', Notification.NotificationType.ALERT)
        link = request.POST.get('link', '').strip()
        target = request.POST.get('target', 'single')

        if not title or not message:
            messages.error(request, 'Title and message are required.')
            return redirect('admin_dashboard:notifications_overview')

        if target == 'all':
            for u in User.objects.filter(is_active=True):
                Notification.send(u, title, message, notif_type, link)
            messages.success(request, f'Notification sent to all {User.objects.filter(is_active=True).count()} users.')
        else:
            user = get_object_or_404(User, id=user_id)
            Notification.send(user, title, message, notif_type, link)
            messages.success(request, f'Notification sent to {user.username}.')
    return redirect('admin_dashboard:notifications_overview')


@login_required
@user_passes_test(is_admin)
@require_POST
def notification_delete(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id)
    notif.delete()
    messages.warning(request, 'Notification deleted.')
    return redirect('admin_dashboard:notifications_overview')


# ── REVIEW MEDIA ──────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def review_media_overview(request):
    search = request.GET.get('search', '').strip()
    type_filter = request.GET.get('type', '')
    qs = ReviewMedia.objects.select_related('review', 'review__product', 'review__user').order_by('-created_at')
    if search:
        qs = qs.filter(
            Q(review__product__name__icontains=search) |
            Q(review__user__username__icontains=search)
        )
    if type_filter == 'video':
        qs = qs.filter(is_video=True)
    elif type_filter == 'photo':
        qs = qs.filter(is_video=False)
    paginator = Paginator(qs, 24)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'page_title': 'Review Media',
        'media_items': page_obj,
        'page_obj': page_obj,
        'search_query': search,
        'type_filter': type_filter,
        'total_count': ReviewMedia.objects.count(),
        'video_count': ReviewMedia.objects.filter(is_video=True).count(),
        'photo_count': ReviewMedia.objects.filter(is_video=False).count(),
    }
    return render(request, 'admin_dashboard/review_media.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def review_media_delete(request, media_id):
    media = get_object_or_404(ReviewMedia, id=media_id)
    media.file.delete(save=False)
    media.delete()
    messages.warning(request, 'Media file deleted.')
    return redirect('admin_dashboard:review_media')

@login_required
@user_passes_test(is_admin)
def user_edit(request, user_id=None):
    from django.contrib.auth import get_user_model
    from .forms import UserForm

    User = get_user_model()
    
    if user_id:
        user = get_object_or_404(User, id=user_id)
        page_title = f"Edit User: {user.username}"
    else:
        user = None
        page_title = "Add New User"

    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            msg = "User updated successfully." if user_id else "User created successfully."
            messages.success(request, msg)
            return redirect('admin_dashboard:users_overview')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserForm(instance=user)

    context = {
        'form': form,
        'page_title': page_title,
    }
    return render(request, 'admin_dashboard/user_form.html', context)
