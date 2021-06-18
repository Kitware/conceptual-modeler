import os
from pywebvue import App
from modeler.config import shared_state, vuetify, DEFAULT_NEW
from modeler.subsurface import SubSurfaceModeler
from modeler.workflow import WorkflowManager
from modeler.visualization import VtkViewer

# -----------------------------------------------------------------------------
# Web App setup
# -----------------------------------------------------------------------------

app = App("Conceptual Modeler", backend="vtk", debug=True)
app.state = shared_state
app.vuetify = vuetify
app.layout = "./template.html"
app.vue_use = ["vuetify", "vtk"]

# -----------------------------------------------------------------------------
# Server setup
# -----------------------------------------------------------------------------

modeler = SubSurfaceModeler(app)
workflow = WorkflowManager(app)
viz = VtkViewer(app, modeler)

# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------


@app.change("activeStackId")
def activate_stack():
    modeler.stack_select(app.get("activeStackId"))


@app.change("activeSurfaceId")
def activate_surface():
    modeler.surface_select(app.get("activeSurfaceId"))


# -----------------------------------------------------------------------------
# Method calls
# -----------------------------------------------------------------------------


@app.trigger("grid")
def update_grid(action, grid):
    # print('trigger::grid', action, grid)
    if action == "save":
        extent = grid.get("extent")
        resolution = grid.get("resolution")
        modeler.update_grid(extent, resolution)
        viz.update_grid(extent, resolution)
        workflow.update_grid()
    else:
        # reset client values to server state
        modeler.dirty("grid")


@app.trigger("ss_move")
def ss_move(type, direction):
    # print('trigger::ss_move', type, direction)
    if type == "stack":
        modeler.stack_move(direction)
    elif type == "surface":
        modeler.surface_move(direction)


@app.trigger("ss_new")
def ss_new(type, data):
    # print('trigger::ss_new', type, data)
    if type == "stack":
        modeler.stack_add(**data)
    elif type == "surface":
        modeler.surface_add(**data)

    # Reset placeholder for client
    app.set(f"{type}New", DEFAULT_NEW[type], force=True)


@app.trigger("ss_remove")
def ss_remove(type, id):
    # print('trigger::ss_remove', id)
    if type == "stack":
        modeler.stack_remove(id)
    elif type == "surface":
        modeler.surface_remove(id)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    app.run_server()
