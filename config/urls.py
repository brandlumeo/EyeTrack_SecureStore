"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from store.sitemaps import CategorySitemap, ProductSitemap, ProjectSitemap, StaticViewSitemap, ViewingGuideSitemap
from support import views as support_views


sitemaps = {
    "static": StaticViewSitemap,
    "categories": CategorySitemap,
    "products": ProductSitemap,
    "projects": ProjectSitemap,
    "guides": ViewingGuideSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-dashboard/', include('admin_dashboard.urls')),
    path('support/', include('support.urls')),
    path('faq/', support_views.faq_view, name='faq'),
    path('get-quote/', support_views.quote_request, name='quote_request'),
    path('', include('store.urls')),
    path('accounts/', include('accounts.urls')),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain"), name="robots_txt"),
    path("firebase-messaging-sw.js", TemplateView.as_view(template_name="firebase-messaging-sw.js", content_type="application/javascript"), name="firebase_sw"),
]

from django.urls import re_path
from django.views.static import serve

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
