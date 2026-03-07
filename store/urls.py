from django.urls import path
from . import views

urlpatterns = [
     path('', views.product_list, name='product_list'),
     path('about/', views.about_page, name='about_page'),
     path('services/', views.services_page, name='services_page'),
     path('support/', views.support_page, name='support_page'),
     path('faq/', views.faq_page, name='faq_page'),
     path('wishlist/', views.wishlist_page, name='wishlist_page'),
     path('compare/', views.compare_page, name='compare_page'),
     path('privacy-policy/', views.privacy_policy_page, name='privacy_policy_page'),
     path('terms/', views.terms_page, name='terms_page'),
     path('refund-policy/', views.refund_policy_page, name='refund_policy_page'),
     path('shipping-policy/', views.shipping_policy_page, name='shipping_policy_page'),
     path('category/<slug:category_slug>/', views.product_list, name='products_by_category'),
     path('product/<slug:slug>/', views.product_detail, name='product_detail'),
     path('api/product/<int:product_id>/quick-view/', views.quick_view_product, name='quick_view_product'),
     path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
     path('cart/', views.cart_view, name='cart'),
     path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
     path('update-cart/<int:product_id>/<str:action>/', views.update_cart, name='update_cart'),
     path('checkout/', views.checkout, name='checkout'),
     path('payment/<int:order_id>/', views.simulated_payment, name='simulated_payment'),
     path('order-success/', views.order_success, name='order_success'),
]
