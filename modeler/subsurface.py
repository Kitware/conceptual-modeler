import time
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


def to_id_order(item):
    return (item.id, item.order)


def to_name_order(item):
    return (item.name, item.order)


def take_first(item):
    return item[0]


def take_second(item):
    return item[1]


def take_order(item):
    return int(item["order"])


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

    def find_index(self, name):
        for i in range(len(self._ids)):
            stack = self._data[self._ids[i]]
            if stack.name == name:
                return i
        return

    def find_by_id(self, id):
        return self._data[id]

    def find_by_name(self, name):
        for stack in self._data.values():
            if stack.name == name:
                return stack
        return

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

    def namelist(self):
        results = []
        for id in self._ids:
            item = self._data[id]
            results.append(item.name)

        results.reverse()

        return results

    def idlist(self):
        results = []
        for id in self._ids:
            results.append(id)

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

    def _insert_new_id(self, name, id):
        print("before")
        index = self.find_index(name)
        print("after", index)
        if index:
            self._ids.insert(index, id)
        else:
            self._ids.append(id)

    def add(self, name, **kwargs):
        if not self.allowed_actions(self._active_id).get("add", False):
            return False

        item = self._klass(name, parent=self._parent, **kwargs)
        self._data[item.id] = item
        self._append_new_id(item.id)
        return item

    def insert(self, locationname, name, **kwargs):
        if not self.allowed_actions(self._active_id).get("add", False):
            return False

        item = self._klass(name, parent=self._parent, **kwargs)
        self._data[item.id] = item
        print(locationname)
        item.out()
        self._insert_new_id(locationname, item.id)
        print("inserted")
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

    def out(self):
        print(self.id, self.name)

    def import_state(self, content):
        self.name = content.get("name", self.name)
        # TODO: handle points/orientations


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
        # Basement constraints
        if id in self._data:
            idx = self._ids.index(id)
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

    def map_stack_to_surfaces(self):
        mapstacks = {}
        for id in self._ids:
            stack = self._data[id]
            surfacesNames = stack.surfaces.idlist()
            if len(surfacesNames) > 0:
                surfacesNames.reverse()
                mapstacks[stack.id] = surfacesNames
        return mapstacks

    def reorder_features(self):
        reorderedfeatures = []
        for id in self._ids:
            stack = self._data[id]
            surfacesNames = stack.surfaces.idlist()
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
            "subsurfaceState": None,
        }

    def find_stack_by_name(self, name):
        return self.stacks.find_by_name(name)

    def find_stack_by_id(self, id):
        return self.stacks.find_by_id(id)

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
                return self.stacks.add(**data)
            else:
                locationname = self.stacks.find_oldest_fault_name()
                if locationname:
                    return self.stacks.insert(locationname, **data)
                else:
                    return self.stacks.add(**data)
        elif type == "Surface":
            if "stackname" in data:
                return self.stacks.find_by_name(data["stackname"]).surfaces.add(
                    data["name"]
                )
            else:
                return self.stacks[data["stackid"]].surfaces.add(data["name"])

    def remove(self, type, id):
        if type == "Stack":
            return self.stacks.remove(id)
        elif type == "Surface" and self.stacks.stack:
            return self.stacks.stack.surfaces.remove(id)

    def select(self, type, id):
        if type == "Stack":
            if self.stacks.selected_id != id:
                self.stacks.selected_id = id
            else:
                self.stacks.selected_id = None
        elif type == "Surface" and self.stacks.stack:
            if self.stacks.stack.surfaces.selected_id != id:
                self.stacks.stack.surfaces.selected_id = id
            else:
                self.stacks.stack.surfaces.selected_id = None

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
        if self._state_handler.add(type, data):
            if type == "Stack":
                stack = self._state_handler.find_stack_by_name(data["name"])
            elif type == "Surface":
                if "stackname" in data:
                    stack = self._state_handler.find_stack_by_name(data["stackname"])
                    surface = stack.surfaces.find_by_name(data["name"])
                    self._geo_model.add_surfaces(surface.id)
                else:
                    stack = self._state_handler.find_stack_by_id(data["stackid"])
                    surface = stack.surfaces.find_by_name(data["name"])
                    self._geo_model.add_surfaces(surface.id)
                mapstacks = self._state_handler.map_stack_to_surfaces()
                gp.map_stack_to_surfaces(
                    self._geo_model, mapstacks, remove_unused_series=True
                )
                reorderedfeatures = self._state_handler.reorder_features()
                if len(reorderedfeatures) > 1:
                    self._geo_model.reorder_features(reorderedfeatures)
                bottomrelations = self._state_handler.bottom_relations()
                for layer in bottomrelations:
                    self._geo_model.set_bottom_relation(layer["name"], layer["feature"])
                isafault = self._state_handler.is_a_fault()
                if len(isafault) > 0:
                    self._geo_model.set_is_fault(isafault)
            # print("** GemPy Fault Relations **")
            print(self._geo_model._faults.faults_relations_df)
            # print("** GemPy Faults **")
            print(self._geo_model._faults)
            # print("** GemPy Surfaces **")
            print(self._geo_model._surfaces)
            self.dirty(f"active{type}Id", f"{type.lower()}s", f"active{type}Actions")

    def remove(self, type, id):
        """type@html: Stack, Surface, Point, Orientation"""
        if self._state_handler.remove(type, id):
            self.dirty(f"active{type}Id", f"{type.lower()}s", f"active{type}Actions")

    def select(self, type, id):
        """type@app: Stack, Surface, Point, Orientation"""
        dirty_list = []
        self._state_handler.select(type, id)

        if type == "Stack":
            dirty_list.extend(
                ["activeStackId", "surfaces", "activeSurfaceId", "activeStackActions"]
            )
        elif type == "Surface":
            dirty_list.extend(["activeSurfaceId", "activeSurfaceActions"])

        if len(dirty_list):
            self.dirty(*dirty_list)

    def move(self, type, direction):
        if self._state_handler.move(type, direction):
            self.dirty(f"{type.lower()}s", f"active{type}Actions")

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
            stack_data = self.parse_surfaces_csv(file_bytes)
            if stack_data:
                self.dirty("surfaces")
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
        stacks = sorted(reader, key=take_order)
        for row in stacks:
            if "formation" in row and "stack" in row and "order" in row:
                self.add(
                    "Surface", {"name": row["formation"], "stackname": row["stack"]}
                )
            else:
                print("Bad surfaces.csv file")
                return
        return stacks
