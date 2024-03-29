import copy
import re

from django.db.models import Case, QuerySet, TextChoices, When
from django.conf import settings

from chart_types.models import ChartType
from filter_groups.models import FilterGroup
from ladders.models import Ladder
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
        self.items = []

        self.spec_str = spec_str
        if spec_str == '':
            # No items.
            return

        filter_spec_item_strs = spec_str.split('-')

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

    @classmethod
    def from_query_params(cls, query_params):
        # Both the `ladder_id` and `filters` parameters describe how to
        # filter the records.

        ladder_id = query_params.get('ladder_id')
        if ladder_id is None:
            ladder_filter_spec = FilterSpec('')
        else:
            ladder = Ladder.objects.get(id=ladder_id)
            ladder_filter_spec = FilterSpec(ladder.filter_spec)

        param_filter_spec_str = query_params.get('filters', '')
        param_filter_spec = FilterSpec(param_filter_spec_str)

        return FilterSpec.merge_two_instances(
            ladder_filter_spec, param_filter_spec)

    @classmethod
    def merge_two_instances(cls, spec1, spec2):
        if spec1.spec_str == '':
            return spec2
        if spec2.spec_str == '':
            return spec1
        spec_str = f"{spec1.spec_str}-{spec2.spec_str}"
        return FilterSpec(spec_str)

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

    def is_empty(self):
        return len(self.items) == 0

    def __str__(self):
        return self.spec_str


def apply_filter_spec(
        records: QuerySet, filter_spec_in: FilterSpec,
        chart_type: ChartType = None) -> QuerySet:
    """
    Filter `records` based on `filter_spec_in`. If `chart_type` is passed,
    any filter spec parts that don't apply to the chart type are excluded.
    """
    filter_spec = filter_spec_in
    if chart_type:
        non_applicable_fgs = \
            set(filter_spec_in.filter_groups) \
            - set(chart_type.filter_groups.all())
        if non_applicable_fgs:
            filter_spec = copy.copy(filter_spec_in)
            for fg in non_applicable_fgs:
                filter_spec.remove_filter_group(fg)

    for item in filter_spec.items:
        filter_id = item['filter_id']
        f = Filter.objects.get(id=filter_id)
        modifier = item['modifier']

        if modifier == FilterSpec.Modifiers.IS:
            # Basic filter matching.
            if f.usage_type == Filter.UsageTypes.CHOOSABLE.value:
                # The record uses this filter.
                records = records.filter(filters=filter_id)
            elif f.usage_type == Filter.UsageTypes.IMPLIED.value:
                # The record has a filter that implies this filter.
                records = records.filter(
                    filters__in=f.incoming_filter_implications.all())
        elif modifier == FilterSpec.Modifiers.IS_NOT:
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
        elif modifier == FilterSpec.Modifiers.LESS_OR_EQUAL:
            # Less than or equal to, for numeric filters.
            records = records.filter(
                filters__filter_group=f.filter_group,
                filters__numeric_value__lte=f.numeric_value)
        elif modifier == FilterSpec.Modifiers.GREATER_OR_EQUAL:
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
