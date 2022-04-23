from django.db import models

from filter_groups.models import FilterGroup


class Filter(models.Model):
    name = models.CharField(max_length=200)
    numeric_value = models.IntegerField(null=True)

    class UsageTypes(models.TextChoices):
        CHOOSABLE = 'choosable', "Choosable"
        IMPLIED = 'implied', "Implied"
    usage_type = models.CharField(
        max_length=10, choices=UsageTypes.choices, default=UsageTypes.CHOOSABLE)

    filter_group = models.ForeignKey(FilterGroup, on_delete=models.CASCADE)

    class SpecModifiers(models.TextChoices):
        NOT = 'n', "NOT"
        GREATER_OR_EQUAL = 'ge', ">="
        LESS_OR_EQUAL = 'le', "<="

    outgoing_filter_implications = models.ManyToManyField(
        'self', symmetrical=False,
        related_name='incoming_filter_implications')

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
