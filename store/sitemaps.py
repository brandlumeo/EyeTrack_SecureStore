from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Category, Product


class StaticViewSitemap(Sitemap):
    priority = 0.7
    changefreq = "weekly"

    def items(self):
        return [
            "product_list",
            "about_page",
            "solutions_page",
            "home_security",
            "services_page",
            "quote_request",
            "support_page",
            "faq_page",
            "privacy_policy_page",
            "terms_page",
            "refund_policy_page",
            "shipping_policy_page",
        ]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_available=True).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse("product_detail", kwargs={"slug": obj.slug})


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.75

    def items(self):
        return Category.objects.order_by("name")

    def location(self, obj):
        return reverse("products_by_category", kwargs={"category_slug": obj.slug})
