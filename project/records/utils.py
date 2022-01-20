from typing import Dict, List

from django.db.models import QuerySet

from charts.models import Chart


def add_record_displays(records: List[Dict], format_spec: List[Dict]):
    """
    Add value_display attribute to each record in `records`.
    This attribute is the human-readable string of the record value,
    such as 1'23"456 instead of 123456.
    """
    for record in records:
        # Order of the hashes determines both rank (importance of this
        # number relative to the others) AND position-order in the string.
        # Can't think of any examples where those would need to be different.
        #
        # Since format_spec is loaded from JSON, the hash keys are strings like
        # 'multiplier', not colon identifiers like :multiplier.
        total_multiplier = 1
        for spec_item in reversed(format_spec):
            total_multiplier = total_multiplier * spec_item.get(
                'multiplier', 1)
            spec_item['total_multiplier'] = total_multiplier

        remaining_value = record['value']
        value_display = ""

        for spec_item in format_spec:
            item_value = remaining_value / spec_item['total_multiplier']
            remaining_value = remaining_value % spec_item['total_multiplier']

            number_format = '%'
            if 'digits' in spec_item:
                number_format += '0' + str(spec_item['digits'])
            number_format += 'd'

            value_display += \
                (number_format % item_value) + spec_item.get('suffix', '')

        record['value_display'] = value_display


def make_record_ranking(records: List[Dict]) -> List[Dict]:
    """
    Include only the first record for each player (given that they've
    already been sorted best-first), and add rank numbers, accounting
    for tied values.
    """
    seen_players = set()
    current_rank = 0
    previous_record_count = 0
    previous_value = None
    ranked_records = []

    for record in records:
        # Get only the first record for each player.
        # We iterate manually through the records to do this. distinct()
        # doesn't seem to get the job done, since "the fields in order_by()
        # must start with the fields in distinct(), in the same order."
        # https://docs.djangoproject.com/en/dev/ref/models/querysets/#distinct
        if record['player_username'] in seen_players:
            # Not the first record from this player. Ignore.
            continue

        if record['value'] != previous_value:
            # Not a tie with the previous record.
            current_rank = previous_record_count + 1
        record['rank'] = current_rank

        ranked_records.append(record)

        previous_record_count += 1
        previous_value = record['value']
        seen_players.add(record['player_username'])

    return ranked_records


def sort_records_by_value(records: QuerySet, chart_id: int) -> QuerySet:
    """
    Best value first - lowest if ascending sort, highest if descending.
    """
    # Determine the ordering direction.
    if chart_id is not None:
        chart = Chart.objects.get(id=chart_id)
        value_ascending = chart.chart_type.order_ascending
    elif records.exists():
        # There's at least one record.
        # Ordering by value across charts assumes all of these charts
        # use the same order. So we'll just take the order of any
        # record's chart.
        a_record = records.first()
        value_ascending = a_record.chart.chart_type.order_ascending
    else:
        # There are no records. The order doesn't matter anyway,
        # so we arbitrarily pick ascending.
        value_ascending = True
    value_order_str = 'value' if value_ascending else '-value'

    # Tiebreak by earliest achieved, followed by earliest submitted.
    return records.order_by(value_order_str, 'date_achieved', 'id')
