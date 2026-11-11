from django.urls import path
from . import download_views, guide_views, ticket_views, views

urlpatterns = [
    path('', views.faq_view, name='faq'),
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
    path('guides/', guide_views.guide_list, name='guide_list'),
    path('guides/<slug:slug>/', guide_views.guide_detail, name='guide_detail'),
    path('downloads/', download_views.download_list, name='download_list'),
    path('downloads/<int:pk>/', download_views.download_file, name='download_file'),
    path('requests/', ticket_views.ticket_list, name='ticket_list'),
    path('requests/new/', ticket_views.ticket_create, name='ticket_create'),
    path('requests/<int:pk>/', ticket_views.ticket_detail, name='ticket_detail'),
    path('requests/<int:pk>/close/', ticket_views.ticket_close, name='ticket_close'),
    path('requests/photo/<int:pk>/', ticket_views.ticket_photo, name='ticket_photo'),
]
