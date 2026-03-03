from django.urls import path
from . import views

urlpatterns = [
     path('', views.product_list, name='product_list'),
     path('category/<slug:category_slug>/', views.product_list, name='products_by_category'),
     path('product/<slug:slug>/', views.product_detail, name='product_detail'),
     path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
     path('cart/', views.cart_view, name='cart'),
     path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
     path('update-cart/<int:product_id>/<str:action>/', views.update_cart, name='update_cart'),
     path('checkout/', views.checkout, name='checkout'),
     path('order-success/', views.order_success, name='order_success'),
]