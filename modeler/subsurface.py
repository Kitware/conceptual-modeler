import time
import math
from enum import Enum, unique

# Added to fix gdal 3.3.0 error
from osgeo import gdal

# import gempy as gp
import numpy as np
import gempy as gp
import json
import csv

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------


def take_order(item):
    return int(item["order"])


def create_id_generator(prefix):
    count = 1
    while True:
        yield f"{prefix}_{count}"
        count += 1


def create_index_generator():
    count = 1
    while True:
        yield count
        count += 1


# -----------------------------------------------------------------------------
# Helper classes
# -----------------------------------------------------------------------------
@unique
class Feature(Enum):
    EROSION = "Erosion"
    FAULT = "Fault"
    ONLAP = "Onlap"


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

    def export_state(self, depth=-1):
        return {
            "extent": self.extent,
            "resolution": self.resolution,
        }

    def import_state(self, content):
        if not content:
            return

        self.extent = content.get("extent", self.extent)
        self.resolution = content.get("resolution", self.resolution)


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

    def find_by_id(self, id):
        for item in self._data.values():
            if item.id == id:
                return item
        return

    @property
    def ids(self):
        results = []
        for id in self._ids:
            results.append(id)
        return results

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

    def _append_new_id(self, id):
        self._ids.append(id)

    def add(self, **kwargs):
        if not self.allowed_actions(self._active_id).get("add", False):
            return False

        item = self._klass(parent=self._parent, **kwargs)
        self._data[item.id] = item
        self._append_new_id(item.id)
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
            if id == self._active_id:
                results[-1]["selected"] = 1

        return results

    def import_state(self, content):
        if not content:
            return

        self._ids = []
        self._data = {}
        self._active_id = None
        keep_active_id = None
        for item in content:
            new_obj = self.add(**item)
            new_obj.import_state(item)
            if item.get("selected", False):
                keep_active_id = new_obj.id

        if keep_active_id:
            self._active_id = keep_active_id


class Orientation:
    id_generator = create_id_generator("Orientation")
    index_generator = create_index_generator()

    def __init__(self, x, y, z, gx, gy, gz, parent=None, **kwargs):
        self.id = next(Orientation.id_generator)
        self.idx = next(Orientation.index_generator)
        self.x = x
        self.y = y
        self.z = z
        self.poleVector = [gx, gy, gz]
        self.surface = parent

    @property
    def html(self):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "gx": self.poleVector[0],
            "gy": self.poleVector[1],
            "gz": self.poleVector[2],
            "surfacename": self.surface.name,
        }

    def export_state(self, depth=-1):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "poleVector": self.poleVector,
        }

    def out(self):
        print(self.id, self.x, self.y, self.z, self.poleVector)

    def import_state(self, content):
        self.x = content.get("x", self.x)
        self.y = content.get("y", self.y)
        self.z = content.get("z", self.z)
        self.poleVector = content.get("poleVector", self.poleVector)


class Orientations(AbstractSortedList):
    def __init__(self, parent):
        super().__init__(Orientation, parent)

    @property
    def orientation(self):
        return self[self.selected_id]

    def allowed_actions(self, id):
        allowed = super().allowed_actions(id)

        # Don't allow moving orientations
        allowed["down"] = 0
        allowed["up"] = 0

        return allowed

    def remove(self, id):
        if not self.allowed_actions(id).get("remove", False):
            return

        idx = self[id].idx
        if self._data.pop(id, None):
            self._ids.remove(id)
            if self._active_id == id:
                self._active_id = None
            return idx

        return


class Point:
    id_generator = create_id_generator("Point")
    index_generator = create_index_generator()

    def __init__(self, x, y, z, parent=None, **kwargs):
        self.id = next(Point.id_generator)
        self.idx = next(Point.index_generator)
        self.x = x
        self.y = y
        self.z = z
        self.surface = parent

    @property
    def html(self):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "surfacename": self.surface.name,
        }

    def export_state(self, depth=-1):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "z": self.z,
        }

    def out(self):
        print(self.id, self.x, self.y, self.z)

    def import_state(self, content):
        self.x = content.get("x", self.x)
        self.y = content.get("y", self.y)
        self.z = content.get("z", self.z)


class Points(AbstractSortedList):
    def __init__(self, parent):
        super().__init__(Point, parent)

    @property
    def point(self):
        return self[self.selected_id]

    def allowed_actions(self, id):
        allowed = super().allowed_actions(id)

        # Don't allow moving points
        allowed["down"] = 0
        allowed["up"] = 0

        return allowed

    def remove(self, id):
        if not self.allowed_actions(id).get("remove", False):
            return

        idx = self[id].idx
        if self._data.pop(id, None):
            self._ids.remove(id)
            if self._active_id == id:
                self._active_id = None
            return idx

        return


class Surface:
    id_generator = create_id_generator("Surface")

    def __init__(self, name, parent=None, **kwargs):
        self.id = next(Surface.id_generator)
        self.name = name
        self.points = Points(self)
        self.orientations = Orientations(self)
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
        out = {
            "id": self.id,
            "name": self.name,
        }

        if depth:
            out["points"] = self.points.export_state(depth - 1)
            out["orientations"] = self.orientations.export_state(depth - 1)
        return out

    def out(self):
        print(self.id, self.name)

    def import_state(self, content):
        self.name = content.get("name", self.name)

        points = content.get("points", None)
        if points:
            self.points.import_state(points)

        orientations = content.get("orientations", None)
        if orientations:
            self.orientations.import_state(orientations)


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
        if self._parent.name == "Basement":
            allowed["add"] = len(self) == 0
            allowed["down"] = 0
            allowed["up"] = 0
            allowed["remove"] = 0

        return allowed

    def reverse_ids(self):
        results = self.ids
        results.reverse()
        return results

    def remove(self, id):
        if not self.allowed_actions(id).get("remove", False):
            return

        if self._data.pop(id, None):
            self._ids.remove(id)
            if self._active_id == id:
                self._active_id = None
            return id

        return

    def add_surface(self, name, **kwargs):
        if not self.allowed_actions(self._active_id).get("add", False):
            return False

        item = self._klass(name, parent=self._parent, **kwargs)
        self._data[item.id] = item
        self._append_new_id(item.id)
        return item

    def find_by_name(self, name):
        for surface in self._data.values():
            if surface.name == name:
                return surface
        return


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

    def out(self):
        print(self.id, self.name, self.feature.value)

    def import_state(self, content):
        self.name = content.get("name", self.name)
        self.feature = content.get("feature", self.feature)
        if not isinstance(self.feature, Feature):
            self.feature = Feature(self.feature)

        surfaces = content.get("surfaces", None)
        if surfaces:
            self.surfaces.import_state(surfaces)


class Stacks(AbstractSortedList):
    def __init__(self):
        super().__init__(Stack)

    @property
    def stack(self):
        return self[self.selected_id]

    def allowed_actions(self, id):
        allowed = super().allowed_actions(id)

        if id in self._data:
            idx = self._ids.index(id)
            # Basement constraints
            allowed["down"] = idx > 1
            allowed["up"] &= idx > 0
            allowed["remove"] = idx > 0
            # Fault constraints
            stack = self._data[self._ids[idx]]
            if idx > 0:
                stack_below = self._data[self._ids[idx - 1]]
                if (
                    stack.feature == Feature.FAULT
                    and stack_below.feature != Feature.FAULT
                ):
                    allowed["down"] = 0
            if idx < (len(self._ids) - 1):
                stack_above = self._data[self._ids[idx + 1]]
                if (
                    stack.feature != Feature.FAULT
                    and stack_above.feature == Feature.FAULT
                ):
                    allowed["up"] = 0

        return allowed

    def add_stack(self, name, **kwargs):
        if not self.allowed_actions(self._active_id).get("add", False):
            return False

        item = self._klass(name, parent=self._parent, **kwargs)
        self._data[item.id] = item
        self._append_new_id(item.id)
        return item

    def remove(self, id):
        if not self.allowed_actions(id).get("remove", False):
            return

        stack = self._data[id]
        ids = stack.surfaces.ids
        if self._data.pop(id, None):
            self._ids.remove(id)
            if self._active_id == id:
                self._active_id = None
            return ids

        return

    def find_by_name(self, name):
        for stack in self._data.values():
            if stack.name == name:
                return stack
        return

    def find_index(self, name):
        for i in range(len(self._ids)):
            stack = self._data[self._ids[i]]
            if stack.name == name:
                return i
        return

    def find_surface_by_name(self, name):
        for stack in self._data.values():
            surface = stack.surfaces.find_by_name(name)
            if surface:
                return surface
        return

    def find_surface_by_id(self, id):
        for stack in self._data.values():
            surface = stack.surfaces.find_by_id(id)
            if surface:
                return surface
        return

    def _insert_new_id(self, name, id):
        index = self.find_index(name)
        if index:
            self._ids.insert(index, id)
        else:
            self._ids.append(id)

    def insert(self, location_name, name, **kwargs):
        if not self.allowed_actions(self._active_id).get("add", False):
            return False

        item = self._klass(name, parent=self._parent, **kwargs)
        self._data[item.id] = item
        self._insert_new_id(location_name, item.id)
        return item

    def map_stack_to_surfaces(self):
        mapstacks = {}
        for id in self._ids:
            stack = self._data[id]
            surfacesNames = stack.surfaces.reverse_ids()
            if len(surfacesNames) > 0:
                surfacesNames.reverse()
                mapstacks[stack.id] = surfacesNames
        return mapstacks

    def reorder_features(self):
        reorderedfeatures = []
        for id in self._ids:
            stack = self._data[id]
            surfacesNames = stack.surfaces.reverse_ids()
            if len(surfacesNames) > 0:
                reorderedfeatures.append(stack.id)
        reorderedfeatures.reverse()
        return reorderedfeatures

    def bottom_relations(self):
        bottomrelations = []
        reorderedfeatures = self.reorder_features()
        if len(reorderedfeatures) > 1:
            for i in range(0, len(reorderedfeatures) - 1, 1):
                stack = self.find_by_id(reorderedfeatures[i])
                nextstack = self.find_by_id(reorderedfeatures[i + 1])
                if stack.feature == Feature.FAULT:
                    bottomrelations.append(
                        {"name": stack.id, "feature": stack.feature.value}
                    )
                else:
                    bottomrelations.append(
                        {"name": stack.id, "feature": nextstack.feature.value}
                    )
        return bottomrelations

    def is_a_fault(self):
        isafault = []
        reorderedfeatures = self.reorder_features()
        if len(reorderedfeatures) > 1:
            for i in range(0, len(reorderedfeatures) - 1, 1):
                stack = self.find_by_id(reorderedfeatures[i])
                if stack.feature == Feature.FAULT:
                    isafault.append(stack.id)
        return isafault

    def find_oldest_fault_name(self):
        for id in self._ids:
            stack = self._data[id]
            if stack.feature == Feature.FAULT:
                return stack.name
        return


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
        grid = self.grid.html
        stacks_html = self.stacks.html
        active_stack = self.stacks.stack
        active_stack_id = None
        stack_actions = {}
        surfaces = None
        surfaces_html = None
        active_surface = None
        active_surface_id = None
        surface_actions = {}
        points = None
        points_html = None
        active_point_id = None
        point_actions = {}
        orientations = None
        orientations_html = None
        active_orientation_id = None
        orientation_actions = {}

        if active_stack:
            active_stack_id = active_stack.id
            stack_actions = self.stacks.allowed_actions(active_stack_id)
            surfaces = active_stack.surfaces

        if surfaces:
            surfaces_html = surfaces.html
            active_surface_id = surfaces.selected_id
            surface_actions = surfaces.allowed_actions(active_surface_id)
            active_surface = surfaces.surface

        if active_surface:
            points = active_surface.points
            active_point_id = points.selected_id
            point_actions = points.allowed_actions(active_point_id)
            points_html = points.html
            orientations = active_surface.orientations
            active_orientation_id = orientations.selected_id
            orientation_actions = orientations.allowed_actions(active_orientation_id)
            orientations_html = orientations.html

        return {
            "features": [a.value for a in Feature],
            "grid": grid,
            "stacks": stacks_html,
            "activeStackId": active_stack_id,
            "activeStackActions": stack_actions,
            "surfaces": surfaces_html,
            "activeSurfaceId": active_surface_id,
            "activeSurfaceActions": surface_actions,
            "points": points_html,
            "activePointActions": point_actions,
            "activePointId": active_point_id,
            "orientations": orientations_html,
            "activeOrientationActions": orientation_actions,
            "activeOrientationId": active_orientation_id,
            "subsurfaceImportTS": 0,
            "subsurfaceState": None,
        }

    def find_stack_by_name(self, name):
        return self.stacks.find_by_name(name)

    def find_stack_by_id(self, id):
        return self.stacks.find_by_id(id)

    def find_surface_by_name(self, name):
        return self.stacks.find_surface_by_name(name)

    def find_surface_by_id(self, id):
        return self.stacks.find_surface_by_id(id)

    def map_stack_to_surfaces(self):
        return self.stacks.map_stack_to_surfaces()

    def reorder_features(self):
        return self.stacks.reorder_features()

    def bottom_relations(self):
        return self.stacks.bottom_relations()

    def is_a_fault(self):
        return self.stacks.is_a_fault()

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
            if Feature(data["feature"]) == Feature.FAULT:
                return self.stacks.add_stack(**data)
            else:
                oldest_fault_name = self.stacks.find_oldest_fault_name()
                if oldest_fault_name:
                    return self.stacks.insert(oldest_fault_name, **data)
                else:
                    return self.stacks.add_stack(**data)
        elif type == "Surface":
            if "stackname" in data:
                return self.stacks.find_by_name(data["stackname"]).surfaces.add_surface(
                    data["name"]
                )
            else:
                return self.stacks[data["stackid"]].surfaces.add_surface(data["name"])
        elif type == "Point":
            if "surfacename" in data:
                surface = self.stacks.find_surface_by_name(data["surfacename"])
                if surface:
                    return surface.points.add(**data)
            else:
                surface = self.stacks.find_surface_by_id(data["surfaceid"])
                if surface:
                    return surface.points.add(**data)
        elif type == "Orientation":
            if "surfacename" in data:
                surface = self.stacks.find_surface_by_name(data["surfacename"])
                if surface:
                    return surface.orientations.add(**data)
            else:
                surface = self.stacks.find_surface_by_id(data["surfaceid"])
                if surface:
                    return surface.orientations.add(**data)

    def remove(self, type, id):
        if type == "Stack":
            return self.stacks.remove(id)
        elif type == "Surface" and self.stacks.stack:
            return self.stacks.stack.surfaces.remove(id)
        elif (
            type == "Point" and self.stacks.stack and self.stacks.stack.surfaces.surface
        ):
            return self.stacks.stack.surfaces.surface.points.remove(id)
        elif (
            type == "Orientation"
            and self.stacks.stack
            and self.stacks.stack.surfaces.surface
        ):
            return self.stacks.stack.surfaces.surface.orientations.remove(id)

    def select(self, type, id):
        if type == "Stack":
            stacks = self.stacks
            if stacks.selected_id != id:
                stacks.selected_id = id
            else:
                stacks.selected_id = None
        elif type == "Surface" and self.stacks.stack:
            surfaces = self.stacks.stack.surfaces
            if surfaces.selected_id != id:
                surfaces.selected_id = id
            else:
                surfaces.selected_id = None
        elif (
            type == "Point" and self.stacks.stack and self.stacks.stack.surfaces.surface
        ):
            points = self.stacks.stack.surfaces.surface.points
            if points.selected_id != id:
                points.selected_id = id
            else:
                points.selected_id = None
        elif (
            type == "Orientation"
            and self.stacks.stack
            and self.stacks.stack.surfaces.surface
        ):
            orientations = self.stacks.stack.surfaces.surface.orientations
            if orientations.selected_id != id:
                orientations.selected_id = id
            else:
                orientations.selected_id = None

    def import_state(self, parsed_json_structure):
        self.grid.import_state(parsed_json_structure.get("grid", None))
        self.stacks.import_state(parsed_json_structure.get("stacks", None))

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
        # Create GemPy Model
        self._geo_model = gp.create_model("conceptual_modeler")
        # Initialize GemPy Interpolator
        gp.set_interpolator(
            self._geo_model,
            output=["geology"],
            theano_optimizer="fast_compile",
        )
        # Add Basement Stack
        type = "Stack"
        data = {"name": "Basement", "feature": Feature.EROSION}
        self.add(type, data)
        # Add basement Surface to Basement Stack
        type = "Surface"
        data = {"name": "basement", "stackname": "Basement"}
        self.add(type, data)
        # Set the basement Surface as the basement
        surfaces = gp.Surfaces(gp.Series(self._geo_model.faults))
        surfaces.set_basement()

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

        # Push all if no args provided
        if len(args) == 0:
            for name in state:
                self._app.set(name, state[name], force=True)

    def dirty_state(self, type):
        """type@app: Stack, Surface, Point, Orientation"""
        dirty_list = []
        stack_state_list = ["stacks", "activeStackId", "activeStackActions"]
        surface_state_list = ["surfaces", "activeSurfaceId", "activeSurfaceActions"]
        point_state_list = ["points", "activePointId", "activePointActions"]
        orientation_state_list = [
            "orientations",
            "activeOrientationId",
            "activeOrientationActions",
        ]

        if type == "Stack":
            dirty_list.extend(stack_state_list)
            dirty_list.extend(surface_state_list)
            dirty_list.extend(point_state_list)
            dirty_list.extend(orientation_state_list)
        elif type == "Surface":
            dirty_list.extend(surface_state_list)
            dirty_list.extend(point_state_list)
            dirty_list.extend(orientation_state_list)
        elif type == "Point":
            dirty_list.extend(point_state_list)
        elif type == "Orientation":
            dirty_list.extend(orientation_state_list)

        if len(dirty_list):
            self.dirty(*dirty_list)

    @property
    def state_handler(self):
        return self._state_handler

    # -----------------------------------------------------
    # Grid
    # -----------------------------------------------------

    def update_grid(self, extent, resolution):
        self._state_handler.grid.extent = extent
        self._state_handler.grid.resolution = resolution
        gp.init_data(
            self._geo_model,
            extent=extent,
            resolution=resolution,
        )
        self.dirty("grid")

    # -----------------------------------------------------
    # State mutation
    # -----------------------------------------------------

    def add(self, type, data):
        """type@html: Stack, Surface, Point, Orientation"""
        item = self._state_handler.add(type, data)
        if item:
            if type == "Stack":
                self.add_stack(type, data)
            elif type == "Surface":
                self.add_surface(item)
            elif type == "Point":
                self.add_point(item)
            elif type == "Orientation":
                self.add_orientation(item)

            # print("** GemPy Fault Relations **")
            # print(self._geo_model._faults.faults_relations_df)
            # print("** GemPy Faults **")
            # print(self._geo_model._faults)
            # print("** GemPy Surfaces **")
            # print(self._geo_model._surfaces)

    def remove(self, type, id):
        """type@html: Stack, Surface, Point, Orientation"""
        index = self._state_handler.remove(type, id)
        if index:
            if type == "Stack":
                self.remove_stack(index)
            if type == "Surface":
                self.remove_surface(index)
            if type == "Point":
                self.remove_point(index)
            if type == "Orientation":
                self.remove_orientation(index)
            self.dirty_state(type)

    def select(self, type, id):
        """type@app: Stack, Surface, Point, Orientation"""
        self._state_handler.select(type, id)
        self.dirty_state(type)

    def move(self, type, direction):
        if self._state_handler.move(type, direction):
            self.dirty(f"{type.lower()}s", f"active{type}Actions")

    def add_stack(self, type, data):
        stack = self._state_handler.find_stack_by_name(data["name"])
        self.dirty_state(type)

    def remove_stack(self, ids):
        for id in ids:
            self._geo_model.delete_surfaces(id)
        mapstacks = self._state_handler.map_stack_to_surfaces()
        gp.map_stack_to_surfaces(self._geo_model, mapstacks, remove_unused_series=True)
        reorderedfeatures = self._state_handler.reorder_features()
        if len(reorderedfeatures) > 1:
            self._geo_model.reorder_features(reorderedfeatures)
        bottomrelations = self._state_handler.bottom_relations()
        for layer in bottomrelations:
            self._geo_model.set_bottom_relation(layer["name"], layer["feature"])
        isafault = self._state_handler.is_a_fault()
        if len(isafault) > 0:
            self._geo_model.set_is_fault(isafault)
        self.dirty_state("Stack")

    def add_surface(self, surface):
        self._geo_model.add_surfaces(surface.id)
        mapstacks = self._state_handler.map_stack_to_surfaces()
        gp.map_stack_to_surfaces(self._geo_model, mapstacks, remove_unused_series=True)
        reorderedfeatures = self._state_handler.reorder_features()
        if len(reorderedfeatures) > 1:
            self._geo_model.reorder_features(reorderedfeatures)
        bottomrelations = self._state_handler.bottom_relations()
        for layer in bottomrelations:
            self._geo_model.set_bottom_relation(layer["name"], layer["feature"])
        isafault = self._state_handler.is_a_fault()
        if len(isafault) > 0:
            self._geo_model.set_is_fault(isafault)
        self.dirty_state("Surface")

    def remove_surface(self, id):
        self._geo_model.delete_surfaces(id)
        mapstacks = self._state_handler.map_stack_to_surfaces()
        gp.map_stack_to_surfaces(self._geo_model, mapstacks, remove_unused_series=True)
        reorderedfeatures = self._state_handler.reorder_features()
        if len(reorderedfeatures) > 1:
            self._geo_model.reorder_features(reorderedfeatures)
        bottomrelations = self._state_handler.bottom_relations()
        for layer in bottomrelations:
            self._geo_model.set_bottom_relation(layer["name"], layer["feature"])
        isafault = self._state_handler.is_a_fault()
        if len(isafault) > 0:
            self._geo_model.set_is_fault(isafault)
        self.dirty_state("Surface")

    def add_point(self, point):
        self._geo_model.add_surface_points(
            X=point.x,
            Y=point.y,
            Z=point.z,
            surface=point.surface.id,
            idx=point.idx,
        )
        self.dirty_state("Point")

    def remove_point(self, index):
        self._geo_model.delete_surface_points(index)
        self.dirty_state("Point")

    def add_orientation(self, orientation):
        self._geo_model.add_orientations(
            X=orientation.x,
            Y=orientation.y,
            Z=orientation.z,
            surface=orientation.surface.id,
            idx=orientation.idx,
            pole_vector=orientation.poleVector,
        )
        self.dirty_state("Orientation")

    def remove_orientation(self, index):
        self._geo_model.delete_orientations(index)
        self.dirty_state("Orientation")

    # -----------------------------------------------------
    # Geometry accessors
    # -----------------------------------------------------

    def compute_geo_model(self):
        gp.compute_model(self._geo_model)

    @property
    def litho(self):
        resolution = self._geo_model._grid.regular_grid.resolution
        if len(resolution) != 3:
            return None

        nx, ny, nz = resolution
        size = nx * ny * nz
        array = self._geo_model.solutions.lith_block
        print("lito size", (nx, ny, nz), size, array.size)
        if size != array.size:
            return None

        return array.view().reshape(nx, ny, nz)

    @property
    def blanking(self):
        resolution = self._geo_model._grid.regular_grid.resolution
        if len(resolution) != 3:
            return None

        nx, ny, nz = resolution
        size = nx * ny * nz
        array = self._geo_model._grid.regular_grid.mask_topo
        print("blanking size", (nx, ny, nz), size, array.size)
        if size != array.size:
            return None

        return array.view().reshape(nx, ny, nz)

    # -----------------------------------------------------
    # Import / Export data
    # -----------------------------------------------------

    def export(self):
        out = self._state_handler.export_state()
        self._app.set("subsurfaceState", out, force=True)
        return out

    def import_data(self, data_type, file_data):
        # print(f'{data_type}: {" ".join(file_data.keys())}')
        file_bytes = file_data.get("content")
        # file_name = file_data.get("name")
        # file_size = file_data.get("size")

        if data_type == "grid.csv":
            grid_data = self.parse_grid_csv(file_bytes)
            if grid_data:
                self.dirty("grid")
                self.update_grid(**grid_data)
                self._app.set("subsurfaceImportTS", time.time())
        elif data_type == "stacks.csv":
            stack_data = self.parse_stacks_csv(file_bytes)
            if stack_data:
                self.dirty("stacks")
        elif data_type == "surfaces.csv":
            surface_data = self.parse_surfaces_csv(file_bytes)
            if surface_data:
                self.dirty("surfaces")
        elif data_type == "points.csv":
            point_data = self.parse_points_csv(file_bytes)
            if point_data:
                self.dirty("points")
        elif data_type == "orientations.csv":
            orientation_data = self.parse_orientations_csv(file_bytes)
            if orientation_data:
                self.dirty("orientations")
        elif data_type == "full-model.json":
            full_data = json.loads(file_bytes.decode("utf-8"))
            self._state_handler.import_state(full_data)
            # TODO: gempy flush
            self.dirty()
            self._app.set("subsurfaceImportTS", time.time())
        else:
            print(f"Do not know how to handle type: {data_type}")

    def parse_grid_csv(self, content):
        reader = csv.DictReader(content.decode("utf-8").splitlines(), delimiter=",")
        for row in reader:
            if (
                "xmin" in row
                and "xmax" in row
                and "ymin" in row
                and "ymax" in row
                and "zmin" in row
                and "zmax" in row
                and "nx" in row
                and "ny" in row
                and "nz" in row
            ):
                return {
                    "extent": [
                        float(row["xmin"]),
                        float(row["xmax"]),
                        float(row["ymin"]),
                        float(row["ymax"]),
                        float(row["zmin"]),
                        float(row["zmax"]),
                    ],
                    "resolution": [
                        int(row["nx"]),
                        int(row["ny"]),
                        int(row["nz"]),
                    ],
                }
            else:
                print("Bad grid.csv file")
                return

    def parse_stacks_csv(self, content):
        reader = csv.DictReader(content.decode("utf-8").splitlines(), delimiter=",")
        stacks = sorted(reader, key=take_order)
        for row in stacks:
            if "stack" in row and "feature" in row and "order" in row:
                self.add("Stack", {"name": row["stack"], "feature": row["feature"]})
            else:
                print("Bad stacks.csv file")
                return
        return stacks

    def parse_surfaces_csv(self, content):
        reader = csv.DictReader(content.decode("utf-8").splitlines(), delimiter=",")
        surfaces = sorted(reader, key=take_order)
        for row in surfaces:
            if "formation" in row and "stack" in row and "order" in row:
                self.add(
                    "Surface", {"name": row["formation"], "stackname": row["stack"]}
                )
            else:
                print("Bad surfaces.csv file")
                return
        return surfaces

    def parse_points_csv(self, content):
        points = csv.DictReader(content.decode("utf-8").splitlines(), delimiter=",")
        for row in points:
            if "X" in row and "Y" in row and "Z" in row and "formation" in row:
                self.add(
                    "Point",
                    {
                        "x": row["X"],
                        "y": row["Y"],
                        "z": row["Z"],
                        "surfacename": row["formation"],
                    },
                )
            else:
                print("Bad points.csv file")
                return
        return points

    def parse_orientations_csv(self, content):
        orientations = csv.DictReader(
            content.decode("utf-8").splitlines(), delimiter=","
        )
        for row in orientations:
            if (
                "X" in row
                and "Y" in row
                and "Z" in row
                and "G_x" in row
                and "G_y" in row
                and "G_z" in row
                and "formation" in row
            ):
                self.add(
                    "Orientation",
                    {
                        "x": row["X"],
                        "y": row["Y"],
                        "z": row["Z"],
                        "gx": row["G_x"],
                        "gy": row["G_y"],
                        "gz": row["G_z"],
                        "surfacename": row["formation"],
                    },
                )
            elif (
                "X" in row
                and "Y" in row
                and "Z" in row
                and "dip" in row
                and "azimuth" in row
                and "polarity" in row
                and "formation" in row
            ):
                diprad = row["dip"] * math.pi / 180.0
                azimuthrad = row["azimuth"] * math.pi / 180.0
                polarity = row["polarity"]
                gx = math.sin(diprad) * math.sin(azimuthrad) * polarity + 1e-12
                gy = math.sin(diprad) * math.cos(azimuthrad) * polarity + 1e-12
                gz = math.cos(diprad) * polarity + 1e-12
                self.add(
                    "Orientation",
                    {
                        "x": row["X"],
                        "y": row["Y"],
                        "z": row["Z"],
                        "gx": gx,
                        "gy": gy,
                        "gz": gz,
                        "surfacename": row["formation"],
                    },
                )
            else:
                print("Bad orientations.csv file")
                return
        return orientations
