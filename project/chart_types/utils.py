
def apply_format_spec(format_spec: list[dict], value: int) -> str:

    # Order of the hashes determines both rank (importance of this
    # number relative to the others) AND position-order in the string.
    # Can't think of any examples where those would need to be different.
    total_multiplier = 1
    for spec_item in reversed(format_spec):
        total_multiplier = total_multiplier * spec_item.get(
            'multiplier', 1)
        spec_item['total_multiplier'] = total_multiplier

    remaining_value = value
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

    return value_display
