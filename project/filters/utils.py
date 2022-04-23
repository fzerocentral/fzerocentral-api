import re

from django.db.models import Case, QuerySet, When
from django.conf import settings

from .models import Filter


def apply_filter_spec(records: QuerySet, filter_spec_str: str) -> QuerySet:
    """
    Filter `records` based on `filter_spec_str`.

    filter_spec_str looks something like '1-4n-9ge-11-24le'.
    Dash-separated tokens, with each token having a filter ID number and
    possibly a suffix indicating how to apply the filter.
    """
    filter_spec_item_strs = filter_spec_str.split('-')
    filter_spec_item_regex = re.compile(r'(\d+)([a-z]*)')

    for item_index, item_str in enumerate(filter_spec_item_strs):
        regex_match = filter_spec_item_regex.fullmatch(item_str)
        if not regex_match:
            raise ValueError(
                f"Could not parse filter spec: {filter_spec_str}")
        filter_id, type_suffix = regex_match.groups()
        f = Filter.objects.get(id=filter_id)

        match type_suffix:
            case '':
                # No suffix; basic filter matching.
                if f.usage_type == Filter.UsageTypes.CHOOSABLE.value:
                    # The record uses this filter.
                    records = records.filter(filters=filter_id)
                elif f.usage_type == Filter.UsageTypes.IMPLIED.value:
                    # The record has a filter that implies this filter.
                    records = records.filter(
                        filters__in=f.incoming_filter_implications.all())
            case 'n':
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
            case 'le':
                # Less than or equal to, for numeric filters.
                records = records.filter(
                    filters__filter_group=f.filter_group,
                    filters__numeric_value__lte=f.numeric_value)
            case 'ge':
                # Greater than or equal to, for numeric filters.
                records = records.filter(
                    filters__filter_group=f.filter_group,
                    filters__numeric_value__gte=f.numeric_value)
            case _:
                raise ValueError(
                    f"Unknown filter type suffix: {type_suffix}")

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
