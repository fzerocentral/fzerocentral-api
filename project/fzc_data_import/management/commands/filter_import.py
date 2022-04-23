import csv

from django.core.management.base import BaseCommand
from django.db.models import Count

from filters.models import Filter
from games.models import Game


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
        filter_names = []
        implication_names_by_filter = dict()
        all_implied_names = set()
        with open(options['csvfile'], 'r') as csvfile:
            reader = csv.reader(csvfile)

            # First row
            game_name, filter_group_name = next(reader)

            # Second row onward
            for row in reader:
                filter_name = row[0]
                filter_names.append(filter_name)
                directly_implied_names = row[1:]

                # Direct implications
                implication_names = set(directly_implied_names)
                # Indirect implications
                for directly_implied_name in directly_implied_names:
                    # Add indirects out of this particular direct implication
                    implication_names |= implication_names_by_filter[
                        directly_implied_name]

                implication_names_by_filter[filter_name] = implication_names

                all_implied_names.update(directly_implied_names)

        game = Game.objects.get(name=game_name)
        filter_group = game.filtergroup_set.get(name=filter_group_name)

        existing_filter_names = set(
            filter_group.filter_set.values_list('name', flat=True))
        self.stdout.write(f"Existing filters: {len(existing_filter_names)}")

        # It's just easier to delete all existing implications, and then
        # subsequently add them all from scratch. Here we delete them.
        ThroughModel = Filter.outgoing_filter_implications.through
        ThroughModel.objects.filter(
            from_filter__filter_group=filter_group).delete()

        # Set up filters to create if they don't exist in the DB yet.
        filters = []
        for filter_name in filter_names:

            if filter_name in existing_filter_names:
                continue

            if filter_name in all_implied_names:
                usage_type = Filter.UsageTypes.IMPLIED.value
            else:
                usage_type = Filter.UsageTypes.CHOOSABLE.value
            filters.append(Filter(
                name=filter_name,
                filter_group=filter_group,
                usage_type=usage_type,
            ))
        # Bulk-create filters.
        created_filters = Filter.objects.bulk_create(filters)

        created_filters_by_name = {f.name: f for f in created_filters}

        # Set up implications to create.
        implications = []
        for filter_name in filter_names:
            f = created_filters_by_name[filter_name]
            for implication_name in implication_names_by_filter[filter_name]:
                f2 = created_filters_by_name[implication_name]
                implications.append(ThroughModel(
                    from_filter=f,
                    to_filter=f2,
                ))
        # Bulk-create implications.
        ThroughModel.objects.bulk_create(implications)

        # Print counts as sanity checks.

        filters = filter_group.filter_set.all()
        implication_count = filters.aggregate(
            Count('outgoing_filter_implications')).get(
                'outgoing_filter_implications__count')
        self.stdout.write(f"""
            Total filters after insertions: {filters.count()}
            Total filter implications after insertions: {implication_count}
            """)
