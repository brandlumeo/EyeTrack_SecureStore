"""
Migration: Add DeliveryAgent, DeliveryAssignment models and
           estimated_delivery_date field on Order.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0012_order_coupon_order_discount_amount"),
    ]

    operations = [
        # 1. Add estimated_delivery_date to Order (nullable — safe, no default needed)
        migrations.AddField(
            model_name="order",
            name="estimated_delivery_date",
            field=models.DateField(blank=True, null=True),
        ),

        # 2. Create DeliveryAgent
        migrations.CreateModel(
            name="DeliveryAgent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("phone", models.CharField(max_length=20)),
                (
                    "vehicle_type",
                    models.CharField(
                        choices=[
                            ("bike", "Bike"),
                            ("car", "Car"),
                            ("van", "Van"),
                            ("walk", "Walking / On Foot"),
                            ("other", "Other"),
                        ],
                        default="bike",
                        max_length=20,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),

        # 3. Create DeliveryAssignment
        migrations.CreateModel(
            name="DeliveryAssignment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "order",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="delivery_assignment",
                        to="orders.order",
                    ),
                ),
                (
                    "agent",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assignments",
                        to="orders.deliveryagent",
                    ),
                ),
                ("estimated_delivery", models.DateField(blank=True, null=True)),
                ("delivery_notes", models.TextField(blank=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-assigned_at"],
            },
        ),
    ]
