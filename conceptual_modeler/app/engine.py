r"""
Define your classes and create the instances that you need to expose
"""
import logging
import time

from . import pipeline_manager as pm
from . import matplotlib_manager as mm

from .modeler.subsurface import SubSurface
from .modeler.visualization import VtkViewer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_NEW_STACK = {"name": "", "feature": "Erosion"}
DEFAULT_NEW_SURFACE = {"name": "", "stackid": ""}
DEFAULT_NEW_POINT = {"x": "", "y": "", "z": "", "surfaceid": ""}
DEFAULT_NEW_ORIENTATION = {
    "x": "",
    "y": "",
    "z": "",
    "gx": "",
    "gy": "",
    "gz": "",
    "surfaceid": "",
}

DEFAULT_NEW = {
    "Stack": DEFAULT_NEW_STACK,
    "Surface": DEFAULT_NEW_SURFACE,
    "Point": DEFAULT_NEW_POINT,
    "Orientation": DEFAULT_NEW_ORIENTATION,
}

TOPOGRAPHY_ITEMS = ["random", "gdal", "saved"]
TOPOGRAPHY_CATEGORY = {"random": 0, "gdal": 1, "saved": 2}

# ---------------------------------------------------------
# Engine class
# ---------------------------------------------------------

class MyBusinessLogic:
    def __init__(self, server):
        self._server = server

        # initialize state + controller
        state, ctrl = server.state, server.controller

        state.update(
            {
                "active_pipeline_card": None,
                "importType": None,
                "importFile": None,
                "topography_file": None,
                "import_model_file": None,
                "run": False,
                "run_button": False,
                "stackNew": DEFAULT_NEW_STACK,
                "surfaceNew": DEFAULT_NEW_SURFACE,
                "pointNew": DEFAULT_NEW_POINT,
                "orientationNew": DEFAULT_NEW_ORIENTATION,
                "topography_items": TOPOGRAPHY_ITEMS,
                "VIEW_3D": False,
                "VIEW_FIGX": False,
                "VIEW_FIGY": False,
                "VIEW_FIGZ": False,
            }
        )

        self._x_fig = mm.MatplotlibManager(state, "x_figure_size")
        self._y_fig = mm.MatplotlibManager(state, "y_figure_size")
        self._z_fig = mm.MatplotlibManager(state, "z_figure_size")

        self._pipeline_manager = pm.PipelineManager(state, "pipeline_tree")
        self._subsurface = SubSurface(self)
        self._viz = VtkViewer(self, self._subsurface)

        ctrl.on_pipeline_action = self.on_pipeline_action
        ctrl.pipeline_actives_change = self.pipeline_actives_change
        ctrl.pipeline_visibility_change = self.pipeline_visibility_change
        ctrl.reset_grid = self.reset_grid
        ctrl.ss_select = self.ss_select
        ctrl.ss_move = self.ss_move
        ctrl.ss_new = self.ss_new
        ctrl.ss_new_with_id = self.ss_new_with_id
        ctrl.ss_remove = self.ss_remove
        ctrl.theme_mode = self.theme_mode

        ctrl.compute_geo_model = self._subsurface.compute_geo_model
        ctrl.import_data = self._subsurface.import_data
        ctrl.parse_zip_file = self._subsurface.parse_zip_file
        ctrl.subsurface_update_grid = self._subsurface.update_grid
        ctrl.subsurface_update_topography = self._subsurface.update_topography
        ctrl.update_topography_file = self._subsurface.update_topography_file

        ctrl.compute = self._viz.compute
        ctrl.getRenderWindow = self._viz.getRenderWindow
        ctrl.set_cube_axes_visibility = self._viz.set_cube_axes_visibility
        ctrl.set_opacity = self._viz.set_opacity
        ctrl.set_representation = self._viz.set_representation
        ctrl.xfig_size = self._x_fig.size
        ctrl.update_xfig = self._viz.update_xfig
        ctrl.yfig_size = self._y_fig.size
        ctrl.update_yfig = self._viz.update_yfig
        ctrl.zfig_size = self._z_fig.size
        ctrl.update_zfig = self._viz.update_zfig
        ctrl.viz_update_grid = self._viz.update_grid
        ctrl.viz_update_topography = self._viz.update_topography

    def push_state(self, key, value):
        state = self._server.state

        if key == "pipelines":
            self._pipeline_manager.add_nodes(value)
        if key == "topography":
            state.topography_category = TOPOGRAPHY_CATEGORY[value["category"]]
        state[key] = value

    def theme_mode(self, event):
        print(">>> ENGINE: Theme mode...")
        self._subsurface.set_theme_mode(event)
        self.update_viewX()
        self.update_viewY()
        self.update_viewZ()
    
    def update_viewX(self):
        print(">>> ENGINE: Update view x...")
        state, ctrl = self._server.state, self._server.controller
        if (state.VIEW_FIGX):
            ctrl.view_x_update(
                figure=ctrl.update_xfig(**ctrl.xfig_size(), cell_number=[state.slice_x])
            )

    def update_viewY(self):
        print(">>> ENGINE: Update view y...")
        state, ctrl = self._server.state, self._server.controller
        if (state.VIEW_FIGY):
            ctrl.view_y_update(
                figure=ctrl.update_yfig(**ctrl.yfig_size(), cell_number=[state.slice_y])
            )

    def update_viewZ(self):
        print(">>> ENGINE: Update view z...")
        state, ctrl = self._server.state, self._server.controller
        if (state.VIEW_FIGZ):
            ctrl.view_z_update(
                figure=ctrl.update_zfig(**ctrl.zfig_size(), cell_number=[state.slice_z])
            )
  
    def get_pipeline(self, id):
        print(">>> ENGINE: Get pipeline...")
        state = self._server.state

        _pipelines = state.pipelines
        for item in _pipelines:
            if item["id"] == id:
                return item["pipeline"]
        return 0

    def on_pipeline_action(self, event):
        print(">>> ENGINE: On pipeline action...")
        _id = event.get("id")
        _action = event.get("action")
        if _action.startswith("collap"):
            _collapsed = True
            self._pipeline_manager.toggle_collapsed(_id)

    def pipeline_actives_change(self, ids):
        print(">>> ENGINE: Pipeline actives change...")
        state = self._server.state

        _id = ids[0]
        prv_ids = state.active_ids
        _pipeline = self.get_pipeline(_id)
        if prv_ids == ids:
            state.active_ids = []
            state.active_pipeline_card = None
        else:
            if _pipeline != 0:
                state.active_pipeline_card = _pipeline
                representation = self._viz.get_representation(_pipeline)
                opacity = self._viz.get_opacity(_pipeline)
                state.current_representation = representation
                state.current_opacity = opacity
            else:
                state.active_pipeline_card = None
            state.active_ids = ids

    def pipeline_visibility_change(self, event):
        print(">>> ENGINE: Pipeline visibility change...")
        state, ctrl = self._server.state, self._server.controller

        _id = event["id"]
        _pipeline = self.get_pipeline(_id)
        _visibility = event["visible"]
        dirty = self._viz.set_visibility(_pipeline, _visibility)
        if dirty:
            self._pipeline_manager.set_visible(_id, _visibility)
            if (state.VIEW_3D):
                ctrl.view_3D_update()

    def reset_grid(self):
        print(">>> ENGINE: Reset grid...")
        self._subsurface.dirty("grid")
    
    def reset_topography(self):
        print(">>> ENGINE: Reset topography...")
        self._subsurface.dirty("topography")

    def ss_select(self, type, id):
        print(">>> ENGINE: SS select...")
        self._subsurface.select(type, id)


    def ss_move(self, type, direction):
        print(">>> ENGINE: SS move...")
        self._subsurface.move(type, direction)


    def ss_new(self, type, data):
        state = self._server.state

        print(">>> ENGINE: SS new...")
        self._subsurface.add(type, data)
        state[f"{type.lower()}New"] = DEFAULT_NEW[type]

    def ss_new_with_id(self, type, data, idname, id):
        state = self._server.state

        print(">>> ENGINE: SS new with id...")
        data[idname] = id
        self._subsurface.add(type, data)
        state[f"{type.lower()}New"] = DEFAULT_NEW[type]

    def ss_remove(self, type, id):
        print(">>> ENGINE: SS remove...")
        self._subsurface.remove(type, id)

# ---------------------------------------------------------
# Server binding
# ---------------------------------------------------------

def initialize(server):
    state, ctrl = server.state, server.controller

    @state.change("run")
    def compute(run, **kwargs):
        print(">>> ENGINE: Computing...")
        if run:
            ctrl.compute_geo_model()
            ctrl.compute(computing=True)
            state.run = False
            print("compute", ctrl.view_3D_update)
            if (state.VIEW_3D):
                ctrl.view_3D_update()
            update_viewX()
            update_viewY()
            update_viewZ()

    @state.change("import_model_file")
    def import_model(import_model_file, **kwargs):
        print(">>> ENGINE: Importing model...")
        if import_model_file:
            ctrl.parse_zip_file(import_model_file)
            state.import_state = False
            state.import_model_file = None

    @state.change("importFile")
    def import_file(importType, importFile, **kwargs):
        if importFile:
            ctrl.import_data(importType, importFile)
        state.importFile = None

    @state.change("export_state")
    def export_state(**kwargs):
        print(">>> ENGINE: Exporting model...")
        if export_state:
            # TODO: Export state
            state.export_state = False

    @state.change("cube_axes_visibility")
    def update_cube_axes_visibility(cube_axes_visibility, **kwargs):
        print(">>> ENGINE: Updating cube axes visibility...")
        ctrl.set_cube_axes_visibility(cube_axes_visibility)
        if (state.VIEW_3D):
            ctrl.view_3D_update()

    @state.change("current_representation")
    def update_representation(active_pipeline_card, current_representation, **kwargs):
        print(">>> ENGINE: Update representation...")
        print("representation entry ", time.time())
        dirty = ctrl.set_representation(active_pipeline_card, current_representation)
        print("representation exit ", time.time())
        if dirty:
            if (state.VIEW_3D):
                ctrl.view_3D_update()
        print("representation update geometry ", time.time())


    @state.change("current_opacity")
    def update_opacity(active_pipeline_card, current_opacity, **kwargs):
        print(">>> ENGINE: Update opacity...")
        print("opacity entry ", time.time())
        dirty = ctrl.set_opacity(active_pipeline_card, current_opacity)
        print("opacity exit ", time.time())
        if dirty:
            if (state.VIEW_3D):
                ctrl.view_3D_update()
        print("opacity update geometry ", time.time())

    @state.change("grid")
    def update_grid(grid, **kwargs):
        print(">>> ENGINE: Update grid...")
        extent = [float(x) for x in grid.get("extent")]
        resolution = [int(x) for x in grid.get("resolution")]
        slider_x_max = resolution[0] - 1
        state.slider_x_max = slider_x_max
        slider_y_max = resolution[1] - 1
        state.slider_y_max = slider_y_max
        slider_z_max = resolution[2] - 1
        state.slider_z_max = slider_z_max
        dirty_subsurface = ctrl.subsurface_update_grid(extent, resolution)
        dirty_viz = ctrl.viz_update_grid()
        if dirty_viz:
            ctrl.compute(computing=False)
            if (state.VIEW_3D):
                ctrl.view_3D_update()

    @state.change("topography")
    def update_topography(topography, **kwargs):
        print(">>> ENGINE: Update topography...")
        if topography["on"] == True:
            ctrl.subsurface_update_topography(topography)
            ctrl.viz_update_topography()

    @state.change("topography_file")
    def update_topography_file(topography_file, topography, **kwargs):
        print(">>> ENGINE: Update topography file...")
        if topography_file:
            ctrl.update_topography_file(topography["category"], topography_file)
            ctrl.viz_update_topography()
        state.topography_file = None

    @state.change("slice_x")
    def update_slice_x(slice_x, **kwargs):
        print(">>> ENGINE: Update slice x...")
        if (state.VIEW_FIGX):
            ctrl.view_x_update(
                figure=ctrl.update_xfig(**ctrl.xfig_size(), cell_number=[slice_x])
            )

    @state.change("x_figure_size")
    def update_viewX(**kwargs):
        print(">>> ENGINE: Update view x...")
        if (state.VIEW_FIGX):
            ctrl.view_x_update(
                figure=ctrl.update_xfig(**ctrl.xfig_size(), cell_number=[state.slice_x])
            )

    @state.change("slice_y")
    def update_slice_y(slice_y, **kwargs):
        print(">>> ENGINE: Update slice y...")
        if (state.VIEW_FIGY):
            ctrl.view_y_update(
                figure=ctrl.update_yfig(**ctrl.yfig_size(), cell_number=[slice_y])
            )

    @state.change("y_figure_size")
    def update_viewY(**kwargs):
        print(">>> ENGINE: Update view y...")
        if (state.VIEW_FIGY):
            ctrl.view_y_update(
                figure=ctrl.update_yfig(**ctrl.yfig_size(), cell_number=[state.slice_y])
            )

    @state.change("slice_z")
    def update_slice_z(slice_z, **kwargs):
        print(">>> ENGINE: Update slice z...")
        if (state.VIEW_FIGZ):
            ctrl.view_z_update(
                figure=ctrl.update_zfig(**ctrl.zfig_size(), cell_number=[slice_z])
            )

    @state.change("z_figure_size")
    def update_viewZ(**kwargs):
        print(">>> ENGINE: Update view z...")
        if (state.VIEW_FIGZ):
            ctrl.view_z_update(
                figure=ctrl.update_zfig(**ctrl.zfig_size(), cell_number=[state.slice_z])
            )

    def protocols_ready(**initial_state):
        #logger.info(f">>> ENGINE(b): Server is ready {initial_state}")
        logger.info(">>> ENGINE: Server is ready")

    ctrl.on_server_ready.add(protocols_ready)
    ctrl.on_server_ready.add(ctrl.view_3D_update)

    engine = MyBusinessLogic(server)
    return engine
