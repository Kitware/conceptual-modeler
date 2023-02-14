import time

from trame.assets.local import LocalFileManager
from trame.ui.vuetify import SinglePageWithDrawerLayout
from trame.widgets import html,vuetify, trame, vtk, matplotlib

from . import cm_assets

PIPELINE_ICON_MANAGER = LocalFileManager(__file__)
PIPELINE_ICON_MANAGER.url("delete", "./icons/trash-can-outline.svg")
PIPELINE_ICON_MANAGER.url("collapsed", "./icons/chevron-up.svg")
PIPELINE_ICON_MANAGER.url("collapsable", "./icons/chevron-down.svg")

PIPELINE_ICONS = PIPELINE_ICON_MANAGER.assets

def initialize(server):
    state, ctrl = server.state, server.controller

    state.trame__title = "Conceptual Modeler"
    state.trame__favicon = "__global/assets/logo.svg"

    server.enable_module(cm_assets)

    with SinglePageWithDrawerLayout(server) as layout:
        layout.title.set_text(state.trame__title)
        with layout.icon:
            html.Span(
                f'<img height="32px" width="32px" src="{state.trame__favicon}" />',
                classes="mr-2",
                style="display: flex; align-content: center;",
            )
        with layout.toolbar as toolbar:
            create_toolbar(ctrl)
        with layout.drawer as drawer:
            create_drawer(drawer, ctrl)
        with layout.content as content:
            create_content(content, state, ctrl)

        # Footer
        # layout.footer.hide()

# -----------------------------------------------------------------------------
# UI Toolbar
# -----------------------------------------------------------------------------

def create_toolbar(ctrl):
    vuetify.VSpacer()
    workflow_buttons()
    vuetify.VSpacer()
    run_button()
    import_button()
    export_button()
    save_simulation_grid_button()
    vuetify.VDivider(vertical=True, classes="mx-2")
    view_buttons()
    vuetify.VDivider(vertical=True, classes="mx-2")
    standard_buttons(ctrl)

# -----------------------------------------------------------------------------
# Workflow Buttons
# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
# View Buttons
# -----------------------------------------------------------------------------

def view_buttons():
    with vuetify.VBtnToggle(
        v_model=("viewLayout", "singleView"),
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

# -----------------------------------------------------------------------------
# Run Button
# -----------------------------------------------------------------------------

def run_button():
    vuetify.VCheckbox(
        v_model=("run", False),
        color="success",
        on_icon="mdi-run",
        off_icon="mdi-run",
        classes="mx-1",
        hide_details=True,
        dense=True,
        disabled=("run_button", False),
    )

# -----------------------------------------------------------------------------
# Import/Export Buttons
# -----------------------------------------------------------------------------

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

def save_simulation_grid_button():
    vuetify.VCheckbox(
        v_model=("save_simulation_grid", False),
        color="success",
        on_icon="mdi-content-save",
        off_icon="mdi-content-save",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )

# -----------------------------------------------------------------------------
# Standard Buttons
# -----------------------------------------------------------------------------

def standard_buttons(ctrl):
    vuetify.VCheckbox(
        v_model=("viewMode", "local"),
        false_value="remote",
        true_value="local",
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
        click=ctrl.view_3D_reset_camera,
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
        change=(ctrl.theme_mode, "[$event]"),
    )

# -----------------------------------------------------------------------------
# Drawer
# -----------------------------------------------------------------------------

def create_drawer(drawer, ctrl):
        drawer.width = 325
        pipeline_widget(ctrl)
        vuetify.VDivider(classes="mb-2")
        # Pipeline Cards
        property_card()
        grid_card(ctrl)
        topography_card(ctrl)
        # Workflow Cards
        stacks_card(ctrl)
        surfaces_card(ctrl)
        points_card(ctrl)
        orientations_card(ctrl)

# -----------------------------------------------------------------------------
# Pipeline Widget
# -----------------------------------------------------------------------------

def pipeline_widget(ctrl):
    trame.GitTree(
        width=325,
        text_color=("$vuetify.theme.dark ? ['white', 'black'] : ['black', 'white']",),
        active_background="#bdbdbd",
        sources=("pipeline_tree",),
        action_map=("icons", PIPELINE_ICONS),
        action_size=25,
        action=(ctrl.on_pipeline_action, "[$event]"),
        actives=("active_ids", []),
        actives_change=(ctrl.pipeline_actives_change, "[$event]"),
        visibility_change=(ctrl.pipeline_visibility_change, "[$event]"),
    )

# -----------------------------------------------------------------------------
# Base Card Components
# -----------------------------------------------------------------------------

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

def ui_card_text():
    card_text = vuetify.VCardText(classes="pa-1")
    return card_text

def ui_workflow_card_text(condition):
    card_text = vuetify.VCardText(
        v_show=condition,
        classes="pa-1",
    )
    return card_text

def ui_card_actions():
    card_actions = vuetify.VCardActions(
        classes="px-0 py-1",
        hide_details=True,
        dense=True,
    )
    return card_actions

def ui_workflow_card_actions(condition):
    card_actions = vuetify.VCardActions(
        v_show=condition,
        classes="px-0 py-1",
        hide_details=True,
        dense=True,
    )
    return card_actions

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

def ui_workflow_card(workflow_name):
    card = vuetify.VCard(
        v_show=workflow_name,
        classes="ma-1 rounded elevation-8",
    )
    return card

# -----------------------------------------------------------------------------
# Properties Card
# -----------------------------------------------------------------------------

def property_card():
    with ui_property_card() as card:
        card_title = ui_property_card_title(
            title="Properties",
            ui_icon="mdi-tools",
        )
        with ui_card_text() as card_text:
            property_card_text()
        with ui_card_actions() as card_actions:
            property_card_actions()

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

def property_card_text():
    with vuetify.VRow(classes="pa-0", dense=True):
        with vuetify.VCol(cols="6"):
            vuetify.VSelect(
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

# -----------------------------------------------------------------------------
# Grid Card
# -----------------------------------------------------------------------------

def grid_card(ctrl):
    with ui_pipeline_card(
        ui_name="grid",
    ) as card:
        card_title = ui_card_title(
            title="Grid",
            ui_icon="mdi-grid",
            file_type="grid.csv",
            file_id="gridFile",
        )
        with ui_card_text() as card_text:
            grid_card_text()
        with ui_card_actions() as card_actions:
            grid_card_actions(ctrl)

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

def grid_card_actions(ctrl):
    vuetify.VSpacer()
    with vuetify.VBtn(
        classes="ma-0",
        icon=True,
        dense=True,
        small=True,
        tile=True,
        color="error",
        click=ctrl.reset_grid,
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

# -----------------------------------------------------------------------------
# Topography Card
# -----------------------------------------------------------------------------

def topography_card(ctrl):
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
            topography_card_actions(ctrl)

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
    with vuetify.VContainer(
        v_show="topography_category === 0", classes="px-0 pt-2 pb-0", dense=True
    ):
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

def topography_card_actions(ctrl):
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
            click=ctrl.reset_topography,
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
            click=ctrl.reset_topography,
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

# -----------------------------------------------------------------------------
# Workflow Stacks Card
# -----------------------------------------------------------------------------

def stacks_card(ctrl):
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
            stacks_card_text(ctrl)
        with ui_workflow_card_actions("true") as card_actions:
            stacks_card_actions(ctrl)

def stacks_card_text(ctrl):
    with vuetify.VList(
        classes="pa-0",
        dense=True,
        hide_details=True,
    ):
        with vuetify.VListItem(
            v_for="(stack, index) in stacks",
            key="index",
            classes=(
                "{ 'v-item--active v-list-item--active': stack.id === activeStackId, 'pa-0': true }",
            ),
            dense=True,
            hide_details=True,
            click=(ctrl.ss_select, "['Stack', stack.id]"),
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
                    v_text="stack.feature",
                    __properties=["v_text"],
                    x_small=True,
                )

def stacks_card_actions(ctrl):
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
            click=(ctrl.ss_new, "['Stack', stackNew]"),
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
            click=(ctrl.ss_move, "['Stack', 'up']"),
            disabled=("!activeStackActions.up",),
        ):
            vuetify.VIcon("mdi-arrow-up")
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="grey darken-3",
            click=(ctrl.ss_move, "['Stack', 'down']"),
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
            click=(ctrl.ss_remove, "['Stack', activeStackId]"),
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

def surfaces_card(ctrl):
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
            surfaces_card_text(ctrl)
        with ui_workflow_card_actions("activeStackId") as card_actions:
            surfaces_card_actions(ctrl)

def surfaces_card_text(ctrl):
    with vuetify.VList(
        classes="pa-0",
        dense=True,
        hide_details=True,
    ):
        with vuetify.VListItem(
            v_for="(surface, index) in surfaces",
            key="index",
            classes=(
                "{ 'v-item--active v-list-item--active': surface.id === activeSurfaceId, 'pa-0': true }",
            ),
            dense=True,
            hide_details=True,
            click=(ctrl.ss_select, "['Surface', surface.id]"),
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
                    v_text="surface.stackname",
                    __properties=["v_text"],
                    x_small=True,
                )

def surfaces_card_actions(ctrl):
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
            click=(ctrl.ss_new_with_id, "['Surface', surfaceNew, 'stackid', activeStackId]"),
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
            click=(ctrl.ss_move, "['Surface', 'up']"),
            disabled=("!activeSurfaceActions.up",),
        ):
            vuetify.VIcon("mdi-arrow-up")
        with vuetify.VBtn(
            icon=True,
            dense=True,
            small=True,
            tile=True,
            color="grey darken-3",
            click=(ctrl.ss_move, "['Surface', 'down']"),
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
            click=(ctrl.ss_remove, "['Surface', activeSurfaceId]"),
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

def points_card(ctrl):
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
            points_card_text(ctrl)
        with ui_workflow_card_actions(
            "activeStackId && activeSurfaceId"
        ) as card_actions:
            points_card_actions(ctrl)

def points_card_text(ctrl):
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
            classes=(
                "{ 'v-item--active v-list-item--active': point.id === activePointId, 'pa-0': true }",
            ),
            dense=True,
            hide_details=True,
            click=(ctrl.ss_select, "['Point', point.id]"),
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
                    v_text="point.surfacename",
                    __properties=["v_text"],
                    x_small=True,
                )

def points_card_actions(ctrl):
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
            click=(ctrl.ss_new_with_id, "['Point', pointNew, 'surfaceid', activeSurfaceId]"),
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
            click=(ctrl.ss_remove, "['Point', activePointId]"),
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

def orientations_card(ctrl):
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
            orientations_card_text(ctrl)
        with ui_workflow_card_actions(
            "activeStackId && activeSurfaceId"
        ) as card_actions:
            orientations_card_actions(ctrl)

def orientations_card_text(ctrl):
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
            classes=(
                "{ 'v-item--active v-list-item--active': orientation.id === activeOrientationId, 'pa-0': true }",
            ),
            dense=True,
            hide_details=True,
            click=(ctrl.ss_select, "['Orientation', orientation.id]"),
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
                    v_text="orientation.surfacename",
                    __properties=["v_text"],
                    x_small=True,
                )

def orientations_card_actions(ctrl):
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
                click=(
                    ctrl.ss_new_with_id,
                    "['Orientation', orientationNew, 'surfaceid', activeSurfaceId]",
                ),
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
            click=(ctrl.ss_remove, "['Orientation', activeOrientationId]"),
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
# UI Content Widget & Callbacks
# -----------------------------------------------------------------------------

def create_content(content, state, ctrl):
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
                    with trame.SizeObserver("x_figure_size"):
                        html_viewX = matplotlib.Figure(
                            figure=ctrl.update_xfig(),
                            style="position: absolute;left: 50%;top: 0px;transform: translateX(-50%);",
                        )
                        state.VIEW_FIGX = True
                        ctrl.view_x_update = html_viewX.update
                    vuetify.VSlider(
                        label="X",
                        style="position: absolute;z-index: 1;left: 10px;right: 10px;bottom: 0;",
                        hide_details=True,
                        color="red",
                        track_color="red",
                        min=0,
                        max=("slider_x_max", 9),
                        v_model=("slice_x", 5),
                        thumb_label=True,
                        thumb_size="24",
                        thumb_color="blue-grey",
                    )
                with vuetify.VCol(classes="pa-0 fill-height"):
                    html_view3D = vtk.VtkRemoteLocalView(
                        ctrl.getRenderWindow("view3D"),
                        mode="local",
                        namespace="view3D",
                    )
                    state.VIEW_3D = True
                    ctrl.view_3D_update = html_view3D.update
                    ctrl.view_3D_reset_camera = html_view3D.reset_camera
            with vuetify.VRow(
                no_gutters=True,
                classes="ma-0",
                style=("{ height: viewLayout !== 'singleView' ? '50%' : '100%' }",),
            ):
                with vuetify.VCol(
                    v_show="viewLayout !== 'singleView'",
                    style="position: relative;",
                ):
                    with trame.SizeObserver("y_figure_size"):
                        html_viewY = matplotlib.Figure(
                            figure=ctrl.update_yfig(),
                            style="position: absolute;left: 50%;top: 0px;transform: translateX(-50%);",
                        )
                        state.VIEW_FIGY = True
                        ctrl.view_y_update = html_viewY.update
                    vuetify.VSlider(
                        label="Y",
                        style="position: absolute;z-index: 1;left: 10px;right: 10px;bottom: 0;",
                        dense=True,
                        hide_details=True,
                        color="yellow",
                        track_color="yellow",
                        min=0,
                        max=("slider_y_max", 9),
                        v_model=("slice_y", 5),
                        thumb_label=True,
                        thumb_size="24",
                        thumb_color="blue-grey",
                    )
                with vuetify.VCol(
                    v_show="viewLayout !== 'singleView'",
                    style="position: relative",
                ):
                    with trame.SizeObserver("z_figure_size"):
                        html_viewZ = matplotlib.Figure(
                            figure=ctrl.update_zfig(),
                            style="position: absolute;left: 50%;top: 0px;transform: translateX(-50%);",
                        )
                        state.VIEW_FIGZ = True
                        ctrl.view_z_update = html_viewZ.update
                    vuetify.VSlider(
                        label="Z",
                        style="position: absolute;z-index: 1;left: 10px;right: 10px;bottom: 0;",
                        dense=True,
                        hide_details=True,
                        color="green",
                        track_color="green",
                        min=0,
                        max=("slider_z_max", 9),
                        v_model=("slice_z", 5),
                        thumb_label=True,
                        thumb_size="24",
                        thumb_color="blue-grey",
                    )
