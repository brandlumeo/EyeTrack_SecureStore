from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.account_dashboard, name="account_dashboard"),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('firebase-login/', views.firebase_login, name='firebase_login'),
    path('google-gsi-login/', views.google_gsi_login, name='google_gsi_login'),
    path("verify-email/sent/", views.verify_email_sent, name="verify_email_sent"),
    path("verify-email/resend/", views.resend_verification_email_view, name="resend_verification_email"),
    path("verify-email/<uidb64>/<token>/", views.verify_email, name="verify_email"),
    path("profile/", views.profile_view, name="profile"),
    path("save-fcm-token/", views.save_fcm_token, name="save_fcm_token"),
    
    # Notifications
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/clear/', views.clear_notifications, name='clear_notifications'),
    path("addresses/", views.address_list_view, name="address_list"),
    path("addresses/add/", views.address_create_view, name="address_add"),
    path("addresses/<int:pk>/edit/", views.address_update_view, name="address_edit"),
    path("addresses/<int:pk>/delete/", views.address_delete_view, name="address_delete"),
    path("addresses/<int:pk>/default/", views.address_set_default_view, name="address_set_default"),
    path('orders/', views.order_history, name='order_history'),
    path("orders/<int:pk>/track/", views.order_tracking, name="order_tracking"),
    path("orders/<int:pk>/invoice/", views.order_invoice, name="order_invoice"),
    path("orders/<int:pk>/invoice/download/", views.order_invoice_download, name="order_invoice_download"),
    path("orders/<int:pk>/cancel/", views.cancel_order, name="cancel_order"),
    path("orders/<int:pk>/return/", views.order_return, name="order_return"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.txt",
            subject_template_name="accounts/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(template_name="accounts/password_reset_confirm.html"),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete",
    ),
]
