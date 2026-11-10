"""
URL configuration for admin_dashboard app
"""

from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('orders/', views.orders_overview, name='orders_overview'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/delete/<int:order_id>/', views.order_delete, name='order_delete'),
    path('installations/', views.installations_overview, name='installations_overview'),
    path('products/', views.products_overview, name='products_overview'),
    path('products/add/', views.product_edit, name='product_add'),
    path('products/edit/<int:product_id>/', views.product_edit, name='product_edit'),
    path('products/delete/<int:product_id>/', views.product_delete, name='product_delete'),
    path('ajax/get-spec-form/', views.get_spec_form, name='get_spec_form'),
    path('users/', views.users_overview, name='users_overview'),
    path('users/add/', views.user_edit, name='user_add'),
    path('users/edit/<int:user_id>/', views.user_edit, name='user_edit'),
    path('users/delete/<int:user_id>/', views.user_delete, name='user_delete'),
    path('analytics/', views.analytics, name='analytics'),
    
    # Store Management
    path('coupons/', views.coupons_overview, name='coupons_overview'),
    path('coupons/add/', views.coupon_edit, name='coupon_add'),
    path('coupons/edit/<int:coupon_id>/', views.coupon_edit, name='coupon_edit'),
    path('coupons/delete/<int:coupon_id>/', views.coupon_delete, name='coupon_delete'),
    
    path('categories/', views.categories_overview, name='categories_overview'),
    path('categories/add/', views.category_edit, name='category_add'),
    path('categories/edit/<int:category_id>/', views.category_edit, name='category_edit'),
    path('categories/delete/<int:category_id>/', views.category_delete, name='category_delete'),
    
    path('payments/', views.payments_overview, name='payments_overview'),
    path('shipments/', views.shipments_overview, name='shipments_overview'),
    
    # Reviews Management
    path('reviews/', views.reviews_overview, name='reviews_overview'),
    path('reviews/delete/<int:review_id>/', views.review_delete, name='review_delete'),
    path('reviews/toggle-status/<int:review_id>/', views.review_toggle_status, name='review_toggle_status'),

    # Returns Management
    path('returns/', views.return_requests_overview, name='return_requests_overview'),
    path('returns/<int:pk>/', views.return_request_detail, name='return_request_detail'),

    # Delivery Management
    path('delivery/', views.delivery_board, name='delivery_board'),
    path('delivery/agents/', views.delivery_agents_overview, name='delivery_agents'),
    path('delivery/agents/add/', views.delivery_agent_edit, name='delivery_agent_add'),
    path('delivery/agents/edit/<int:agent_id>/', views.delivery_agent_edit, name='delivery_agent_edit'),
    path('delivery/agents/delete/<int:agent_id>/', views.delivery_agent_delete, name='delivery_agent_delete'),
    # Technician Management
    path('technicians/', views.technicians_overview, name='technicians_overview'),
    path('technicians/add/', views.technician_edit, name='technician_add'),
    path('technicians/edit/<int:tech_id>/', views.technician_edit, name='technician_edit'),
    path('technicians/delete/<int:tech_id>/', views.technician_delete, name='technician_delete'),

    # Trash / Recycle Bin
    path('trash/', views.trash_overview, name='trash_overview'),
    path('trash/action/<str:model_type>/<int:item_id>/<str:action>/', views.trash_action, name='trash_action'),

    # Serviceable Areas (Pincode Coverage)
    path('serviceable-areas/', views.serviceable_areas_overview, name='serviceable_areas'),
    path('serviceable-areas/add/', views.serviceable_area_edit, name='serviceable_area_add'),
    path('serviceable-areas/edit/<int:area_id>/', views.serviceable_area_edit, name='serviceable_area_edit'),
    path('serviceable-areas/delete/<int:area_id>/', views.serviceable_area_delete, name='serviceable_area_delete'),

    # FAQ Management
    path('leads/', views.quote_requests_overview, name='quote_requests'),
    path('service-requests/', views.tickets_overview, name='tickets_overview'),
    path('service-requests/<int:ticket_id>/', views.ticket_manage, name='ticket_manage'),
    path('projects/', views.projects_overview, name='projects_overview'),
    path('projects/add/', views.project_edit, name='project_add'),
    path('projects/edit/<int:project_id>/', views.project_edit, name='project_edit'),
    path('projects/delete/<int:project_id>/', views.project_delete, name='project_delete'),
    path('projects/toggle/<int:project_id>/', views.project_toggle_publish, name='project_toggle_publish'),
    path('leads/<int:lead_id>/update/', views.quote_request_update, name='quote_request_update'),
    path('faqs/', views.faqs_overview, name='faqs_overview'),
    path('faqs/add/', views.faq_edit, name='faq_add'),
    path('faqs/edit/<int:faq_id>/', views.faq_edit, name='faq_edit'),
    path('faqs/delete/<int:faq_id>/', views.faq_delete, name='faq_delete'),
    path('faqs/categories/', views.faq_categories_overview, name='faq_categories'),
    path('faqs/categories/add/', views.faq_category_edit, name='faq_category_add'),
    path('faqs/categories/edit/<int:cat_id>/', views.faq_category_edit, name='faq_category_edit'),
    path('faqs/categories/delete/<int:cat_id>/', views.faq_category_delete, name='faq_category_delete'),

    # Invoices
    path('invoices/', views.invoices_overview, name='invoices_overview'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),

    # Installation Photos
    path('installation-photos/', views.installation_photos_overview, name='installation_photos'),
    path('installation-photos/<int:booking_id>/', views.installation_photos_booking, name='installation_photos_booking'),
    path('installation-photos/delete/<int:photo_id>/', views.installation_photo_delete, name='installation_photo_delete'),

    # Customer Profiles
    path('profiles/', views.profiles_overview, name='profiles_overview'),
    path('profiles/<int:profile_id>/', views.profile_detail, name='profile_detail'),

    # Customer Addresses
    path('addresses/', views.addresses_overview, name='addresses_overview'),
    path('addresses/delete/<int:address_id>/', views.address_delete, name='address_delete'),

    # Notifications
    path('notifications/', views.notifications_overview, name='notifications_overview'),
    path('notifications/send/', views.notification_send, name='notification_send'),
    path('notifications/delete/<int:notif_id>/', views.notification_delete, name='notification_delete'),

    # Review Media
    path('review-media/', views.review_media_overview, name='review_media'),
    path('review-media/delete/<int:media_id>/', views.review_media_delete, name='review_media_delete'),
]
