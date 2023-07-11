from dataclasses import dataclass
import itertools
import numpy as np
import random
import types
import typing

# Directions
_LEFT = 0
_RIGHT = 1
_UP = 2
_DOWN = 3

# Not virtual cell types (these are actually presented on cells layout)
# Virtual cell types are: _HEAD, _VACANCY
_EMPTY = 0
_SPAWNER = 1
_BODY = 2


_point = tuple[int, int]
_ndint = np.ndarray[int]
_ndbool = np.ndarray[bool]
_pfilter = typing.Callable[[_point], bool]


class _PointChecker:
    """Checks if the point lays in bounds."""

    def __init__(self, w: int, h: int):
        self.__w = w
        self.__h = h

    def __call__(self, point: _point) -> bool:
        """Checks if the point lays in bounds."""
        x, y = point

        return (0 <= x < self.__w) and (0 <= y < self.__h)


@dataclass
class _Arrays:
    """
    Used to store and share some data about level structure between functions.

    Includes:
        cells: _ndint
        hor_doors: _ndbool
        ver_doors: _ndbool
    """

    cells: _ndint
    hor_doors: _ndbool
    ver_doors: _ndbool


def _get_nbr_points(
    point: _point,
    filter_: _pfilter,
) -> list[_point]:
    """
    Returns all valid neighbor points.

    point
        point to get neighbor points for.
    filter_
        function defining which point is valid.
    """
    x, y = point

    return [
        item
        for item in (
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1),
        )
        if filter_(item)
    ]


def _get_nbr_dirs(point: _point, filter_: _pfilter) -> list[int]:
    """
    Returns all directions pointing to the valid neighbor points.

    point
        point to get directions for.
    filter_
        function defining which point is valid.
    """
    x, y = point

    return [
        pair[1]
        for pair in (
            ((x - 1, y), _LEFT),
            ((x + 1, y), _RIGHT),
            ((x, y - 1), _UP),
            ((x, y + 1), _DOWN),
        )
        if filter_(pair[0])
    ]


def _get_nbr_points_n_dirs(
    point: _point, filter_: _pfilter
) -> list[tuple[_point, int]]:
    """
    Returns list of tuples of all valid neighbor points with directions pointing at them.

    point
        point to get data for.
    filter_
        function defining which point is valid.
    """
    x, y = point

    return [
        pair
        for pair in (
            ((x - 1, y), _LEFT),
            ((x + 1, y), _RIGHT),
            ((x, y - 1), _UP),
            ((x, y + 1), _DOWN),
        )
        if filter_(pair[0])
    ]


def _get_door(point: _point, dir: int, data: _Arrays) -> bool:
    """
    Returns the door state.

    The door is specified using the direction from the adjacent cell point.

    point
        adjacent cell point from which the direction is indicated.
    dir
        direction code.
    data
        level structure data including the doors data.
    """
    x, y = point

    if dir == _LEFT:
        return data.hor_doors[x - 1, y]
    if dir == _RIGHT:
        return data.hor_doors[x, y]
    if dir == _UP:
        return data.ver_doors[x, y - 1]
    if dir == _DOWN:
        return data.ver_doors[x, y]


def _set_door(point: _point, dir: int, value: bool, data: _Arrays):
    """
    Sets the door state.

    The door is specified using the direction from the adjacent cell point.

    point
        adjacent cell point from which the direction is indicated.
    dir
        direction code.
    data
        level structure data including the doors data.
    """
    x, y = point

    if dir == _LEFT:
        data.hor_doors[x - 1, y] = value
    if dir == _RIGHT:
        data.hor_doors[x, y] = value
    if dir == _UP:
        data.ver_doors[x, y - 1] = value
    if dir == _DOWN:
        data.ver_doors[x, y] = value


def _wire(point: _point, data: _Arrays, filter_: _pfilter):
    """
    Wires the virtual _HEAD cell with not virtual _SPAWNER cells nearby.

    _HEAD cell position is specified using point argument.
    _SPAWNER cells are listed in data.

    point
        position of the virtual _HEAD cell to wire.
    data
        level structure data including the not virtual cells data.
    filter_
        function defining which point is valid.
    """
    dirs = [
        pair[1]
        for pair in _get_nbr_points_n_dirs(point, filter_)
        if data.cells[*pair[0]] == _SPAWNER
    ]

    for dir in dirs:
        _set_door(point, dir, True, data)


def _process_as_if_dead_end(
    point: _point, data: _Arrays, filter_: _pfilter, chance: float = 0.35
) -> bool:
    """
    Processes the cell as a dead end if it is.

    point
        point to check and process if it is a dead end.
    data
        level structure data.
    filter_
        function defining which point is valid.
    chance
        parameter that determines the probability of continuing additional wirings after the first one.
    """
    x, y = point

    # If the cell is not empty
    if data.cells[x, y] == _BODY:
        # Get the neighbors directions
        dirs = [
            pair[1]
            for pair in _get_nbr_points_n_dirs(point, filter_)
            if data.cells[*pair[0]] == _BODY
        ]

        # One neighbor is always connected and boring < NOTE 1
        if len(dirs) == 1:
            # But it means it is a dead end forever
            return True

        # Find the first door and hope it is the last
        first = None
        for dir in dirs:
            if _get_door(point, dir, data):
                if first != None:
                    # The door wasn't last
                    return
                else:
                    first = dir

        # Remove the connected neighbor
        dirs.remove(first)
        del first

        # Keep in mind we have atleast 1 extra neighbor, check the NOTE 1
        choice = random.choice(dirs)
        _set_door(point, choice, True, data)
        dirs.remove(choice)

        while (len(dirs) > 0) and (random.random() <= chance):
            choice = random.choice(dirs)
            _set_door(point, choice, True, data)
            dirs.remove(choice)

        return False


def _big_cell_filter(point: _point, data: _Arrays) -> bool:
    """
    Defines if big cell can be placed at this point.

    When evaluating, the upper left corner of the big cell is positioned above the point.
    """
    x, y = point

    return (
        data.hor_doors[x, y]
        and data.ver_doors[x, y]
        and data.hor_doors[x, y + 1]
        and data.ver_doors[x + 1, y]
    )


def _place_big_cell(point: _point, data: _Arrays):
    """Displaces the structures of common cells and doors with a big cell"""
    x, y = point

    cells = data.cells

    cells[x, y] = _EMPTY
    cells[x + 1, y] = _EMPTY
    cells[x, y + 1] = _EMPTY
    cells[x + 1, y + 1] = _EMPTY

    data.hor_doors[x, y] = False
    data.hor_doors[x, y + 1] = False
    data.ver_doors[x, y] = False
    data.ver_doors[x + 1, y] = False


def _difference(x: int, y: int) -> int:
    """Equal to abs(x-y)"""
    if x < y:
        return y - x

    return x - y


def _max_point_difference(a: _point, b: _point) -> int:
    """Returns the maximum between x's differences and y's differences."""
    return max(
        _difference(a[0], b[0]),
        _difference(a[1], b[1]),
    )


def _finish(
    w: int, h: int, data: _Arrays, filter_: _pfilter, chance: float
) -> types.GenericAlias(tuple, (_ndbool,) * 4 + (list[_point],)):
    """
    Finishes the generation.

    1. Processes the dead ends.
    2. Lists the chests
    3. Places the big rooms.
    4. Changes the common cells structure to the final bool 2-dimensional array.
    5. Returns the result.
    """
    chests = []

    for cell in itertools.product(range(w), range(h)):
        if _process_as_if_dead_end(cell, data, filter_, chance):
            chests.append(cell)

    big_cells = np.full((w - 1, h - 1), False, bool)

    # Potential big cells. We create it using filter only once!
    # We will manage this list taking intersecting vacancies out
    p_big_cells = [
        cell
        for cell in itertools.product(range(w - 1), range(h - 1))
        if _big_cell_filter(cell, data)
    ]

    while len(p_big_cells) > 0:
        choice = random.choice(p_big_cells)

        _place_big_cell(choice, data)

        big_cells[*choice] = True

        # Taking intersecting vacancies out
        p_big_cells = [
            cell for cell in p_big_cells if _max_point_difference(cell, choice) > 1
        ]

    # It's time to turn cells into bool array
    cells = np.empty((w, h), bool)
    for x, y in itertools.product(range(w), range(h)):
        cells[x, y] = data.cells[x, y] == _BODY

    return (
        cells,
        big_cells,
        data.hor_doors,
        data.ver_doors,
        chests,
    )


def generate(
    w: int, h: int, px: int, py: int, chance: float = 0.35, c: int = 3
) -> types.GenericAlias(tuple, (_ndbool,) * 4 + (list[_point],)):
    """
    Generates and returns the data using the "Rooms" model generation.

    w
        level width.
    h
        level height.
    px
        generation epicenter x coordinate.
    py
        generation epicenter y coordinate.
    chance
        parameter that determines the probability of continuing additional wirings after the first one during the dead ends processing.
    c
        parameter that defines the maximum number of heads spawned during the loop.
    """
    if w <= 0:
        raise ValueError(f"w must be positive")

    if h <= 0:
        raise ValueError(f"h must be positive")

    if not (0 <= px < w):
        raise ValueError(f"0 <= px < w must be True")

    if not (0 <= py < h):
        raise ValueError(f"0 <= py < h must be True")

    if not (0.0 < chance < 1.0):
        raise ValueError(f"0.0 < chance < 1.0 must be True")

    if c < 0:
        raise ValueError(f"c can not be negative")

    cells = np.full((w, h), _EMPTY, int)

    data = _Arrays(
        cells=cells,
        hor_doors=np.full((w - 1, h), False, bool),
        ver_doors=np.full((w, h - 1), False, bool),
    )

    filter_ = _PointChecker(w, h)

    spawners = [(px, py)]
    cells[px, py] = _SPAWNER

    del px, py

    # Potential heads
    vacancies = set()

    while True:
        # Fill in vacancies
        for spawner in spawners:
            vacancies.update(
                [
                    cell
                    for cell in _get_nbr_points(spawner, filter_)
                    if cells[*cell] == _EMPTY
                ]
            )

        match len(vacancies):
            case 0:
                # No vacancy may be created
                for spawner in spawners:
                    cells[*spawner] = _BODY

                return _finish(w, h, data, filter_, chance)
            case L if L > c:
                # Pick the maximum of c heads
                heads = random.sample(sorted(vacancies), c)
            case _:
                # Pick all the heads
                heads = vacancies

        # Wire the head with adjacent spawners
        for head in heads:
            _wire(head, data, filter_)

        # Turn spawners into body
        for spawner in spawners:
            cells[*spawner] = _BODY

        # Turn heads into spawners
        spawners.clear()
        spawners.extend(heads)
        for spawner in spawners:
            cells[*spawner] = _SPAWNER

        vacancies.clear()
