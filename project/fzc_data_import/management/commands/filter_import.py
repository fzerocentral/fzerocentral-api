import csv

from django.core.management.base import BaseCommand
from django.db.models import Count
from tqdm import tqdm

from filters.models import Filter
from games.models import Game
from chart_types.models import ChartType


class Command(BaseCommand):
    help = """
    Import filters and implications from a CSV file into the database.
    The CSV is assumed to define all filters and DIRECT implications of a
    particular filter group (which is assumed to already exist).
    WARNING: The filter group's existing implications will be deleted
    before the import starts. (However, existing filters will not be deleted.)
    
    CSV format:
    First row:
    - Game name
    - Name of a chart type that uses the filter group of interest.
      This is used to disambiguate between filter groups of the same name in the
      same game; for example, vehicle choices may be different between different
      game modes, thus necessitating a different 'Vehicle' filter group for each
      mode.
    - Filter group name
    Subsequent rows:
    - Filter name goes in the first column
    - The second, third, etc. columns have names of filters DIRECTLY implied by
      the filter in question. One implied filter name per column. These rows 
      must be in reverse topographical order: start with the filters that don't
      imply anything, then list the filters that directly imply those, and so
      on, finishing with the filters that aren't implied by anything.
    
    For example:
    F-Zero GX, Course Time, Machine
    Non-Custom
    Custom
    Blue Falcon, Non-Custom
    Dread Hammer body, Custom
    Maximum Star cockpit, Custom
    Titan-G4 booster, Custom
    Gallant Star-G4, Dread Hammer body, Maximum Star cockpit, Titan-G4 booster
    
    It's not necessary to specify "Gallant Star-G4, Custom" because that's an
    INDIRECT implication. This command will figure out indirect
    implications from the CSV's direct implications, and both types of
    implications will be added to the database.
    
    Example usage:
    python manage.py filter_import fzc_data_import/data/gx_machine_filters.csv
    """

    def add_arguments(self, parser):
        parser.add_argument(
            'csvfile',
            type=str,
            help="Filepath of the CSV file containing the filters")

    def handle(self, *args, **options):

        # Get filter group details, and establish which filters are implied
        # rather than choosable.
        all_implied_names = set()
        with open(options['csvfile'], 'r') as csvfile:
            reader = csv.reader(csvfile)

            # First row
            game_name, name_of_ct_with_fg, filter_group_name = next(reader)

            # Second row onward
            for row in reader:
                direct_outgoing_names = row[1:]
                all_implied_names.update(direct_outgoing_names)

        game = Game.objects.get(name=game_name)
        ct_with_fg = ChartType.objects.get(game=game, name=name_of_ct_with_fg)
        filter_group = ct_with_fg.filter_groups.get(name=filter_group_name)

        existing_filters = filter_group.filter_set.all()
        self.stdout.write(f"Existing filters: {existing_filters.count()}")

        # It's just easier to delete all existing implications, and then
        # subsequently add them all from scratch.
        for filter in existing_filters:
            filter.outgoing_filter_implications.clear()

        all_outgoing = dict()

        # Create filters that don't exist in the DB yet, and add implications.
        with open(options['csvfile'], 'r') as csvfile:
            reader = csv.reader(csvfile)

            # Discard the first row, we don't need it now.
            next(reader)

            # Iterate over filters.
            for row in tqdm(reader):
                filter_name = row[0]
                direct_outgoing_names = row[1:]

                try:
                    filter = filter_group.filter_set.get(name=filter_name)
                except Filter.DoesNotExist:
                    # Create filter
                    if filter_name in all_implied_names:
                        usage_type = Filter.UsageTypes.IMPLIED.value
                    else:
                        usage_type = Filter.UsageTypes.CHOOSABLE.value
                    filter = Filter(
                        name=filter_name, filter_group=filter_group,
                        usage_type=usage_type)
                    filter.save()

                # Determine effective implications based on the direct
                # implications.
                all_outgoing_names = set()
                for direct_outgoing_name in direct_outgoing_names:
                    # Direct
                    all_outgoing_names.add(
                        direct_outgoing_name)
                    # Indirect
                    all_outgoing_names.update(
                        all_outgoing[direct_outgoing_name])

                # If this filter is implied by other filters, save those
                # implications for lookup later.
                if filter_name in all_implied_names:
                    all_outgoing[filter_name] = all_outgoing_names

                # Insert effective implications.
                for outgoing_name in all_outgoing_names:
                    implied_filter = Filter.objects.get(
                        filter_group=filter_group, name=outgoing_name)
                    filter.outgoing_filter_implications.add(implied_filter)

        # Print counts as sanity checks

        filters = filter_group.filter_set.all()
        implication_count = filters.aggregate(
            Count('outgoing_filter_implications')).get(
                'outgoing_filter_implications__count')
        self.stdout.write(f"""
            Total filters after insertions: {filters.count()}
            Total filter implications after insertions: {implication_count}
            """)
