from vtkmodules.vtkCommonCore import (
    vtkFloatArray, 
    vtkLookupTable, 
    vtkPoints,
)
from vtkmodules.vtkCommonDataModel import (
    vtkCellArray,
    vtkImageData, 
    vtkPlane,
    vtkPolyData,
    vtkTriangle,
)
from vtkmodules.vtkFiltersCore import (
    vtkCutter, 
    vtkThreshold,
)
from vtkmodules.vtkFiltersCore import (
    vtkGlyph3D,
)
from vtkmodules.vtkFiltersModeling import (
    vtkOutlineFilter,
)
from vtkmodules.vtkFiltersSources import (
    vtkArrowSource,
    vtkSphereSource,
)
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkDataSetMapper,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
)
from vtkmodules.vtkRenderingAnnotation import (
    vtkCubeAxesActor,
)

def hextorgb(hcolor):
    h = hcolor.lstrip('#')
    rstring = h[0:2]
    r = int(rstring, 16)
    gstring = h[2:4]
    g = int(gstring, 16)
    bstring = h[4:6]
    b = int(bstring, 16)
    return [r/255.0, g/255.0, b/255.0]

def vector_magnitude(vector):
    sum = 0
    for i in range(len(vector)):
        sum = vector[i]*vector[i] + sum    
    return pow(sum,0.5)

def slider(min, max, resolution):
    return {
        "min": min,
        "max": max,
        "step": (max - min) / (resolution - 1),
    }


class ViewView:
    def __init__(self, name="default", app=None):
        self.name = name
        self._app = app
        self.renderer = vtkRenderer()
        self.renderWindow = vtkRenderWindow()
        self.renderWindow.AddRenderer(self.renderer)
        self.axes = vtkCubeAxesActor()
        self._scene = {}

        self.renderer.SetBackground(0.2, 0.4, 0.6)
        self.camera.SetViewUp(0.0, 0.0, 1.0)
        self.camera.SetPosition(50.0, 50.0 - 1.0, 50.0)
        self.camera.SetFocalPoint(50.0, 50.0, 50.0)
        

    def resetCamera(self):
        self.renderer.ResetCamera()
        self._app.update(ref=self.name, method="resetCamera", args=[])

    def updateCamera(self, center):
        self.camera.SetPosition(center[0], center[1] - 1.0, center[2])
        self.camera.SetFocalPoint(center[0], center[1], center[2])
        self.resetCamera()

    @property
    def camera(self):
        return self.renderer.GetActiveCamera()

    def add(self, name, source):
        if name in self._scene:
            print(f"Trying to add name({name}) twice in {self.name}")
            return None

        actor = vtkActor()
        mapper = vtkDataSetMapper()
        lut = vtkLookupTable()
        lut.SetTableRange(0.0, 1.0)
        lut.SetNumberOfTableValues(2)
        lut.SetNumberOfColors(2)
        lut.Build()
        lut.SetTableValue(0, 1.0, 1.0, 1.0, 1.0)
        lut.SetTableValue(1, 0.0, 0.0, 0.0, 1.0)
        if source.IsA("vtkDataSet"):
            mapper.SetInputData(source)
        else:
            mapper.SetInputConnection(source.GetOutputPort())
        mapper.SetLookupTable(lut)
        mapper.SetScalarRange(0.0, 1.0)
        mapper.SetScalarModeToUseCellData()
        mapper.SetColorModeToMapScalars()
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

    def add_surface_points(self, surface, color, radius, point_list):
        points = vtkPoints()
        vertices = vtkCellArray()
        for p in point_list:
            point_id = points.InsertNextPoint(p)
            vertices.InsertNextCell(1)
            vertices.InsertCellPoint(point_id)
        points_polydata = vtkPolyData()
        points_polydata.SetPoints(points)
        points_polydata.SetVerts(vertices)
        points_polydata.Modified()

        sphereSource = vtkSphereSource()
        sphereSource.SetRadius(radius)
        sphereSource.Update()

        glyph3D = vtkGlyph3D()
        glyph3D.SetSourceConnection(sphereSource.GetOutputPort())
        glyph3D.SetInputData(points_polydata)
        glyph3D.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(glyph3D.GetOutputPort())
        mapper.Update()

        actor = vtkActor()
        actor.SetMapper(mapper)
        rgbcolor = hextorgb(color)
        actor.GetProperty().SetColor(rgbcolor[0],rgbcolor[1],rgbcolor[2])

        self.renderer.AddActor(actor)

        name = surface+"_points"
        item = {
            "name": name,
            "source": glyph3D,
            "mapper": mapper,
            "actor": actor,
        }
        self._scene[name] = item
        return item

    def add_surface_orientations(self, surface, color, radius, orientation_list):
        points = vtkPoints()
        vertices = vtkCellArray()
        direction = vtkFloatArray()
        direction.SetName('direction')
        direction.SetNumberOfComponents(3)
        direction.SetNumberOfTuples(len(orientation_list))
        magnitude = vtkFloatArray()
        magnitude.SetName('magnitude')
        magnitude.SetNumberOfTuples(len(orientation_list))
        index = 0
        for o in orientation_list:
            p = [o[0], o[1], o[2]]
            d = [o[3], o[4], o[5]]
            point_id = points.InsertNextPoint(p)
            vertices.InsertNextCell(1)
            vertices.InsertCellPoint(point_id)
            direction.SetTuple(index, d)
            m = vector_magnitude(d)
            magnitude.SetTuple1(index, m)
            index += 1

        points_polydata = vtkPolyData()
        points_polydata.SetPoints(points)
        points_polydata.SetVerts(vertices)
        points_polydata.GetPointData().AddArray(direction)
        points_polydata.GetPointData().SetActiveVectors('direction')
        points_polydata.GetPointData().AddArray(magnitude)
        points_polydata.GetPointData().SetActiveScalars('magnitude')
        points_polydata.Modified()

        arrowSource = vtkArrowSource()
        arrowSource.SetTipRadius(0.5)
        arrowSource.SetShaftRadius(0.25)
        arrowSource.Update()

        glyph3D = vtkGlyph3D()
        glyph3D.SetSourceConnection(arrowSource.GetOutputPort())
        glyph3D.SetInputData(points_polydata)
        glyph3D.SetVectorModeToUseVector()
        glyph3D.SetScaleFactor(radius)
        glyph3D.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(glyph3D.GetOutputPort())
        mapper.Update()

        actor = vtkActor()
        actor.SetMapper(mapper)
        rgbcolor = hextorgb(color)
        actor.GetProperty().SetColor(rgbcolor[0],rgbcolor[1],rgbcolor[2])
        self.renderer.AddActor(actor)

        name = surface+"_orientations"
        item = {
            "name": name,
            "source": glyph3D,
            "mapper": mapper,
            "actor": actor,
        }
        self._scene[name] = item
        return item

    def add_surface(self, surface, color, vertices, simplices):
        surface_points = vtkPoints()
        surface_polydata = vtkPolyData()
        surface_triangles = vtkCellArray()
        for v in vertices:
            surface_points.InsertNextPoint(v)
        for s in simplices:
            triangle = vtkTriangle()
            triangle.GetPointIds().SetId(0, s[0])
            triangle.GetPointIds().SetId(1, s[1])
            triangle.GetPointIds().SetId(2, s[2])
            surface_triangles.InsertNextCell(triangle)

        surface_polydata.SetPoints(surface_points)
        surface_polydata.SetPolys(surface_triangles)
        surface_polydata.Modified()

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(surface_polydata)
        mapper.Update()

        actor = vtkActor()
        actor.SetMapper(mapper)
        rgbcolor = hextorgb(color)
        actor.GetProperty().SetColor(rgbcolor[0],rgbcolor[1],rgbcolor[2])

        self.renderer.AddActor(actor)
        
        name = surface+"_surface"
        item = {
            "name": name,
            "source": surface_polydata,
            "mapper": mapper,
            "actor": actor,
        }
        self._scene[name] = item
        return item

    def update_cube_axes(self, source):
        bounds = source.GetBounds()
        self.axes.SetBounds( bounds[0], bounds[1], bounds[2], bounds[3], bounds[4], bounds[5])

    def add_cube_axes(self, source):
        bounds = source.GetBounds()
        self.axes.SetBounds( bounds[0], bounds[1], bounds[2], bounds[3], bounds[4], bounds[5])
        self.axes.SetCamera(self.renderer.GetActiveCamera())
        self.axes.SetXLabelFormat("%6.1f")
        self.axes.SetYLabelFormat("%6.1f")
        self.axes.SetZLabelFormat("%6.1f")
        self.axes.SetFlyModeToOuterEdges()
        self.renderer.AddActor(self.axes)

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
        self._current_actors = []

        # VTK
        # ref: https://github.com/cgre-aachen/gempy/blob/master/gempy/plot/visualization_3d.py
        self._grid = vtkImageData()
        self._litho_field = vtkFloatArray()
        self._litho_field.SetName("litho")
        self._grid.GetCellData().SetScalars(self._litho_field)
        self._filter_threshold = vtkThreshold()
        self._filter_threshold.SetInputData(self._grid)
        self._filter_threshold.ThresholdByUpper(0.0)
        #  Outline
        self._filter_outline = vtkOutlineFilter()
        self._filter_outline.SetInputData(self._grid)

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
        self._views = {}
        self.update_grid(dirty=False)
        index = 0
        for key in ["vtkViewX", "vtkViewY", "vtkViewZ", "vtkView3D"]:
            view = ViewView(key, self._app)
            self._views[key] = view
            if index < len(self._slice_filters):
                view.add(f"slice{key[-1]}", self._slice_filters[index])
                view.view2D(index)
            else:
                item = view.add("outline", self._filter_outline)
                item = view.add("grid", self._filter_threshold)
                item.get("actor").GetProperty().SetEdgeVisibility(1)
                self.set_visibility("grid", False)
                view.add_cube_axes(self._grid)
            index += 1
            view.resetCamera()

        # Expend shared state in app
        app.state.update(self.state)

    @property
    def state(self):
        bounds = self._grid.GetBounds()
        resolutions = self.resolutions
        return {
            "visibility": [],
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

    def get_ordered_surfaces(self):
        ordered_surfaces = []
        mapstacks = self._modeler._state_handler.map_stack_to_surfaces()
        for stack in mapstacks.keys():
            ordered_surfaces.extend(mapstacks[stack])
        ordered_surfaces.reverse()
        return ordered_surfaces

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

    def resetCamera(self):
        for key in self._views:
            self._views[key].resetCamera()
    
    def set_visibility(self, name, on_off):
        item = self._views["vtkView3D"].get(name)
        item.get("actor").SetVisibility(on_off)

    def toggle_visibility(self, name):
        item = self._views["vtkView3D"].get(name)
        item.get("actor").SetVisibility(not item.get("actor").GetVisibility())

    def update_slice_origin(self, origin, dirty=True):
        for plane in self._slice_planes:
            plane.SetOrigin(origin)

        # if dirty:
        #     self.update_views()

    def update_from_modeler(self):
        self.update_grid()
        self.compute()

    def update_grid(self, dirty=True):
        grid = self._modeler._state_handler.grid
        resolution = grid.resolution
        extent = grid.extent
        self._grid.SetDimensions(
            resolution[0] + 1, resolution[1] + 1, resolution[2] + 1
        )
        self._grid.SetSpacing(
            (extent[1] - extent[0]) / (resolution[0]),
            (extent[3] - extent[2]) / (resolution[1]),
            (extent[5] - extent[4]) / (resolution[2]),
        )
        self._grid.SetOrigin(
            extent[0],
            extent[2],
            extent[4],
        )
        self._litho_field.SetNumberOfTuples(self._grid.GetNumberOfCells())
        self._litho_field.Fill(0)

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
        for name in self._current_actors:
            self._views["vtkView3D"].remove(name)

        self.update_surface()
        self.update_surface_points()
        self.update_surface_orientations()

        self.update_lithography()
        self.update_cube_axes()
        self.update_views()

    def update_lithography(self):
        litho = self._modeler._geo_model.solutions.lith_block
        blank = self._modeler._geo_model._grid.regular_grid.mask_topo
        i_max, j_max, k_max = self.resolutions
        if litho.size == i_max * j_max * k_max:
            self._litho_field.Fill(0)
            lithography = litho.reshape(i_max, j_max, k_max)
            if blank.size == i_max * j_max * k_max:
                blanking = blank.reshape(i_max, j_max, k_max)
                index = 0
                for k in range(k_max):
                    for j in range(j_max):
                        for i in range(i_max):
                            if blanking[i, j, k]:
                                self._litho_field.SetTuple1(index, -1)
                            else:
                                self._litho_field.SetTuple1(index, lithography[i, j, k])
                            index += 1
            else:
                index = 0
                for k in range(k_max):
                    for j in range(j_max):
                        for i in range(i_max):
                            self._litho_field.SetTuple1(index, lithography[i, j, k])
                            index += 1
            self.update_lut()
            self._litho_field.Modified()
            self._filter_threshold.Update()
            self.field_ready = True
        else:
            print("No Change")

    def update_lut(self):
        item = self._views["vtkView3D"].get("grid")
        colors = self._modeler._geo_model.surfaces.colors.colordict
        surfaces = self.get_ordered_surfaces()
        scalarMin = 0.0
        scalarMax = len(surfaces)
        lut = vtkLookupTable()
        lut.SetTableRange(scalarMin, scalarMax)
        lut.SetNumberOfTableValues(len(surfaces) + 1)
        lut.SetNumberOfColors(len(surfaces) + 1)
        lut.Build()
        lut.SetTableValue(0, 1.0, 1.0, 1.0, 1.0)
        for i in range(1,len(surfaces) + 1):
            rgbcolor = hextorgb(colors[surfaces[i-1]])
            lut.SetTableValue(i, rgbcolor[0], rgbcolor[1], rgbcolor[2], 1.0)
        item["mapper"].SetScalarRange(scalarMin, scalarMax)
        item["mapper"].SetLookupTable(lut)
        item["mapper"].SetScalarModeToUseCellData()
        item["mapper"].SetColorModeToMapScalars()
        item["mapper"].ScalarVisibilityOn()
        item["mapper"].Update()

    def update_cube_axes(self):
        self._views["vtkView3D"].update_cube_axes(self._grid)

    def update_surface_points(self):
        view = self._views["vtkView3D"]
        spacing = self._grid.GetSpacing()
        radius = min(spacing)
        surfaces = self.get_ordered_surfaces()
        # remove basement from list
        surfaces.remove('Surface_1')
        colors = self._modeler._geo_model.surfaces.colors.colordict
        for surface in surfaces:
            color = colors[surface]
            surface_filter = self._modeler._geo_model._surface_points.df.surface == surface
            points = self._modeler._geo_model._surface_points.df[surface_filter][["X", "Y", "Z"]].values
            name = surface+"_points"
            self._current_actors.append(name)
            view.add_surface_points(surface, color, radius, points)
            self.set_visibility(name, False)

    def update_surface_orientations(self):
        view = self._views["vtkView3D"]
        spacing = self._grid.GetSpacing()
        radius = min(spacing)
        surfaces = self.get_ordered_surfaces()
        # remove basement from list
        surfaces.remove('Surface_1')
        colors = self._modeler._geo_model.surfaces.colors.colordict
        for surface in surfaces:
            color = colors[surface]
            surface_filter = self._modeler._geo_model._orientations.df.surface == surface
            orientations = self._modeler._geo_model._orientations.df[surface_filter][["X", "Y", "Z", "G_x", "G_y", "G_z"]].values
            name = surface+"_orientations"
            self._current_actors.append(name)
            view.add_surface_orientations(surface, color, radius, orientations)
            self.set_visibility(name, False)

    def update_surface(self):
        view = self._views["vtkView3D"]
        surfaces = self.get_ordered_surfaces()
        # remove basement from list
        surfaces.remove('Surface_1')
        colors = self._modeler._geo_model.surfaces.colors.colordict
        for surface in surfaces:
            color = colors[surface]
            surface_filter = self._modeler._geo_model._surfaces.df.surface == surface
            test = self._modeler._geo_model._surfaces.df[surface_filter]
            vertices = test.vertices.values.tolist()[0]
            simplices = test.edges.values.tolist()[0]
            name = surface+"_surface"
            self._current_actors.append(name)
            view.add_surface(surface, color, vertices, simplices)
            self.set_visibility(name, False)

    def update_visibility(self, visibility):
        surfaces = self.get_ordered_surfaces()
        # remove basement from list
        surfaces.remove('Surface_1')
        self.set_visibility("grid", False)
        for surface in surfaces:
            name = surface+"_surface"
            self.set_visibility(name, False)
            name = surface+"_points"
            self.set_visibility(name, False)
            name = surface+"_orientations"
            self.set_visibility(name, False)
        for item in visibility:
            self.set_visibility(item, True)
        self.update_views()
