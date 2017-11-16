# coding: utf-8
import collections
import typing
from math import sqrt

import numpy

from synergine2_xyz.xyz import DIRECTION_MODIFIERS


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


def get_min_and_max(positions) -> (int, int, int, int, int):
    max_x_position = max(positions, key=lambda p: p[0])
    min_x_position = min(positions, key=lambda p: p[0])
    max_y_position = max(positions, key=lambda p: p[1])
    min_y_position = min(positions, key=lambda p: p[1])
    max_z_position = max(positions, key=lambda p: p[2])
    min_z_position = min(positions, key=lambda p: p[2])

    max_x = max_x_position[0]
    min_x = min_x_position[0]
    max_y = max_y_position[1]
    min_y = min_y_position[1]
    max_z = max_z_position[2]
    min_z = min_z_position[2]

    return min_x, max_x, min_y, max_y, min_z, max_z


def get_str_representation_from_positions(
    items_positions: dict,
    separator='',
    tabulation='',
    start_with='',
    end_with='',
    force_items_as=None,
    force_positions_as=None,
    complete_lines_with=' ',
) -> str:
    positions = []
    for item_positions in items_positions.values():
        positions.extend(item_positions)
    positions = sorted(positions, key=lambda p: (p[2], p[1], p[0]))

    if complete_lines_with is not None:
        min_x, max_x, min_y, max_y, min_z, max_z = get_min_and_max(positions)

        all_ = []

        for x in range(min_x, max_x+1):
            for y in range(min_y, max_y+1):
                for z in range(min_z, max_z+1):
                    all_.append((x, y, z))

        pass

        for one_of_all in all_:
            if one_of_all not in positions:
                if complete_lines_with not in items_positions:
                    items_positions[complete_lines_with] = []
                items_positions[complete_lines_with].append(one_of_all)

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


def get_around_positions_of(
        position,
        distance=1,
        exclude_start_point=True,
) -> list:
    """
    Return positions around a point.
    :param position: (x, y, z) tuple
    :param distance: Distance to compute
    :return: list of (x, y, z) positions
    """
    start_x = position[0] - distance
    start_y = position[1] - distance
    # start_z = position[0] - distance
    positions = []
    range_distance = (distance * 2) + 1
    for dx in range(range_distance):
        for dy in range(range_distance):
            # for dz in range(range_distance):
            # points.append((start_z+dz, start_x+dx, start_y+dy))
            positions.append((start_x + dx, start_y + dy, position[2]))
    if exclude_start_point:
        positions.remove(position)

    return positions


def get_distance_between_points(a: tuple, b: tuple) -> float:
    return abs(sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2))


def get_position_for_direction(from_position: tuple, direction: int) -> tuple:
    modifier = DIRECTION_MODIFIERS[direction]
    return (
        from_position[0] + modifier[0],
        from_position[1] + modifier[1],
        from_position[2] + modifier[2],
    )


def get_angle(a: typing.Tuple[int, int], b: typing.Tuple[int, int]) -> int:
    b = (b[0] - a[0], b[1] - a[1])
    a = 0, 1

    ang1 = numpy.arctan2(*a[::-1])
    ang2 = numpy.arctan2(*b[::-1])

    return numpy.rad2deg((ang1 - ang2) % (2 * numpy.pi))


def get_line_xy_path(start, end):
    """
    TODO: copied from http://www.roguebasin.com/index.php?title=Bresenham%27s_Line_Algorithm#Python
    What is the licence ?
    Bresenham's Line Algorithm
    Produces a list of tuples from start and end

    >>> points1 = get_line((0, 0), (3, 4))
    >>> points2 = get_line((3, 4), (0, 0))
    >>> assert(set(points1) == set(points2))
    >>> print points1
    [(0, 0), (1, 1), (1, 2), (2, 3), (3, 4)]
    >>> print points2
    [(3, 4), (2, 3), (1, 2), (1, 1), (0, 0)]
    """
    # Setup initial conditions
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1

    # Determine how steep the line is
    is_steep = abs(dy) > abs(dx)

    # Rotate line
    if is_steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2

    # Swap start and end points if necessary and store swap state
    swapped = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        swapped = True

    # Recalculate differentials
    dx = x2 - x1
    dy = y2 - y1

    # Calculate error
    error = int(dx / 2.0)
    ystep = 1 if y1 < y2 else -1

    # Iterate over bounding box generating points between start and end
    y = y1
    points = []
    for x in range(x1, x2 + 1):
        coord = (y, x) if is_steep else (x, y)
        points.append(coord)
        error -= abs(dy)
        if error < 0:
            y += ystep
            error += dx

    # Reverse the list if the coordinates were swapped
    if swapped:
        points.reverse()
    return points
