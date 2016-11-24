import collections


def get_positions_from_str_representation(str_representation):
    # TODO: Manage z axis (like ------------ as separator)
    lines = str_representation.split("\n")  # One item per lines
    lines = map(lambda l: l.strip().replace(' ', ''), lines)  # Remove spaces
    lines = filter(lambda l: bool(l), lines)  # Only line with content
    lines = list(lines)

    width = len(lines[0])
    height = len(lines)

    if not width % 2 or not height % 2:
        raise Exception(
            'Width and height of your representation must be odd. '
            'Actually it\'s {0}x{1}'.format(
                width,
                height,
            ))

    items_positions = collections.defaultdict(list)

    start_x = - int(width / 2 - 0.5)
    start_y = - int(height / 2 - 0.5)
    start_z = 0

    current_y = start_y
    current_z = start_z

    for line in lines:
        current_x = start_x
        for char in line:
            items_positions[char].append((
                current_x,
                current_y,
                current_z,
            ))
            current_x += 1
        current_y += 1

    return items_positions


def get_str_representation_from_positions(
    items_positions: dict,
    separator='',
    tabulation='',
    start_with='',
    end_with='',
    force_items_as=None,
    force_positions_as=None,
) -> str:
    positions = []
    for item_positions in items_positions.values():
        positions.extend(item_positions)
    positions = sorted(positions, key=lambda p: (p[2], p[1], p[0]))

    str_representation = start_with + tabulation

    start_x = positions[0][0]
    start_y = positions[0][1]
    start_z = positions[0][2]

    current_y = start_y
    current_z = start_z

    for position in positions:
        item = None
        for parsed_item in items_positions:
            if position in items_positions[parsed_item]:
                item = parsed_item
                break

        if position[1] != current_y:
            str_representation += "\n" + tabulation

        if position[2] != current_z:
            str_representation += '----' + "\n" + tabulation

        str_item = item
        if force_items_as:
            for force_item_as in force_items_as:
                if force_item_as[0] == item:
                    str_item = force_item_as[1]
                    break

        if force_positions_as:
            for force_position_as in force_positions_as:
                if position == force_position_as[0]:
                    str_item = force_position_as[1]
                    break

        added_value = str_item
        if position[0] != start_x:
            added_value = separator + added_value

        str_representation += added_value
        current_y = position[1]
        current_z = position[2]

    return str_representation + end_with


def get_around_positions_of_positions(position, exclude_start_position=True) -> list:
    """
    TODO: compute with z (allow or disable with parameter)
    Return positions around a point with distance of 1.

    :param position: (x, y, z) tuple
    :param exclude_start_position: if True, given position will not be
    added to result list
    :return: list of (x, y, z) positions
    :rtype: list
    """
    pz = position[2]
    px = position[0]
    py = position[1]
    points = [
        (px-1, py-1, pz),
        (px,   py-1, pz),
        (px+1, py+1, pz),
        (px-1, py  , pz),
        (px+1, py  , pz),
        (px-1, py+1, pz),
        (px,   py+1, pz),
        (px+1, py-1, pz)
    ]
    if not exclude_start_position:
        points.append(position)
    return points
