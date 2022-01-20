import re

from django.db.models import QuerySet

from .models import Filter


def apply_filter_spec(records: QuerySet, filter_spec_str: str):
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
        filter = Filter.objects.get(id=filter_id)

        match type_suffix:
            case '':
                # No suffix; basic filter matching.
                if filter.usage_type == Filter.UsageTypes.CHOOSABLE.value:
                    # The record uses this filter.
                    records = records.filter(filters=filter_id)
                elif filter.usage_type == Filter.UsageTypes.IMPLIED.value:
                    # The record has a filter that implies this filter.
                    records = records.filter(
                        filters__in=filter.incoming_filter_implications.all())
            case 'n':
                # Negation.
                if filter.usage_type == Filter.UsageTypes.CHOOSABLE.value:
                    # The record has a filter in this group that doesn't
                    # match the specified filter.
                    records = records \
                        .filter(filters__filter_group=filter.filter_group) \
                        .exclude(filters=filter_id)
                elif filter.usage_type == Filter.UsageTypes.IMPLIED.value:
                    # The record has a filter in this group that doesn't
                    # imply the specified filter.
                    records = records \
                        .filter(filters__filter_group=filter.filter_group) \
                        .exclude(filters__in=filter.incoming_filter_implications.all())
            case 'le':
                # Less than or equal to, for numeric filters.
                records = records.filter(
                    filters__filter_group=filter.filter_group,
                    filters__numeric_value__lte=filter.numeric_value)
            case 'ge':
                # Greater than or equal to, for numeric filters.
                records = records.filter(
                    filters__filter_group=filter.filter_group,
                    filters__numeric_value__gte=filter.numeric_value)
            case _:
                raise ValueError(
                    f"Unknown filter type suffix: {type_suffix}")

    return records
