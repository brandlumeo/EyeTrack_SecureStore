from django.urls import path
from . import views

urlpatterns = [
    path('', views.faq_view, name='faq'),
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
]
