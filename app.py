import os
import time
from collections import defaultdict

from trame.app import get_server
from trame.assets.local import LocalFileManager, to_url
from trame.ui.vuetify import SinglePageWithDrawerLayout
from trame.widgets import html, vtk, vuetify, trame, matplotlib

import cm_assets

# Allow 1MB 1024*1024 messages
#os.environ["WSLINK_MAX_MSG_SIZE"] = "1048576"

from modeler.subsurface import SubSurface
from modeler.visualization import VtkViewer

DEFAULT_NEW_STACK = {"name": "", "feature": "Erosion"}
DEFAULT_NEW_SURFACE = {"name": "", "stackid": ""}
DEFAULT_NEW_POINT = {"x": "", "y": "", "z": "", "surfaceid": ""}
DEFAULT_NEW_ORIENTATION = {"x": "", "y": "", "z": "", "gx": "", "gy": "", "gz": "", "surfaceid": ""}

DEFAULT_NEW = {
    "Stack": DEFAULT_NEW_STACK,
    "Surface": DEFAULT_NEW_SURFACE,
    "Point": DEFAULT_NEW_POINT,
    "Orientation": DEFAULT_NEW_ORIENTATION,
}

TOPOGRAPHY_ITEMS = ['random', 'gdal', 'saved']
TOPOGRAPHY_CATEGORY = {'random': 0, 'gdal': 1, 'saved': 2}

# -----------------------------------------------------------------------------
# Server setup
# -----------------------------------------------------------------------------

server = get_server()
state, ctrl = server.state, server.controller

state.trame__title = "Conceptual Modeler"
state.trame__favicon = "__global/assets/logo.svg"

server.enable_module(cm_assets)

# -----------------------------------------------------------------------------

class MatplotlibStateHandler:
    def __init__(self, name):
        self._name = name
        self._dpi = 192
        self._w_inch = 1
        self._h_inch = 1
        state[self._name] = {}

    @property
    def size(self):
        if state[self._name] is not None:
            pixel_ratio = state[self._name].get("pixelRatio")
            dpi = state[self._name].get("dpi")
            rect = state[self._name].get("size")
            w_inch = (rect.get("width") - 30) / (dpi / pixel_ratio)
            h_inch = (rect.get("height") - 30) / (dpi / pixel_ratio)
            if w_inch > 0 and h_inch > 0:
                self._dpi = dpi
                self._w_inch = w_inch
                self._h_inch = h_inch
        return {
            "figsize": (self._w_inch, self._h_inch),
            "dpi": self._dpi,
        }

x_fig_state = MatplotlibStateHandler("x_figure_size")
y_fig_state = MatplotlibStateHandler("y_figure_size")
z_fig_state = MatplotlibStateHandler("z_figure_size")

# -----------------------------------------------------------------------------
# Server setup
# -----------------------------------------------------------------------------

class Application:
    def __init__(self):
        self.pipeline_manager = PipelineManager(state, "pipeline_tree")
        self.subsurface = SubSurface(self)
        self.viz = VtkViewer(self, self.subsurface)

        self.html_view3D = vtk.VtkRemoteLocalView(self.viz.getRenderWindow("view3D"), trame_server=server, mode='local', namespace='view3D')
        self.html_viewX = matplotlib.Figure(trame_server=server, figure=self.viz.update_xfig(), style="position: absolute;left: 50%;top: 0px;transform: translateX(-50%);")
        self.html_viewY = matplotlib.Figure(trame_server=server, figure=self.viz.update_yfig(), style="position: absolute;left: 50%;top: 0px;transform: translateX(-50%);")
        self.html_viewZ = matplotlib.Figure(trame_server=server, figure=self.viz.update_zfig(), style="position: absolute;left: 50%;top: 0px;transform: translateX(-50%);")

        # add view update on ready
        ctrl.on_server_ready.add(self.html_view3D.update)

        self.layout = SinglePageWithDrawerLayout(server)
        self.layout.title.set_text("Conceptual Modeler")
        with self.layout.icon:
            html.Span(
                f'<img height="32px" width="32px" src="{state.trame__favicon}" />',
                classes="mr-2",
                style="display: flex; align-content: center;",
            )

    def push_state(self, key, value):
        if key == "pipelines":
            self.pipeline_manager.add_nodes(value)
        if key == "topography":
            state.topography_category = TOPOGRAPHY_CATEGORY[value["category"]]
        state[key] = value

# -----------------------------------------------------------------------------
# Pipeline setup
# -----------------------------------------------------------------------------

class PipelineManager:
    def __init__(self, state, name):
        self._state = state
        self._name = name
        self._next_id = 1
        self._nodes = {}
        self._children_map = defaultdict(set)

    def _update_hierarchy(self):
        self._children_map.clear()
        for node in self._nodes.values():
            self._children_map[node.get("parent")].add(node.get("id"))

        self.update()

    def _add_children(self, list_to_fill, node_id):
        for child_id in self._children_map[node_id]:
            node = self._nodes[child_id]
            list_to_fill.append(node)
            if node.get("collapsed"):
                continue
            self._add_children(list_to_fill, node.get("id"))

        return list_to_fill

    def update(self):
        result = self._add_children([], "0")
        new_result = sorted(result, key=lambda d: int(d['id']))
        self._state[self._name] = new_result
        return new_result

    def add_nodes(self, pipelines):
        for pipeline in pipelines:
            _id = pipeline["id"]
            node = {
                **pipeline,
            }
            self._nodes[_id] = node
        self._update_hierarchy()

    def remove_node(self, _id):
        for id in self._children_map[_id]:
            self.remove_node(_id)
        self._nodes.pop(_id)
        self._update_hierarchy()

    def get_collapsed(self, id, pipeline):
        node = self.get_node(id)
        if node and node["pipeline"] == pipeline:
            return node["collapsed"]
        return True

    def toggle_collapsed(self, _id, icons=["collapsed", "collapsable"]):
        node = self.get_node(_id)
        node["collapsed"] = not node["collapsed"]

        # Toggle matching action icon
        actions = node.get("actions", [])
        for i in range(len(actions)):
            action = actions[i]
            if action in icons:
                actions[i] = icons[(icons.index(action) + 1) % 2]

        self.update()
        return node["collapsed"]

    def toggle_visible(self, _id):
        node = self.get_node(_id)
        node["visible"] = not node["visible"]
        self.update()
        return node["visible"]

    def get_visible(self, id, pipeline):
        node = self.get_node(id)
        if node and node["pipeline"] == pipeline:
            return node["visible"]
        return False

    def set_visible(self, _id, visible):
        node = self.get_node(_id)
        node["visible"] = visible
        self.update()

    def get_node(self, _id):
        return self._nodes.get(f"{_id}")

# -----------------------------------------------------------------------------
# Callbacks
# -------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# UI Toolbar & Callbacks
# -----------------------------------------------------------------------------

def create_toolbar(toolbar):
    with toolbar:
        vuetify.VSpacer()
        workflow_buttons()
        vuetify.VSpacer()
        run_button()
        import_button()
        export_button()
        vuetify.VDivider(vertical=True, classes="mx-2")
        view_buttons()
        vuetify.VDivider(vertical=True, classes="mx-2")
        standard_buttons()

def workflow_buttons():
    vuetify.VCheckbox(
        v_model=("stacks_workflow", False),
        color="success",
        on_icon="mdi-layers-triple",
        off_icon="mdi-layers-triple",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )
    vuetify.VCheckbox(
        v_model=("surfaces_workflow", False),
        color="success",
        on_icon="mdi-elevation-rise",
        off_icon="mdi-elevation-rise",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )
    vuetify.VCheckbox(
        v_model=("points_workflow", False),
        color="success",
        on_icon="mdi-chart-bubble",
        off_icon="mdi-chart-bubble",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )
    vuetify.VCheckbox(
        v_model=("orientations_workflow", False),
        color="success",
        on_icon="mdi-compass",
        off_icon="mdi-compass",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )

def view_buttons():
    with vuetify.VBtnToggle(
        v_model=("viewLayout","singleView"),
        classes="mx-1",
        dense=True,
        hide_details=True,
        required=True,
    ):
        with vuetify.VBtn(
            small=True,
            icon=True,
            value="singleView",
        ):
            vuetify.VIcon("mdi-border-all-variant")
        with vuetify.VBtn(
            small=True,
            icon=True,
            value="multiView",
        ):
            vuetify.VIcon("mdi-border-all")

def run_button():
    vuetify.VCheckbox(
        v_model=("run", False),
        color="success",
        on_icon="mdi-run",
        off_icon="mdi-run",
        classes="mx-1",
        hide_details=True,
        dense=True,
        disabled=("run_button", False)
    )

def import_button():
    vuetify.VCheckbox(
        click=f"document.getElementById('model_id').click();",
        v_model=("import_state", False),
        color="success",
        on_icon="mdi-arrow-up-bold-box-outline",
        off_icon="mdi-arrow-up-bold-box-outline",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )
    html.Input(
        id="model_id",
        type="file",
        style="display: none",
        __events=["change"],
        change="import_model_file=$event.target.files[0]",
    )

def export_button():
    vuetify.VCheckbox(
        v_model=("export_state", False),
        color="success",
        on_icon="mdi-arrow-down-bold-box-outline",
        off_icon="mdi-arrow-down-bold-box-outline",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )

@state.change("run")
def compute(run, **kwargs):
    if run:
        application.subsurface.compute_geo_model()
        application.viz.compute(computing=True)
        state.run = False
        application.html_view3D.update()
        update_viewX()
        update_viewY()
        update_viewZ()

@state.change("import_model_file")
def import_model(import_model_file, **kwargs):
    if import_model_file:
        application.subsurface.parse_zip_file(import_model_file)
        state.import_state = False
        state.import_model_file = None

@state.change("export_model_file")
def export_state(**kwargs):
    #TODO: Export state
    print("Export state")

def standard_buttons():
    vuetify.VCheckbox(
        v_model=("view3DMode", 'local'),
        false_value='remote',
        true_value='local',
        color="success",
        on_icon="mdi-lan-disconnect",
        off_icon="mdi-lan-connect",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )
    vuetify.VCheckbox(
        v_model=("cube_axes_visibility", True),
        color="success",
        on_icon="mdi-cube-outline",
        off_icon="mdi-cube-off-outline",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )
    with vuetify.VBtn(
            icon=True,
            click=application.html_view3D.reset_camera,
        ):
        vuetify.VIcon("mdi-focus-field")
    vuetify.VCheckbox(
        v_model="$vuetify.theme.dark",
        color="white",
        on_icon="mdi-lightbulb-off-outline",
        off_icon="mdi-lightbulb-outline",
        classes="mx-1",
        hide_details=True,
        dense=True,
        change=(theme_mode, "[$event]"),
    )

@state.change("cube_axes_visibility")
def update_cube_axes_visibility(cube_axes_visibility, **kwargs):
    dirty = application.viz.set_cube_axes_visibility(cube_axes_visibility)
    if dirty:
        application.html_view3D.update()

def theme_mode(event):
    application.subsurface.set_theme_mode(event)
    update_viewX()
    update_viewY()
    update_viewZ()

# -----------------------------------------------------------------------------
# UI Drawer
# -----------------------------------------------------------------------------

def create_drawer(drawer):
    with drawer:
        drawer.width = 325
        pipeline_widget()
        vuetify.VDivider(classes="mb-2")
        #Pipeline Cards
        property_card()
        grid_card()
        #Workflow Cards
        stacks_card()
        surfaces_card()
        points_card()
        orientations_card()
        topography_card()

# -----------------------------------------------------------------------------
# UI Card & Callbacks
# -----------------------------------------------------------------------------

def ui_workflow_card(workflow_name):
    card = vuetify.VCard(
        v_show=workflow_name,
        classes="ma-1 rounded elevation-8",
    )
    return card

def ui_pipeline_card(ui_name):
    card = vuetify.VCard(
        v_show=f"active_pipeline_card == '{ui_name}'",
        classes="ma-1 rounded elevation-8",
    )
    return card

def ui_property_card():
    card = vuetify.VCard(
        v_show="active_pipeline_card",
        classes="ma-1 rounded elevation-8",
    )
    return card

def ui_card_title(title, ui_icon, file_type, file_id):
    with vuetify.VCardTitle(
        classes="grey lighten-1 pa-0 grey--text text--darken-3",
        style="user-select: none; cursor: pointer",
        hide_details=True,
        dense=True,
    ) as card_title:
        vuetify.VIcon(ui_icon, classes="mr-3", color="grey darken-3")
        html.Div(title)
        vuetify.VSpacer()
        with vuetify.VBtn(
            click=f"importType='{file_type}';document.getElementById('{file_id}').click();",
            dense=True,
            icon=True,
            tile=True,
            small=True,
        ):
            vuetify.VIcon("mdi-database-arrow-up-outline")
        html.Input(
            id=file_id,
            type="file",
            style="display: none",
            __events=["change"],
            change="importFile=$event.target.files[0]",
        )
    return card_title

def ui_property_card_title(title, ui_icon):
    with vuetify.VCardTitle(
        classes="grey lighten-1 pa-0 grey--text text--darken-3",
        style="user-select: none; cursor: pointer",
        hide_details=True,
        dense=True,
    ) as card_title:
        vuetify.VIcon(ui_icon, classes="mr-3", color="grey darken-3")
        html.Div(title)
    return card_title

def ui_workflow_card_text(condition):
    card_text = vuetify.VCardText(
        v_show=condition,
        classes="pa-1",
    )
    return card_text

def ui_card_text():
    card_text = vuetify.VCardText(classes="pa-1")
    return card_text

def ui_workflow_card_actions(condition):
    card_actions = vuetify.VCardActions(
        v_show=condition,
        classes="px-0 py-1",
        hide_details=True,
        dense=True,
    )
    return card_actions

def ui_card_actions():
    card_actions = vuetify.VCardActions(
        classes="px-0 py-1",
        hide_details=True,
        dense=True,
    )
    return card_actions

@state.change("importFile")
def import_file(importType, importFile, **kwargs):
    if importFile:
        application.subsurface.import_data(importType, importFile)
    # reset layout state
    state.importFile = None

# -----------------------------------------------------------------------------
# UI Property Card
# -----------------------------------------------------------------------------

def property_card():
    with ui_property_card() as card:
        card_title = ui_property_card_title(
            title="Properties",
            ui_icon="mdi-tools",
        )
        with ui_card_text(
        ) as card_text:
            property_card_text()
        with ui_card_actions(
        ) as card_actions:
            property_card_actions()

def property_card_text():
    with vuetify.VRow(classes="pa-0", dense=True):
        with vuetify.VCol(cols="6"):
            vuetify.VSelect(
                # Representation
                v_model=("current_representation", 3),
                items=(
                    "representations",
                    [
                        {"text": "Points", "value": 0},
                        {"text": "Wireframe", "value": 1},
                        {"text": "Surface", "value": 2},
                        {"text": "SurfaceWithEdges", "value": 3},
                    ],
                ),
                label="Representation",
                hide_details=True,
                dense=True,
                outlined=True,
                classes="pt-1",
            )
        with vuetify.VCol(cols="6"):
            vuetify.VSlider(
                # Opacity
                v_model=("current_opacity", 0.2),
                min=0,
                max=1,
                step=0.1,
                label="Opacity",
                classes="mt-1",
                hide_details=True,
                dense=True,
            )

def property_card_actions():
    vuetify.VSpacer()

@state.change("current_representation")
def update_representation(active_pipeline_card, current_representation, **kwargs):
    print("representation entry ", time.time())
    dirty = application.viz.set_representation(active_pipeline_card, current_representation)
    print("representation exit ", time.time())
    if dirty:
        application.html_view3D.update()
    print("representation update geometry ", time.time())

@state.change("current_opacity")
def update_opacity(active_pipeline_card, current_opacity, **kwargs):
    print("opacity entry ", time.time())
    dirty = application.viz.set_opacity(active_pipeline_card, current_opacity)
    print("opacity exit ", time.time())
    if dirty:
        application.html_view3D.update()
    print("opacity update geometry ", time.time())

# -----------------------------------------------------------------------------
# UI Grid Card
# -----------------------------------------------------------------------------

def grid_card():
    with ui_pipeline_card(
        ui_name="grid",
    ) as card:
        card_title = ui_card_title(
            title="Grid",
            ui_icon="mdi-grid",
            file_type="grid.csv",
            file_id="gridFile",
        )
        with ui_card_text(
        ) as card_text:
            grid_card_text()
        with ui_card_actions(
        ) as card_actions:
            grid_card_actions()

def grid_card_text():
    html.Div("Extent")
    vuetify.VDivider(classes="mb-2")
    with vuetify.VRow(classes="pa-0 pt-1", dense=True):
        with vuetify.VCol(cols="6"):
            vuetify.VTextField(
                classes="mb-1",
                dense=True,
                hide_details=True,
                label="X min",
                type="number",
                v_model=("grid.extent[0]",),
            )
        with vuetify.VCol(cols="6"):
            vuetify.VTextField(
                classes="mb-1",
                dense=True,
                hide_details=True,
                label="X max",
                type="number",
                v_model=("grid.extent[1]",),
            )
        with vuetify.VCol(cols="6"):
            vuetify.VTextField(
                classes="mb-1",
                dense=True,
                hide_details=True,
                label="Y min",
                type="number",
                v_model=("grid.extent[2]",),
            )
        with vuetify.VCol(cols="6"):
            vuetify.VTextField(
                classes="mb-1",
                dense=True,
                hide_details=True,
                label="Y max",
                type="number",
                v_model=("grid.extent[3]",),
            )
        with vuetify.VCol(cols="6"):
            vuetify.VTextField(
                classes="mb-1",
                dense=True,
                hide_details=True,
                label="Z min",
                type="number",
                v_model=("grid.extent[4]",),
            )
        with vuetify.VCol(cols="6"):
            vuetify.VTextField(
                classes="mb-1",
                dense=True,
                hide_details=True,
                label="Z max",
                type="number",
                v_model=("grid.extent[5]",),
            )
    html.Div("Resolution")
    vuetify.VDivider(classes="mb-2")
    with vuetify.VRow(classes="pa-0 pt-1", dense=True):
        with vuetify.VCol(cols="4"):
            vuetify.VTextField(
                classes="mb-1",
                dense=True,
                hide_details=True,
                label="NX",
                type="number",
                v_model=("grid.resolution[0]",),
            )
        with vuetify.VCol(cols="4"):
            vuetify.VTextField(
                classes="mb-1",
                dense=True,
                hide_details=True,
                label="NY",
                type="number",
                v_model=("grid.resolution[1]",),
            )
        with vuetify.VCol(cols="4"):
            vuetify.VTextField(
                classes="mb-1",
                dense=True,
                hide_details=True,
                label="NZ",
                type="number",
                v_model=("grid.resolution[2]",),
            )

def grid_card_actions():
    vuetify.VSpacer()
    with vuetify.VBtn(
        classes="ma-0",
        icon=True,
        dense=True,
        small=True,
        tile=True,
        color="error",
        click=reset_grid,
    ):
        vuetify.VIcon("mdi-cancel")
    with vuetify.VBtn(
        classes="ma-0",
        icon=True,
        dense=True,
        small=True,
        tile=True,
        color="success",
        click="flushState('grid');",
    ):
        vuetify.VIcon("mdi-check")

@state.change("grid")
def update_grid(grid, **kwargs):
    extent = [float(x) for x in grid.get("extent")]
    resolution = [int(x) for x in grid.get("resolution")]
    slider_x_max = resolution[0] - 1
    state.slider_x_max = slider_x_max
    slider_y_max = resolution[1] - 1
    state.slider_y_max = slider_y_max
    slider_z_max = resolution[2] - 1
    state.slider_z_max = slider_z_max
    dirty_subsurface = application.subsurface.update_grid(extent, resolution)
    dirty_viz = application.viz.update_grid()
    if dirty_viz:
        application.viz.compute(computing=False)
        application.html_view3D.update()

def reset_grid():
    application.subsurface.dirty("grid")

# -----------------------------------------------------------------------------
# Stacks and Surfaces (SS) Callbacks
# -----------------------------------------------------------------------------

def ss_select(type, id):
    application.subsurface.select(type, id)

def ss_move(type, direction):
    application.subsurface.move(type, direction)

def ss_new(type, data):
    application.subsurface.add(type, data)
    # Reset layout state
    state[f"{type.lower()}New"] = DEFAULT_NEW[type]

def ss_new_with_id(type, data, idname, id):
    data[idname] = id
    application.subsurface.add(type, data)
    # Reset layout state
    state[f"{type.lower()}New"] = DEFAULT_NEW[type]

def ss_remove(type, id):
    application.subsurface.remove(type, id)

# -----------------------------------------------------------------------------
# Workflow Stacks Card
# -----------------------------------------------------------------------------

def stacks_card():
    with ui_workflow_card(
        workflow_name="stacks_workflow",
    ) as card:
        card_title = ui_card_title(
            title="Stacks",
            ui_icon="mdi-layers-triple",
            file_type="stacks.csv",
            file_id="stacksFile",
        )
        with ui_workflow_card_text("true") as card_text:
            stacks_card_text()
        with ui_workflow_card_actions("true") as card_actions:
            stacks_card_actions()

def stacks_card_text():
    with vuetify.VList(
        classes="pa-0",
        dense=True,
        hide_details=True,
    ):
        with vuetify.VListItem(
            v_for="(stack, index) in stacks",
            key="index",
            classes=("{ 'v-item--active v-list-item--active': stack.id === activeStackId, 'pa-0': true }",),
            dense=True,
            hide_details=True,
            click=(ss_select, "['Stack', stack.id]"),
            color="primary",
        ):
            with vuetify.VListItemIcon(
                v_if="stack.feature === 'Fault'",
                classes="float-left",
            ):
                vuetify.VIcon("mdi-abjad-hebrew")
            with vuetify.VListItemIcon(
                v_if="stack.feature === 'Onlap'",
                classes="float-left",
            ):
                vuetify.VIcon("mdi-chart-sankey-variant")
            with vuetify.VListItemIcon(
                v_if="stack.feature === 'Erosion'",
                classes="float-left",
            ):
                vuetify.VIcon("mdi-waves")
            with vuetify.VListItemContent():
                vuetify.VListItemTitle("{{stack.name}}")
            with vuetify.VListItemIcon(
                classes="float-left",
            ):
                vuetify.VIcon(
                    v_text="stack.feature", __properties = ["v_text"], x_small=True,
                )

def stacks_card_actions():
    with vuetify.VRow(
        classes="py-1",
        dense=True,
        v_show="!activeStackId",
    ):
        with vuetify.VCol(cols="5"):
            vuetify.VTextField(
                classes="pl-1",
                v_model=("stackNew.name",),
                label="Name",
                dense=True,
                hide_details=True,
            )
        with vuetify.VCol(cols="5"):
            vuetify.VSelect(
                    v_model=("stackNew.feature",),
                    label="Type",
                    items=("features",),
                    dense=True,
                    hide_details=True,
            )
        vuetify.VSpacer()
        with vuetify.VBtn(
                classes="pt-4",
                icon=True,
                dense=True,
                small=True,
                tile=True,
                color="success",
                click=(ss_new, "['Stack', stackNew]"),
        ):
            vuetify.VIcon("mdi-check")
    with vuetify.VRow(
        classes="py-1",
        dense=True,
        v_show="activeStackId",
    ):
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="grey darken-3",
            click=(ss_move, "['Stack', 'up']"),
            disabled=("!activeStackActions.up",),
        ):
            vuetify.VIcon("mdi-arrow-up")
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="grey darken-3",
            click=(ss_move, "['Stack', 'down']"),
            disabled=("!activeStackActions.down",),
        ):
            vuetify.VIcon("mdi-arrow-down")
        vuetify.VSpacer()
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="error",
            click=(ss_remove, "['Stack', activeStackId]"),
            disabled=("!activeStackActions.remove",),
        ):
            vuetify.VIcon("mdi-cancel")
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="success",
            click="activeStackId = ''",
            disabled=("!activeStackActions.add",),
        ):
            vuetify.VIcon("mdi-check")

# -----------------------------------------------------------------------------
# Workflow Surfaces Card
# -----------------------------------------------------------------------------

def surfaces_card():
    with ui_workflow_card(
        workflow_name="surfaces_workflow",
    ) as card:
        card_title = ui_card_title(
            title="Surfaces",
            ui_icon="mdi-elevation-rise",
            file_type="surfaces.csv",
            file_id="surfacesFile",
        )
        with ui_workflow_card_text("activeStackId") as card_text:
            surfaces_card_text()
        with ui_workflow_card_actions("activeStackId") as card_actions:
            surfaces_card_actions()

def surfaces_card_text():
    with vuetify.VList(
        classes="pa-0",
        dense=True,
        hide_details=True,
    ):
        with vuetify.VListItem(
            v_for="(surface, index) in surfaces",
            key="index",
            classes=("{ 'v-item--active v-list-item--active': surface.id === activeSurfaceId, 'pa-0': true }",),
            dense=True,
            hide_details=True,
            click=(ss_select, "['Surface', surface.id]"),
            color="primary",
        ):
            with vuetify.VListItemIcon(
                v_if="surface.feature === 'Fault'",
                classes="float-left",
            ):
                vuetify.VIcon("mdi-slash-forward", color=("surface.color",))
            with vuetify.VListItemIcon(
                v_if="surface.feature === 'Onlap'",
                classes="float-left",
            ):
                vuetify.VIcon("mdi-chart-sankey-variant", color=("surface.color",))
            with vuetify.VListItemIcon(
                v_if="surface.feature === 'Erosion'",
                classes="float-left",
            ):
                vuetify.VIcon("mdi-wave", color=("surface.color",))
            with vuetify.VListItemContent():
                vuetify.VListItemTitle("{{surface.name}}")
            with vuetify.VListItemIcon(
                classes="float-left",
            ):
                vuetify.VIcon(
                    v_text="surface.stackname", __properties = ["v_text"], x_small=True,
                )

def surfaces_card_actions():
    with vuetify.VRow(
        classes="py-1",
        dense=True,
        v_show="!activeSurfaceId",
    ):
        with vuetify.VCol(cols="5"):
            vuetify.VTextField(
                classes="pl-1",
                v_model=("surfaceNew.name",),
                label="Name",
                dense=True,
                hide_details=True,
            )
        vuetify.VSpacer()
        with vuetify.VBtn(
                classes="pt-4",
                icon=True,
                dense=True,
                small=True,
                tile=True,
                color="success",
                click=(ss_new_with_id, "['Surface', surfaceNew, 'stackid', activeStackId]"),
        ):
            vuetify.VIcon("mdi-check")
    with vuetify.VRow(
        classes="py-1",
        dense=True,
        v_show="activeSurfaceId",
    ):
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="grey darken-3",
            click=(ss_move, "['Surface', 'up']"),
            disabled=("!activeSurfaceActions.up",),
        ):
            vuetify.VIcon("mdi-arrow-up")
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="grey darken-3",
            click=(ss_move, "['Surface', 'down']"),
            disabled=("!activeSurfaceActions.down",),
        ):
            vuetify.VIcon("mdi-arrow-down")
        vuetify.VSpacer()
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="error",
            click=(ss_remove, "['Surface', activeSurfaceId]"),
            disabled=("!activeSurfaceActions.remove",),
        ):
            vuetify.VIcon("mdi-cancel")
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="success",
            click="activeSurfaceId = ''",
            disabled=("!activeSurfaceActions.add",),
        ):
            vuetify.VIcon("mdi-check")

# -----------------------------------------------------------------------------
# Workflow Points Card
# -----------------------------------------------------------------------------

def points_card():
    with ui_workflow_card(
        workflow_name="points_workflow",
    ) as card:
        card_title = ui_card_title(
            title="Points",
            ui_icon="mdi-chart-bubble",
            file_type="points.csv",
            file_id="pointsFile",
        )
        with ui_workflow_card_text("activeStackId && activeSurfaceId") as card_text:
            points_card_text()
        with ui_workflow_card_actions("activeStackId && activeSurfaceId") as card_actions:
            points_card_actions()

def points_card_text():
    with vuetify.VList(
        classes="pa-0",
        dense=True,
        hide_details=True,
    ):
        vuetify.VSubheader(
            "X, Y, Z",
            classes="d-flex justify-center",
        )
        with vuetify.VListItem(
            v_for="(point, index) in points",
            key="index",
            classes=("{ 'v-item--active v-list-item--active': point.id === activePointId, 'pa-0': true }",),
            dense=True,
            hide_details=True,
            click=(ss_select, "['Point', point.id]"),
            color="primary",
        ):
            with vuetify.VListItemIcon(
                classes="float-left",
            ):
                vuetify.VIcon("mdi-circle-medium")
            vuetify.VListItemContent(
                "{{point.x}}, {{point.y}}, {{point.z}}",
                classes="d-flex justify-center text-caption",
                x_small=True,
            )
            with vuetify.VListItemIcon(
                classes="float-right",
            ):
                vuetify.VIcon(
                    v_text="point.surfacename", __properties = ["v_text"], x_small=True,
                )

def points_card_actions():
    with vuetify.VRow(
        classes="py-1",
        dense=True,
        v_show="!activePointId",
    ):
        with vuetify.VCol(cols="3"):
            vuetify.VTextField(
                classes="pl-1",
                v_model=("pointNew.x",),
                label="X",
                type="number",
                dense=True,
                hide_details=True,
            )
        with vuetify.VCol(cols="3"):
            vuetify.VTextField(
                v_model=("pointNew.y",),
                label="Y",
                type="number",
                dense=True,
                hide_details=True,
            )
        with vuetify.VCol(cols="3"):
            vuetify.VTextField(
                v_model=("pointNew.z",),
                label="Z",
                type="number",
                dense=True,
                hide_details=True,
            )
        vuetify.VSpacer()
        with vuetify.VBtn(
                classes="pt-4",
                icon=True,
                dense=True,
                small=True,
                tile=True,
                color="success",
                click=(ss_new_with_id, "['Point', pointNew, 'surfaceid', activeSurfaceId]"),
        ):
            vuetify.VIcon("mdi-check")
    with vuetify.VRow(
        classes="py-1",
        dense=True,
        v_show="activePointId",
    ):
        vuetify.VSpacer()
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="error",
            click=(ss_remove, "['Point', activePointId]"),
            disabled=("!activePointActions.remove",),
        ):
            vuetify.VIcon("mdi-cancel")
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="success",
            click="activePointId = ''",
            disabled=("!activePointActions.add",),
        ):
            vuetify.VIcon("mdi-check")

# -----------------------------------------------------------------------------
# Workflow Orientations Card
# -----------------------------------------------------------------------------

def orientations_card():
    with ui_workflow_card(
        workflow_name="orientations_workflow",
    ) as card:
        card_title = ui_card_title(
            title="Orientations",
            ui_icon="mdi-compass",
            file_type="orientations.csv",
            file_id="orientationsFile",
        )
        with ui_workflow_card_text("activeStackId && activeSurfaceId") as card_text:
            orientations_card_text()
        with ui_workflow_card_actions("activeStackId && activeSurfaceId") as card_actions:
            orientations_card_actions()

def orientations_card_text():
    with vuetify.VList(
        classes="pa-0",
        dense=True,
        hide_details=True,
    ):
        vuetify.VSubheader(
            "X, Y, Z & GX, GY, GZ",
            classes="d-flex justify-center",
        )
        with vuetify.VListItem(
            v_for="(orientation, index) in orientations",
            key="index",
            classes=("{ 'v-item--active v-list-item--active': orientation.id === activeOrientationId, 'pa-0': true }",),
            dense=True,
            hide_details=True,
            click=(ss_select, "['Orientation', orientation.id]"),
            color="primary",
        ):
            with vuetify.VListItemIcon(
                classes="float-left",
            ):
                vuetify.VIcon("mdi-compass-outline")
            vuetify.VListItemContent(
                "{{orientation.x}}, {{orientation.y}}, {{orientation.z}} & {{Number.parseFloat(orientation.gx).toFixed(2)}}, {{Number.parseFloat(orientation.gy).toFixed(2)}}, {{Number.parseFloat(orientation.gz).toFixed(2)}}",
                classes="d-flex justify-center text-caption",
                x_small=True,
            )
            with vuetify.VListItemIcon(
                classes="float-right",
            ):
                vuetify.VIcon(
                    v_text="orientation.surfacename", __properties = ["v_text"], x_small=True,
                )

def orientations_card_actions():
    with vuetify.VRow(
        classes="py-1",
        dense=True,
        v_show="!activeOrientationId",
    ):
        with vuetify.VCol(cols="3"):
            vuetify.VTextField(
                classes="pl-1",
                v_model=("orientationNew.x",),
                label="X",
                type="number",
                dense=True,
                hide_details=True,
            )
        with vuetify.VCol(cols="3"):
            vuetify.VTextField(
                v_model=("orientationNew.y",),
                label="Y",
                type="number",
                dense=True,
                hide_details=True,
            )
        with vuetify.VCol(cols="3"):
            vuetify.VTextField(
                v_model=("orientationNew.z",),
                label="Z",
                type="number",
                dense=True,
                hide_details=True,
            )
        with vuetify.VCol(cols="3", classes="px-0"):
            vuetify.VSpacer()
            with vuetify.VBtn(
                    classes="pt-2 float-right",
                    icon=True,
                    dense=True,
                    small=True,
                    tile=True,
                    color="success",
                    click=(ss_new_with_id, "['Orientation', orientationNew, 'surfaceid', activeSurfaceId]"),
            ):
                vuetify.VIcon("mdi-check")
        with vuetify.VCol(cols="3"):
            vuetify.VTextField(
                classes="pl-1",
                v_model=("orientationNew.gx",),
                label="GX",
                type="number",
                dense=True,
                hide_details=True,
            )
        with vuetify.VCol(cols="3"):
            vuetify.VTextField(
                v_model=("orientationNew.gy",),
                label="GY",
                type="number",
                dense=True,
                hide_details=True,
            )
        with vuetify.VCol(cols="3"):
            vuetify.VTextField(
                v_model=("orientationNew.gz",),
                label="GZ",
                type="number",
                dense=True,
                hide_details=True,
            )
    with vuetify.VRow(
        classes="py-1",
        dense=True,
        v_show="activeOrientationId",
    ):
        vuetify.VSpacer()
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="error",
            click=(ss_remove, "['Orientation', activeOrientationId]"),
            disabled=("!activeOrientationActions.remove",),
        ):
            vuetify.VIcon("mdi-cancel")
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="success",
            click="activeOrientationId = ''",
            disabled=("!activeOrientationActions.add",),
        ):
            vuetify.VIcon("mdi-check")

# -----------------------------------------------------------------------------
# Workflow Topology Card
# -----------------------------------------------------------------------------

def topography_card():
    with ui_pipeline_card(
        ui_name="topography",
    ) as card:
        card_title = ui_card_title(
            title="Topography",
            ui_icon="mdi-image-filter-hdr",
            file_type="topography.zip",
            file_id="topographyFile",
        )
        with ui_card_text() as card_text:
            topography_card_text()
        with ui_card_actions() as card_actions:
            topography_card_actions()

def topography_card_text():
    with vuetify.VRow(classes="pa-0", dense=True):
        with vuetify.VCol(cols="6"):
            vuetify.VSelect(
                # Type
                v_model=("topography_category", 0),
                items=(
                    "category",
                    [
                        {"text": "Random", "value": 0},
                        {"text": "GDAL", "value": 1},
                        {"text": "Saved", "value": 2},
                    ],
                ),
                label="Type",
                hide_details=True,
                dense=True,
                outlined=True,
                classes="pt-1",
            )
    with vuetify.VContainer(v_show="topography_category === 0", classes="px-0 pt-2 pb-0", dense=True):
        with vuetify.VRow(classes="pa-0 pt-1", dense=True):
            with vuetify.VCol(cols="6"):
                vuetify.VTextField(
                    classes="mb-1",
                    dense=True,
                    hide_details=True,
                    label="Seed",
                    type="number",
                    v_model=("topography.seed",),
                )
            with vuetify.VCol(cols="6"):
                vuetify.VTextField(
                    classes="mb-1",
                    dense=True,
                    hide_details=True,
                    label="FD",
                    type="number",
                    v_model=("topography.fd",),
                )
            with vuetify.VCol(cols="6"):
                vuetify.VTextField(
                    classes="mb-1",
                    dense=True,
                    hide_details=True,
                    label="dZ Min",
                    type="number",
                    v_model=("topography.dzmin",),
                )
            with vuetify.VCol(cols="6"):
                vuetify.VTextField(
                    classes="mb-1",
                    dense=True,
                    hide_details=True,
                    label="dZ Max",
                    type="number",
                    v_model=("topography.dzmax",),
                )
            with vuetify.VCol(cols="6"):
                vuetify.VTextField(
                    classes="mb-1",
                    dense=True,
                    hide_details=True,
                    label="X Resolution",
                    type="number",
                    v_model=("topography.rx",),
                )
            with vuetify.VCol(cols="6"):
                vuetify.VTextField(
                    classes="mb-1",
                    dense=True,
                    hide_details=True,
                    label="Y Resolution",
                    type="number",
                    v_model=("topography.ry",),
                )

def topography_card_actions():
    with vuetify.VRow(
        classes="py-1",
        dense=True,
        v_show="topography_category === 0",
    ):
        vuetify.VSpacer()
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="error",
            click=reset_topography,
        ):
            vuetify.VIcon("mdi-cancel")
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="success",
            click="topography.on=true;topography.category=topography_items[topography_category];flushState('topography');",
        ):
            vuetify.VIcon("mdi-check")
    with vuetify.VRow(
        classes="py-1",
        dense=True,
        v_show="topography_category > 0",
    ):
        vuetify.VSpacer()
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="error",
            click=reset_topography,
        ):
            vuetify.VIcon("mdi-cancel")
        with vuetify.VBtn(
            click=f"document.getElementById('topography_id').click();",
            dense=True,
            icon=True,
            tile=True,
            small=True,
            color="success",
        ):
            vuetify.VIcon("mdi-database-check-outline")
        html.Input(
            id="topography_id",
            type="file",
            style="display: none",
            __events=["change"],
            change="topography.on=true;topography.category=topography_items[topography_category];topography_file=$event.target.files[0];",
        )

@state.change("topography")
def update_topography(topography, **kwargs):
    if topography["on"] == True:
        application.subsurface.update_topography(topography)
        application.viz.update_topography()

@state.change("topography_file")
def update_topography_file(topography_file, topography, **kwargs):
    if topography_file:
        application.subsurface.update_topography_file(topography["category"], topography_file)
        application.viz.update_topography()
    state.topography_file = None

def reset_topography():
    application.subsurface.dirty("topography")

# -----------------------------------------------------------------------------
# UI Drawer Pipeline Widget & Callbacks
# -----------------------------------------------------------------------------

icon_manager = LocalFileManager(__file__)
icon_manager.url("delete", "./icons/trash-can-outline.svg")
icon_manager.url("collapsed", "./icons/chevron-up.svg")
icon_manager.url("collapsable", "./icons/chevron-down.svg")

ICONS = icon_manager.assets

def pipeline_widget():
    trame.GitTree(
        width=325,
        text_color=("$vuetify.theme.dark ? ['white', 'black'] : ['black', 'white']",),
        active_background="#bdbdbd",
        sources=("pipeline_tree",),
        action_map=("icons", ICONS),
        action_size=25,
        action=(on_action, "[$event]"),
        actives = ("active_ids", []),
        actives_change=(actives_change, "[$event]"),
        visibility_change=(visibility_change, "[$event]"),
    )

def get_pipeline(id):
    _pipelines = state.pipelines
    for item in _pipelines[0]:
        if item["id"] == id:
            return item["pipeline"]
    return 0

def on_action(event):
    _id = event.get("id")
    _pipeline = get_pipeline(_id)
    _action = event.get("action")
    if _action.startswith("collap"):
        _collapsed = application.pipeline_manager.toggle_collapsed(_id)

def actives_change(ids):
    _id = ids[0]
    card = state.active_pipeline_card
    prv_ids = state.active_ids
    _pipeline = get_pipeline(_id)
    if prv_ids == ids:
        state.active_ids = []
        state.active_pipeline_card = None
    else:
        if _pipeline != 0:
            state.active_pipeline_card = _pipeline
            representation = application.viz.get_representation(_pipeline)
            opacity = application.viz.get_opacity(_pipeline)
            state.current_representation = representation
            state.current_opacity = opacity
        else:
            state.active_pipeline_card = None
        state.active_ids = ids

def visibility_change(event):
    _id = event["id"]
    _pipeline = get_pipeline(_id)
    _visibility = event["visible"]
    dirty = application.viz.set_visibility(_pipeline, _visibility)
    if dirty:
        application.pipeline_manager.set_visible(_id, _visibility)
        application.html_view3D.update()

# -----------------------------------------------------------------------------
# UI Content Widget & Callbacks
# -----------------------------------------------------------------------------

def create_content(content):
    with content:
        with vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
            style="position: relative",
        ):
            with vuetify.VRow(
                no_gutters=True,
                classes="ma-0",
                style=("{ height: viewLayout !== 'singleView' ? '50%' : '100%' }",),
            ):
                with vuetify.VCol(
                    v_show="viewLayout !== 'singleView'",
                    style="position: relative",
                ):
                    with trame.SizeObserver("x_figure_size") as x_size:
                        x_size.add_child(application.html_viewX)
                    vuetify.VSlider(
                        label="X",
                        style="position: absolute;z-index: 1;left: 10px;right: 10px;bottom: 0;",
                        hide_details=True,
                        color="red",
                        track_color="red",
                        min=0,
                        max=("slider_x_max",9),
                        v_model=("slice_x",5),
                        thumb_label=True,
                        thumb_size="24",
                        thumb_color="blue-grey",
                    )
                vuetify.VCol(
                    classes="pa-0 fill-height",
                    children=[application.html_view3D],
                )
            with vuetify.VRow(
                no_gutters=True,
                classes="ma-0",
                style=("{ height: viewLayout !== 'singleView' ? '50%' : '100%' }",),
            ):
                with vuetify.VCol(
                    v_show="viewLayout !== 'singleView'",
                    style="position: relative; axiscolor: 'white';",
                ):
                    with trame.SizeObserver("y_figure_size") as y_size:
                        y_size.add_child(application.html_viewY)
                    vuetify.VSlider(
                        label="Y",
                        style="position: absolute;z-index: 1;left: 10px;right: 10px;bottom: 0;",
                        dense=True,
                        hide_details=True,
                        color="yellow",
                        track_color="yellow",
                        min=0,
                        max=("slider_y_max",9),
                        v_model=("slice_y",5),
                        thumb_label=True,
                        thumb_size="24",
                        thumb_color="blue-grey",
                    )
                with vuetify.VCol(
                    v_show="viewLayout !== 'singleView'",
                    style="position: relative",
                ):
                    with trame.SizeObserver("z_figure_size") as z_size:
                        z_size.add_child(application.html_viewZ)
                    vuetify.VSlider(
                        label="Z",
                        style="position: absolute;z-index: 1;left: 10px;right: 10px;bottom: 0;",
                        dense=True,
                        hide_details=True,
                        color="green",
                        track_color="green",
                        min=0,
                        max=("slider_z_max",9),
                        v_model=("slice_z",5),
                        thumb_label=True,
                        thumb_size="24",
                        thumb_color="blue-grey",
                    )

@state.change("slice_x")
def update_slice_x(slice_x, **kwargs):
    application.html_viewX.update(figure=application.viz.update_xfig(**x_fig_state.size,cell_number=[slice_x]))

@state.change("x_figure_size")
def update_viewX(**kwargs):
    application.html_viewX.update(figure=application.viz.update_xfig(**x_fig_state.size, cell_number=state.slice_x))

@state.change("slice_y")
def update_slice_y(slice_y, **kwargs):
    application.html_viewY.update(figure=application.viz.update_yfig(**y_fig_state.size,cell_number=[slice_y]))

@state.change("y_figure_size")
def update_viewY(**kwargs):
    application.html_viewY.update(figure=application.viz.update_yfig(**y_fig_state.size, cell_number=state.slice_y))

@state.change("slice_z")
def update_slice_z(slice_z, **kwargs):
    application.html_viewZ.update(figure=application.viz.update_zfig(**z_fig_state.size,cell_number=[slice_z]))

@state.change("z_figure_size")
def update_viewZ(**kwargs):
    application.html_viewZ.update(figure=application.viz.update_zfig(**z_fig_state.size, cell_number=state.slice_z))

# -----------------------------------------------------------------------------
# GUI Layout
# -----------------------------------------------------------------------------

application = Application()

create_toolbar(application.layout.toolbar)
create_drawer(application.layout.drawer)
create_content(application.layout.content)

state.update({
    "active_pipeline_card": None,
    "importType": None,
    "importFile": None,
    "topography_file": None,
    "import_model_file": None,
    "export_model_file": None,
    "run": False,
    "run_button": False,
    "stackNew": DEFAULT_NEW_STACK,
    "surfaceNew": DEFAULT_NEW_SURFACE,
    "pointNew": DEFAULT_NEW_POINT,
    "orientationNew": DEFAULT_NEW_ORIENTATION,
    "topography_items": TOPOGRAPHY_ITEMS,
})

# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    #print(application.layout.html)
    server.start()
