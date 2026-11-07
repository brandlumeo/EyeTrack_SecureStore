"""Import the four like-new laptops supplied in the November 2026 product list."""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from store.models import Category, Product


LAPTOPS = (
    {
        "sku": "LAT-5420-I5",
        "name": "Dell Latitude 5420 – Core i5 11th Gen",
        "brand": "Dell",
        "processor": "Core i5 11th Gen",
        "screen": '14"',
        "graphics": "Integrated",
        "extra": None,
        "price": "33600.00",
    },
    {
        "sku": "LAT-5420-I7",
        "name": "Dell Latitude 5420 – Core i7 11th Gen",
        "brand": "Dell",
        "processor": "Core i7 11th Gen",
        "screen": '14"',
        "graphics": "Integrated",
        "extra": None,
        "price": "39900.00",
    },
    {
        "sku": "LAT-3400-I5",
        "name": "Dell Latitude 3400 – Core i5 8th Gen",
        "brand": "Dell",
        "processor": "Core i5 8th Gen",
        "screen": '14"',
        "graphics": "Integrated",
        "extra": None,
        "price": "23800.00",
    },
    {
        "sku": "TP-P51-I7",
        "name": "Lenovo ThinkPad P51 – Core i7 7th Gen",
        "brand": "Lenovo",
        "processor": "Core i7 7th Gen",
        "screen": '15.6"',
        "graphics": "4GB Dedicated",
        "extra": "Numeric keypad",
        "price": "41300.00",
    },
)


class Command(BaseCommand):
    help = "Add/update the four supplied laptop listings; new listings have zero stock."

    @transaction.atomic
    def handle(self, *args, **options):
        category, _ = Category.all_objects.get_or_create(
            slug="laptops", defaults={"name": "Laptops", "icon": "bi-laptop"}
        )
        if category.is_deleted:
            category.restore()
        for laptop in LAPTOPS:
            highlights = [
                f"SKU: {laptop['sku']}",
                f"Brand: {laptop['brand']}",
                f"Processor: {laptop['processor']}",
                "RAM: 8GB",
                "Storage: 256GB SSD",
                f"Screen: {laptop['screen']}",
                f"Graphics: {laptop['graphics']}",
                "Condition: Like New",
            ]
            if laptop["extra"]:
                highlights.append(f"Extra features: {laptop['extra']}")
            description = (
                f"Like-new {laptop['name'].split(' – ')[0]} laptop with an Intel "
                f"{laptop['processor']} processor, 8GB RAM, 256GB SSD, "
                f"a {laptop['screen']} screen, and {laptop['graphics'].lower()} graphics."
            )
            if laptop["extra"]:
                description += f" Includes a {laptop['extra'].lower()}."
            description += f" Condition: Like New. SKU: {laptop['sku']}."
            product, created = Product.all_objects.update_or_create(
                slug=laptop["sku"].lower(),
                defaults={
                    "category": category,
                    "name": laptop["name"],
                    "description": description,
                    "highlights": "\n".join(highlights),
                    "price": Decimal(laptop["price"]),
                    "is_available": True,
                    "is_deleted": False,
                    "deleted_at": None,
                },
                create_defaults={
                    "category": category,
                    "name": laptop["name"],
                    "description": description,
                    "highlights": "\n".join(highlights),
                    "price": Decimal(laptop["price"]),
                    "is_available": True,
                    "stock": 0,
                    "installation_available": False,
                },
            )
            action = "Added" if created else "Updated"
            self.stdout.write(f"{action}: {laptop['sku']} | INR {product.price} | stock {product.stock}")
        self.stdout.write(self.style.SUCCESS("Four laptop listings imported. Existing stock and images are preserved on repeat imports."))
