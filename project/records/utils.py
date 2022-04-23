from django.db.models import QuerySet

from chart_types.utils import apply_format_spec
from charts.models import Chart
from core.utils import add_ranks


def add_record_displays(records: list[dict], format_spec: list[dict]):
    """
    Add value_display attribute to each record in `records`.
    This attribute is the human-readable string of the record value,
    such as 1'23"456 instead of 123456.
    """
    for record in records:
        record['value_display'] = apply_format_spec(
            format_spec, record['value'])


def make_record_ranking(records: list[dict]) -> list[dict]:
    """
    Include only the first record for each player (given that they've
    already been sorted best-first), and add rank numbers, accounting
    for tied values.
    """
    seen_players = set()
    record_ranking = []

    for record in records:
        # Get only the first record for each player.
        # We iterate manually through the records to do this. distinct()
        # doesn't seem to get the job done, since "the fields in order_by()
        # must start with the fields in distinct(), in the same order."
        # https://docs.djangoproject.com/en/dev/ref/models/querysets/#distinct
        # TODO: Re-evaluate this. Not the end of the world if we have to sort
        #  players manually.
        if record['player_id'] in seen_players:
            # Not the first record from this player. Ignore.
            continue

        record_ranking.append(record)
        seen_players.add(record['player_id'])

    add_ranks(record_ranking, 'value')

    return record_ranking


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
