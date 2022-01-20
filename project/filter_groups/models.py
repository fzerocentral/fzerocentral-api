from django.db import models


class FilterGroup(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=2000)

    class Kinds(models.TextChoices):
        SELECT = 'select', "Select"
        NUMERIC = 'numeric', "Numeric"
    kind = models.CharField(
        max_length=10, choices=Kinds.choices, default=Kinds.SELECT)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
