from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPlane
from vtkmodules.vtkCommonCore import vtkFloatArray
from vtkmodules.vtkFiltersCore import vtkCutter, vtkThreshold
from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkRenderWindow,
    vtkDataSetMapper,
    vtkActor,
)


def slider(min, max, resolution):
    return {
        "min": min,
        "max": max,
        "step": (max - min) / (resolution - 1),
    }


class ViewView:
    def __init__(self, name="default"):
        self.name = name
        self.renderer = vtkRenderer()
        self.renderWindow = vtkRenderWindow()
        self.renderWindow.AddRenderer(self.renderer)
        self._scene = {}

        self.renderer.SetBackground(0.2, 0.4, 0.6)

    def resetCamera(self):
        self.renderer.ResetCamera()

    @property
    def camera(self):
        return self.renderer.GetActiveCamera()

    def add(self, name, source):
        if name in self._scene:
            print(f"Trying to add name({name}) twice in {self.name}")
            return None

        actor = vtkActor()
        mapper = vtkDataSetMapper()
        if source.IsA("vtkDataSet"):
            mapper.SetInputData(source)
        else:
            mapper.SetInputConnection(source.GetOutputPort())
        actor.SetMapper(mapper)
        self.renderer.AddActor(actor)
        item = {
            "name": name,
            "source": source,
            "mapper": mapper,
            "actor": actor,
        }
        self._scene[name] = item
        return item

    def get(self, name):
        return self._scene.get(name, None)

    def remove(self, name):
        item = self.get(name)
        if item:
            self.renderer.RemoveActor(item["actor"])
            self._scene.pop(name)

    @property
    def view(self):
        return self.renderWindow

    def view2D(self, axis_idx):
        positon = [0, 0, 0]
        positon[axis_idx] = -1
        self.camera.ParallelProjectionOn()
        self.camera.SetFocalPoint(0, 0, 0)
        self.camera.SetPosition(positon)

        if axis_idx == 2:
            self.camera.SetViewUp(0, 1, 0)
        else:
            self.camera.SetViewUp(0, 0, 1)


class VtkViewer:
    def __init__(self, app, modeler):
        self._app = app
        self._modeler = modeler

        # VTK
        # ref: https://github.com/cgre-aachen/gempy/blob/master/gempy/plot/visualization_3d.py
        self._grid = vtkImageData()
        self._litho_field = vtkFloatArray()
        self._litho_field.SetName("litho")
        self._blank_field = vtkFloatArray()
        self._blank_field.SetName("blank")
        self._grid.GetCellData().AddArray(self._litho_field)
        self._grid.GetCellData().SetScalars(self._blank_field)

        self._filter_threshold = vtkThreshold()
        self._filter_threshold.SetInputData(self._grid)
        self._filter_threshold.ThresholdByLower(0.5)
        # self.thresholdFilter.SetInputArrayToProcess(0, 0, 0,
        #   "vtkDataObject::FIELD_ASSOCIATION_CELLS",
        #   "blank")

        # slices
        self._slice_planes = [
            vtkPlane(),
            vtkPlane(),
            vtkPlane(),
        ]
        self._slice_filters = [
            vtkCutter(),
            vtkCutter(),
            vtkCutter(),
        ]
        for i in range(3):
            normal = [0, 0, 0]
            normal[i] = 1
            self._slice_planes[i].SetNormal(normal)
            self._slice_filters[i].SetInputData(self._grid)
            self._slice_filters[i].SetCutFunction(self._slice_planes[i])

        # Views
        self.update_grid([0, 100, 0, 100, 0, 100], [10, 10, 10], dirty=False)
        self._views = {}
        index = 0
        for key in ["vtkViewX", "vtkViewY", "vtkViewZ", "vtkView3D"]:
            view = ViewView(key)
            self._views[key] = view
            if index < len(self._slice_filters):
                view.add(f"slice{key[-1]}", self._slice_filters[index])
                view.view2D(index)
            else:
                item = view.add("grid", self._filter_threshold)
                item.get("actor").GetProperty().SetEdgeVisibility(1)
            index += 1
            view.resetCamera()

        # Expend shared state in app
        app.state.update(self.state)

    @property
    def state(self):
        bounds = self._grid.GetBounds()
        resolutions = self.resolutions
        return {
            "vtkCutOrigin": tuple(self._slice_planes[0].GetOrigin()),
            "vtkView3D": self._app.scene(self._views["vtkView3D"].view),
            "vtkViewX": self._app.scene(self._views["vtkViewX"].view),
            "vtkViewY": self._app.scene(self._views["vtkViewY"].view),
            "vtkViewZ": self._app.scene(self._views["vtkViewZ"].view),
            "vtkBounds": self._grid.GetBounds(),
            "sliderX": slider(bounds[0], bounds[1], resolutions[0]),
            "sliderY": slider(bounds[2], bounds[3], resolutions[1]),
            "sliderZ": slider(bounds[4], bounds[5], resolutions[2]),
            "interaction2D": [
                {
                    "button": 1,
                    "action": "Pan",
                },
                {
                    "button": 2,
                    "action": "Zoom",
                },
                {
                    "button": 3,
                    "action": "Zoom",
                    "scrollEnabled": True,
                },
                {
                    "button": 1,
                    "action": "ZoomToMouse",
                    "shift": True,
                },
                {
                    "button": 1,
                    "action": "ZoomToMouse",
                    "alt": True,
                },
            ],
        }

    def dirty(self, *args):
        state = self.state
        for name in args:
            if name in state:
                self._app.set(name, state[name], force=True)
            else:
                print(f"Unable to dirty missing key {name}")

    def update_views(self):
        for key in self._views:
            self._app.set(key, self._app.scene(self._views[key].view))

    @property
    def resolutions(self):
        dims = self._grid.GetDimensions()
        return (dims[0] - 1, dims[1] - 1, dims[2] - 1)

    def update_slice_origin(self, origin, dirty=True):
        for plane in self._slice_planes:
            plane.SetOrigin(origin)

        if dirty:
            self.update_views()

    def update_grid(self, extent, resolution, dirty=True):
        self._grid.SetDimensions(
            resolution[0] + 1, resolution[1] + 1, resolution[2] + 1
        )
        self._grid.SetSpacing(
            (extent[1] - extent[0]) / (resolution[0] - 1),
            (extent[3] - extent[2]) / (resolution[1] - 1),
            (extent[5] - extent[4]) / (resolution[2] - 1),
        )
        self._grid.SetOrigin(
            extent[0],
            extent[2],
            extent[4],
        )
        self._litho_field.SetNumberOfTuples(self._grid.GetNumberOfCells())
        self._litho_field.Fill(0)
        self._blank_field.SetNumberOfTuples(self._grid.GetNumberOfCells())
        self._blank_field.Fill(0)

        # Update sliders
        bounds = self._grid.GetBounds()
        self.update_slice_origin(
            [
                (bounds[0] + bounds[1]) * 0.5,
                (bounds[2] + bounds[3]) * 0.5,
                (bounds[4] + bounds[5]) * 0.5,
            ],
            dirty=dirty,
        )

        if dirty:
            self.dirty("sliderX", "sliderY", "sliderZ")

    def compute(self):
        # Update VTK mesh
        self._blank_field.Fill(0)
        self._litho_field.Fill(0)

        # Get gempy data
        litho = self._modeler.litho
        blanking = self._modeler.blanking

        if litho:
            i_max, j_max, k_max = self.resolutions
            if blanking:
                index = 0
                for k in range(k_max):
                    for j in range(j_max):
                        for i in range(i_max):
                            self._litho_field.SetTuple1(index, litho[i, j, k])
                            if blanking[i, j, k]:
                                self._blank_field.SetTuple1(index, 1)
                            index += 1
            else:
                index = 0
                for k in range(k_max):
                    for j in range(j_max):
                        for i in range(i_max):
                            self._litho_field.SetTuple1(index, litho[i, j, k])
                            index += 1

        self._litho_field.Modified()
        self._blank_field.Modified()
        self._filter_threshold.Update()
        self.field_ready = True

        self.update_views()

    def update_from_modeler(self):
        grid_data = self._modeler.state.get("grid")
        self.update_grid(**grid_data)
        self.compute()
