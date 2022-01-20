# TODO: Make this a management command instead of a standalone script.

# Script to generate a CSV (spreadsheet) of GX machine filters, including both
# filter names and implication links.
#
# See filter_import.py for the CSV format spec.
#
# Requires Python 3.7+ and PyYAML (pip install PyYAML).

import csv
import yaml


if __name__ == '__main__':

    with open('gx_machine_filter_info.yaml', 'r') as yamlfile:
        filter_info = yaml.full_load(yamlfile)

    parts_to_special_name_lookup = dict()
    for machine in filter_info['special_name_custom_machines']:
        # lookup key example: Dread Hammer,Combat Cannon,Titan -G4
        lookup_key = \
            f"{machine['body']},{machine['cockpit']},{machine['booster']}"
        parts_to_special_name_lookup[lookup_key] = machine['name']

    with open('gx_machine_filters.csv', 'w', newline='', encoding='utf-8') \
            as csvfile:

        writer = csv.writer(csvfile)

        # First row should contain: game name, name of a chart type that uses
        # this filter group, filter group name.
        writer.writerow(["F-Zero GX", "Course Time", "Machine"])

        # Write the filters in order, such that every filter is written after
        # all the filters it implies are written.

        writer.writerow(["Custom"])
        writer.writerow(["Non-Custom"])

        for part_type in ['body', 'cockpit', 'booster']:
            for rating in ['E', 'D', 'C', 'B', 'A']:
                filter_name = f"{rating} custom {part_type}"
                implication = "Custom"
                writer.writerow([filter_name, implication])

        body_parts = filter_info['body_parts']
        for part_info in body_parts:
            name = f"{part_info['name']} body"
            implication = f"{part_info['rating']} custom body"
            writer.writerow([name, implication])

        cockpit_parts = filter_info['cockpit_parts']
        for part_info in cockpit_parts:
            name = f"{part_info['name']} cockpit"
            implication = f"{part_info['rating']} custom cockpit"
            writer.writerow([name, implication])

        booster_parts = filter_info['booster_parts']
        for part_info in booster_parts:
            name = f"{part_info['name']} booster"
            implication = f"{part_info['rating']} custom booster"
            writer.writerow([name, implication])

        non_custom_name_set = set()
        for machine_info in filter_info['non_custom_machines']:
            implication = "Non-Custom"
            writer.writerow([machine_info['name'], implication])
            non_custom_name_set.add(machine_info['name'])

        for body in body_parts:
            for cockpit in cockpit_parts:
                for booster in booster_parts:
                    lookup_key = \
                        f"{body['name']},{cockpit['name']},{booster['name']}"

                    if lookup_key in parts_to_special_name_lookup:

                        name = parts_to_special_name_lookup[lookup_key]

                    else:

                        name_format = booster['machine_name_format']
                        first_word_spec = ' '.join(name_format.split()[:2])
                        second_word_spec = ' '.join(name_format.split()[2:4])
                        has_suffix = name_format.endswith('suffix')

                        name = ""

                        if first_word_spec == 'body a':
                            name += body['first_word_a']
                        elif first_word_spec == 'body b':
                            name += body['first_word_b']
                        elif first_word_spec == 'cockpit a':
                            name += cockpit['first_word_a']
                        elif first_word_spec == 'cockpit b':
                            name += cockpit['first_word_b']
                        else:
                            raise ValueError(
                                f"Invalid name format: {name_format}")

                        name += " "

                        if second_word_spec == 'body a':
                            name += body['second_word_a']
                        elif second_word_spec == 'body b':
                            name += body['second_word_b']
                        elif second_word_spec == 'cockpit a':
                            name += cockpit['second_word_a']
                        elif second_word_spec == 'cockpit b':
                            name += cockpit['second_word_b']
                        else:
                            raise ValueError(
                                f"Invalid name format: {name_format}")

                        if has_suffix:
                            # Example suffix: '-G4'
                            b_name = booster['name']
                            suffix = b_name[b_name.find('-'):]
                            name += suffix

                    # Check if the custom machine has the same name as a
                    # non-custom, and add the name suffix " (Custom)" in that
                    # case.
                    if name in non_custom_name_set:
                        name += " (Custom)"

                    writer.writerow([
                        name,
                        # Each custom machine implies its 3 parts
                        f"{body['name']} body",
                        f"{cockpit['name']} cockpit",
                        f"{booster['name']} booster",
                    ])
