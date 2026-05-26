from django.db import models

class FAQCategory(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default="bi-question-circle", help_text="Bootstrap icon class")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "FAQ Categories"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

class FAQ(models.Model):
    category = models.ForeignKey(FAQCategory, on_delete=models.CASCADE, related_name="faqs")
    question = models.CharField(max_length=255)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.question
