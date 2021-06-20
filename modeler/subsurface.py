import time
from enum import Enum, unique

# Added to fix gdal 3.3.0 error
from osgeo import gdal

# import gempy as gp
import numpy as np
import gempy as gp
from . import importer

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


def create_id_generator(prefix):
    count = 1
    while True:
        yield f"{prefix}_{count}"
        count += 1


# -----------------------------------------------------------------------------
# Helper classes
# -----------------------------------------------------------------------------
@unique
class Feature(Enum):
    EROSION = "Erosion"
    FAULT = "Fault"
    ONLAP = "OnLap"


class Grid:
    def __init__(self):
        self.extent = [0, 100, 0, 100, 0, 100]
        self.resolution = [10, 10, 10]

    @property
    def html(self):
        return {
            "extent": self.extent,
            "resolution": self.resolution,
        }


class AbstractSortedList:
    def __init__(self, klass, parent=None):
        self._parent = parent
        self._klass = klass
        self._ids = []
        self._data = {}
        self._active_id = None

    def __getitem__(self, id):
        if id in self._data:
            return self._data[id]

    def __len__(self):
        return len(self._ids)

    @property
    def selected_id(self):
        return self._active_id

    @selected_id.setter
    def selected_id(self, value):
        self._active_id = value

    # @property
    # def selected(self):
    #     if self._active_id in self._data:
    #         return self._data[self._active_id]

    # @selected.setter
    # def selected(self, value):
    #     self._active_id = None
    #     for id in self._data:
    #         if self._data[id] == value:
    #             self._active_id = id
    #             break

    @property
    def names(self):
        results = []
        for id in self._ids:
            item = self._data[id]
            results.append(item.name)
        return results

    @property
    def ids(self):
        return self._ids

    @property
    def html(self):
        results = []
        for id in self._ids:
            item = self._data[id]
            out = {"id": id}
            out.update(item.html)
            results.append(out)

        results.reverse()

        return results

    def allowed_actions(self, id):
        actions = {
            "add": 1,
            "remove": 0,
            "up": 0,
            "down": 0,
        }
        if id in self._data:
            idx = self._ids.index(id)
            last_idx = len(self._ids) - 1
            actions["remove"] = 1
            actions["up"] = int(idx < last_idx)
            actions["down"] = int(idx > 0)

        return actions

    def _insert_new_id(self, id):
        self._ids.append(id)

    def add(self, name, **kwargs):
        if not self.allowed_actions(self._active_id).get("add", False):
            return False

        item = self._klass(name, parent=self._parent, **kwargs)
        self._data[item.id] = item
        self._insert_new_id(item.id)
        self._active_id = item.id
        return item

    def remove(self, id):
        if not self.allowed_actions(id).get("remove", False):
            return False

        if self._data.pop(id, None):
            self._ids.remove(id)
            if self._active_id == id:
                self._active_id = None
            return True

        return False

    def up(self, id):
        if not self.allowed_actions(id).get("up", False):
            return False

        l = self._ids
        index = l.index(id)
        if len(l) > index + 1:
            l[index], l[index + 1] = l[index + 1], l[index]
            return True

        return False

    def down(self, id):
        if not self.allowed_actions(id).get("down", False):
            return False

        l = self._ids
        index = l.index(id)
        if index > 0:
            l[index], l[index - 1] = l[index - 1], l[index]
            return True

        return False

    def export_state(self, depth=-1):
        results = []
        for id in self._ids:
            results.append(self[id].export_state(depth - 1))
        return results


class Surface:
    id_generator = create_id_generator("Surface")

    def __init__(self, name, parent=None, **kwargs):
        self.id = next(Surface.id_generator)
        self.name = name
        self.points = []
        self.orientations = []
        self.stack = parent

    @property
    def html(self):
        return {
            "id": self.id,
            "name": self.name,
            "feature": self.stack.feature.value,
            "stackname": self.stack.name,
        }

    def export_state(self, depth=-1):
        return {
            "id": self.id,
            "name": self.name,
        }


class Surfaces(AbstractSortedList):
    def __init__(self, parent):
        super().__init__(Surface, parent)

    @property
    def surface(self):
        return self[self.selected_id]

    def allowed_actions(self, id):
        allowed = super().allowed_actions(id)

        # A fault can only have 1 surface
        if self._parent.feature == Feature.FAULT:
            allowed["add"] = len(self) == 0

        return allowed


class Stack:
    id_generator = create_id_generator("Stack")

    def __init__(self, name, feature=Feature.EROSION, **kwargs):
        self.id = next(Stack.id_generator)
        self.name = name
        self.surfaces = Surfaces(self)

        if isinstance(feature, Feature):
            self.feature = feature
        else:
            self.feature = Feature(feature)

    @property
    def html(self):
        return {
            "name": self.name,
            "feature": self.feature.value,
        }

    def export_state(self, depth=-1):
        out = {
            "id": self.id,
            "name": self.name,
            "feature": self.feature.value,
        }

        if depth:
            out["surfaces"] = self.surfaces.export_state(depth - 1)

        return out


class Stacks(AbstractSortedList):
    def __init__(self):
        super().__init__(Stack)
        self.add("basement", feature=Feature.EROSION)

    @property
    def stack(self):
        return self[self.selected_id]

    def allowed_actions(self, id):
        allowed = super().allowed_actions(id)
        # add more constraints

        return allowed


# -----------------------------------------------------------------------------
# State Manager
# -----------------------------------------------------------------------------


class StateManager:
    def __init__(self):
        self.grid = Grid()
        self.stacks = Stacks()

    def __getitem__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]

    @property
    def client_state(self):
        return {
            "subsurfaceImportTS": 0,
            "features": [a.value for a in Feature],
            "grid": self.grid.html,
            "activeStackId": self.stacks.selected_id,
            "activeStackActions": self.stacks.allowed_actions(self.stacks.selected_id),
            "stacks": self.stacks.html,
            "surfaces": self.stacks.stack.surfaces.html if self.stacks.stack else [],
            "activeSurfaceActions": self.stacks.stack.surfaces.allowed_actions(
                self.stacks.stack.surfaces.selected_id
            )
            if self.stacks.stack
            else {},
            "activeSurfaceId": self.stacks.stack.surfaces.selected_id
            if self.stacks.stack
            else None,
        }

    def move(self, type, direction):
        active_stack = self.stacks.stack
        if active_stack:
            if type == "Stack":
                if direction == "up":
                    return self.stacks.up(active_stack.id)
                else:
                    return self.stacks.down(active_stack.id)
            elif type == "Surface":
                active_surface = active_stack.surfaces.surface
                if direction == "up":
                    return active_stack.surfaces.up(active_surface.id)
                else:
                    return active_stack.surfaces.down(active_surface.id)

    def add(self, type, data):
        if type == "Stack":
            return self.stacks.add(**data)
        elif type == "Surface" and self.stacks.stack:
            return self.stacks.stack.surfaces.add(**data)

    def remove(self, type, id):
        if type == "Stack":
            return self.stacks.remove(id)
        elif type == "Surface" and self.stacks.stack:
            return self.stacks.stack.surfaces.remove(id)

    def select(self, type, id):
        change_detected = False
        if type == "Stack":
            change_detected = self.stacks.selected_id != id
            self.stacks.selected_id = id
        elif type == "Surface" and self.stacks.stack:
            change_detected = self.stacks.stack.surfaces.selected_id != id
            self.stacks.stack.surfaces.selected_id = id

        return change_detected

    def import_state(self, type, state):
        pass

    def export_state(self, depth=-1):
        return {
            "version": 1,
            "origin": "https://github.com/Kitware/conceptual-modeler",
            "type": "conceptual-modeler-full",
            "grid": self.grid.export_state(depth),
            "stacks": self.stacks.export_state(depth),
        }


# -----------------------------------------------------------------------------
# Main class
# -----------------------------------------------------------------------------


class SubSurfaceModeler:
    def __init__(self, app):
        self._app = app
        self._state_handler = StateManager()

        # gempy model
        self._has_topology = False
        self._model = gp.create_model("conceptual_modeler")
        # self._model.add_surfaces('basement')
        # gp.map_stack_to_surfaces(self.geo_model, mapstacks, remove_unused_series=True)
        # self.geo_model.reorder_features(orderStacks)
        # self.geo_model.set_bottom_relation(self.stacks[i]['name'], self.stacks[i-1]['feature'])

        # Expend shared state in app
        app.state.update(self._state_handler.client_state)

    def dirty(self, *args):
        # print('dirty', *args)
        state = self._state_handler.client_state
        # print('==> ok')
        for name in args:
            if name in state:
                self._app.set(name, state[name], force=True)
            else:
                print(f"Unable to dirty missing key {name}")

    @property
    def state_handler(self):
        return self._state_handler

    # -----------------------------------------------------
    # Grid
    # -----------------------------------------------------

    def update_grid(self, extent, resolution):
        self._state_handler.grid.extent = extent
        self._state_handler.grid.resolution = resolution
        # update gempy
        gp.init_data(
            self._model,
            extent=extent,
            resolution=resolution,
        )
        gp.set_interpolator(
            self._model,
            output=["geology"],
            theano_optimizer="fast_compile",
        )

        self.dirty("grid")

    # -----------------------------------------------------
    # State mutation
    # -----------------------------------------------------

    def add(self, type, data):
        """type@html: Stack, Surface, Point, Orientation"""
        if self._state_handler.add(type, data):
            self.dirty(f"active{type}Id", f"{type.lower()}s", f"active{type}Actions")

    def remove(self, type, id):
        """type@html: Stack, Surface, Point, Orientation"""
        if self._state_handler.remove(type, id):
            self.dirty(f"active{type}Id", f"{type.lower()}s", f"active{type}Actions")

    def select(self, type, id):
        """type@app: Stack, Surface, Point, Orientation"""
        dirty_list = []
        change_detected = self._state_handler.select(type, id)

        if type == "Stack":
            dirty_list.extend(["surfaces", "activeSurfaceId", "activeStackActions"])
        elif type == "Surface":
            if change_detected:
                dirty_list.append("activeSurfaceId")
            dirty_list.append("activeSurfaceActions")

        if len(dirty_list):
            self.dirty(*dirty_list)

    def move(self, type, direction):
        if self._state_handler.move(type, direction):
            self.dirty(f"{type.lower()}s", f"active{type}Actions")

    # -----------------------------------------------------
    # Geometry accessors
    # -----------------------------------------------------

    def compute_model(self):
        gp.compute_model(self._model)

    @property
    def litho(self):
        resolution = self._model._grid.regular_grid.resolution
        if len(resolution) != 3:
            return None

        nx, ny, nz = resolution
        size = nx * ny * nz
        array = self._model.solutions.lith_block
        print("lito size", (nx, ny, nz), size, array.size)
        if size != array.size:
            return None

        return array.view().reshape(nx, ny, nz)

    @property
    def blanking(self):
        resolution = self._model._grid.regular_grid.resolution
        if len(resolution) != 3:
            return None

        nx, ny, nz = resolution
        size = nx * ny * nz
        array = self._model._grid.regular_grid.mask_topo
        print("blanking size", (nx, ny, nz), size, array.size)
        if size != array.size:
            return None

        return array.view().reshape(nx, ny, nz)

    # -----------------------------------------------------
    # Import / Export data
    # -----------------------------------------------------

    def import_data(self, data_type, file_data):
        # print(f'{data_type}: {" ".join(file_data.keys())}')
        file_bytes = file_data.get("content")
        # file_name = file_data.get("name")
        # file_size = file_data.get("size")

        if data_type == "grid.csv":
            grid_data = importer.parse_grid_csv(file_bytes)
            if grid_data:
                self.dirty("grid")  # update client first
                self.update_grid(**grid_data)
                self._app.set("subsurfaceImportTS", time.time())
        else:
            print(f"Do not know how to handle type: {data_type}")
