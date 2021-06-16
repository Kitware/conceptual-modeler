from enum import Enum, unique

# Added to fix gdal 3.3.0 error
from osgeo import gdal

import gempy as gp
import numpy as np

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------


def to_id_order(item):
    return (item.id, item.order)


def to_name_order(item):
    return (item.name, item.order)


def take_first(item):
    return item[0]


def take_second(item):
    return item[1]


def next_order_size(list, **kwargs):
    return len(list)


# -----------------------------------------------------------------------------
# Helper classes
# -----------------------------------------------------------------------------


class Grid:
    def __init__(self):
        self.extent = [0, 100, 0, 100, 0, 100]
        self.resolution = [10, 10, 10]


class AbstractSortedList:
    def __init__(self, klass, next_order):
        self._klass = klass
        self._next_order = next_order
        self._next_id = 0
        self._list = []
        self._active_id = None

    def __getitem__(self, id):
        for item in self._list:
            if item.id == id:
                return item
        return None

    @property
    def selected(self):
        return self._active_id

    @selected.setter
    def selected(self, value):
        self._active_id = value

    @property
    def names(self):
        list = map(to_name_order, self._list)
        sorted_list = sorted(list, key=take_second)
        return map(take_first, sorted_list)

    @property
    def ids(self):
        list = map(to_id_order, self._list)
        sorted_list = sorted(list, key=take_second)
        return map(take_first, sorted_list)

    def add(self, name, **kwargs):
        self._next_id += 1
        order = self._next_order(self._list, **kwargs)
        self._list.append(
            self._klass(name, id=f"{name}_{self._next_id}", **kwargs, order=order)
        )

    def remove(self, id):
        to_delete = self[id]
        if to_delete:
            self._list.remove(to_delete)
            return True

        return False

    def up(self, id):
        ids = self.ids
        index = ids.index(id)
        if len(ids) > index + 1:
            next_id = ids[index + 1]
            from_item = self[id]
            to_item = self[next_id]
            from_order = from_item.order
            to_order = to_item.order
            to_item.order = from_order
            from_item.order = to_order
            return True

        return False

    def down(self, id):
        ids = self.ids
        index = ids.index(id)
        if index > 1:
            prev_id = ids[index - 1]
            from_item = self[id]
            to_item = self[prev_id]
            from_order = from_item.order
            to_order = to_item.order
            to_item.order = from_order
            from_item.order = to_order
            return True

        return False


class Surface:
    def __init__(self, name, id=None, order=0):
        self.name = name
        self.id = id if id else name
        self.order = order


class Surfaces(AbstractSortedList):
    def __init__(self):
        super().__init__(Surface, next_order_size)

    @property
    def surface(self):
        return self[self.selected]


@unique
class Feature(Enum):
    EROSION = "Erosion"
    FAULT = "Fault"
    ONLAP = "OnLap"


class Stack:
    def __init__(self, name, feature=Feature.EROSION, order=1, id=None):
        self.id = id if id else name
        self.name = name
        self.feature = feature
        self.order = order
        self.surfaces = Surfaces()


class Stacks(AbstractSortedList):
    def __init__(self):
        super().__init__(Stack, next_order_size)
        self.add("basement", order=0)

    @property
    def stack(self):
        return self[self.selected]


# -----------------------------------------------------------------------------
# Main class
# -----------------------------------------------------------------------------


class GemPyModeler:
    def __init__(self, app):
        self._app = app

        # state
        self._grid = Grid()
        self._stacks = Stacks()

        # gempy model
        # self._model = gp.create_model('conceptual_modeler')
        # self._model.add_surfaces('basement')
        # gp.map_stack_to_surfaces(self.geo_model, mapstacks, remove_unused_series=True)
        # self.geo_model.reorder_features(orderStacks)
        # self.geo_model.set_bottom_relation(self.stacks[i]['name'], self.stacks[i-1]['feature'])

        # Update app with our shared state
        # app.state.update(INITIAL_STATE)
