import re

from django.db.models import Case, QuerySet, TextChoices, When
from django.conf import settings

from filter_groups.models import FilterGroup
from .models import Filter


class FilterSpec:

    spec_item_regex = re.compile(r'(\d+)([a-z]*)')

    class Modifiers(TextChoices):
        IS = '', ""
        IS_NOT = 'n', "NOT"
        # These two are for numeric filters only.
        GREATER_OR_EQUAL = 'ge', ">="
        LESS_OR_EQUAL = 'le', "<="

    def __init__(self, spec_str: str):
        """
        :param spec_str: Looks something like '1-4n-9ge-11-24le'.
            Dash-separated tokens, with each token having a filter ID number
            and possibly a modifier suffix indicating how to apply the filter.
        """
        self.spec_str = spec_str
        filter_spec_item_strs = spec_str.split('-')
        self.items = []

        for item_index, item_str in enumerate(filter_spec_item_strs):
            regex_match = self.spec_item_regex.fullmatch(item_str)
            if not regex_match:
                raise ValueError(
                    f"Could not parse filter spec: {spec_str}")
            filter_id, modifier_code = regex_match.groups()
            self.items.append(dict(
                filter_id=filter_id,
                modifier=self.Modifiers(modifier_code),
            ))

    @property
    def filter_groups(self) -> list[FilterGroup]:
        return [
            Filter.objects.get(id=item['filter_id']).filter_group
            for item in self.items
        ]

    def remove_filter_group(self, filter_group: FilterGroup):
        """
        Remove the item of the given filter group, if such an item exists.
        """
        filter_groups = self.filter_groups
        if filter_group in filter_groups:
            index = filter_groups.index(filter_group)
            self.items.pop(index)

    def __str__(self):
        return self.spec_str


def apply_filter_spec(records: QuerySet, filter_spec: FilterSpec) -> QuerySet:
    """
    Filter `records` based on `filter_spec_str`.
    """
    for item in filter_spec.items:
        filter_id = item['filter_id']
        f = Filter.objects.get(id=filter_id)

        match item['modifier']:
            case FilterSpec.Modifiers.IS:
                # Basic filter matching.
                if f.usage_type == Filter.UsageTypes.CHOOSABLE.value:
                    # The record uses this filter.
                    records = records.filter(filters=filter_id)
                elif f.usage_type == Filter.UsageTypes.IMPLIED.value:
                    # The record has a filter that implies this filter.
                    records = records.filter(
                        filters__in=f.incoming_filter_implications.all())
            case FilterSpec.Modifiers.IS_NOT:
                # Negation.
                if f.usage_type == Filter.UsageTypes.CHOOSABLE.value:
                    # The record has a filter in this group that doesn't
                    # match the specified filter.
                    records = records \
                        .filter(filters__filter_group=f.filter_group) \
                        .exclude(filters=filter_id)
                elif f.usage_type == Filter.UsageTypes.IMPLIED.value:
                    # The record has a filter in this group that doesn't
                    # imply the specified filter.
                    records = records \
                        .filter(filters__filter_group=f.filter_group) \
                        .exclude(filters__in=f.incoming_filter_implications.all())
            case FilterSpec.Modifiers.LESS_OR_EQUAL:
                # Less than or equal to, for numeric filters.
                records = records.filter(
                    filters__filter_group=f.filter_group,
                    filters__numeric_value__lte=f.numeric_value)
            case FilterSpec.Modifiers.GREATER_OR_EQUAL:
                # Greater than or equal to, for numeric filters.
                records = records.filter(
                    filters__filter_group=f.filter_group,
                    filters__numeric_value__gte=f.numeric_value)

    return records


def apply_name_search(
        queryset: QuerySet, search_arg: str, limit: int = None) -> QuerySet:

    if limit is None:
        limit = settings.REST_FRAMEWORK['PAGE_SIZE']

    # Remove all chars besides letters, numbers, and spaces. Replace such
    # chars with spaces.
    cleaned_search_arg = re.sub(r'[^\w\s]', ' ', search_arg)
    # Parse space-separated search terms.
    search_terms = cleaned_search_arg.split(' ')
    # Case-insensitive 'contains this search term' test on the filter name.
    # Up to 5 terms (to prevent malicious use).
    for search_term in search_terms[:5]:
        queryset = queryset.filter(name__icontains=search_term)

    # Take care of ordering. Exact match always comes first.
    # Then alphabetical order by name.
    # https://stackoverflow.com/questions/52047107/order-a-django-queryset-with-specific-objects-first
    queryset = queryset.order_by(
        Case(When(name__iexact=search_arg, then=0), default=1),
        'name',
    )
    return queryset
