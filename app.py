import os
import json
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

@app.change("selection")
def update_visibility():
    viz.update_visibility(app.get("selection"))

@app.change("vtkCutOrigin")
def update_slices():
    viz.update_slice_origin(app.get("vtkCutOrigin"))


@app.change("importType")
def reset_file():
    app.set("importFile", None)


@app.change("importFile")
def import_file():
    data_type = app.get("importType")
    file_data = app.get("importFile")
    if file_data:
        modeler.import_data(data_type, file_data)

    # reset current import
    workflow.update_grid()  # <= not great we should embed our wf in state
    app.set("importType", None)
    app.set("importFile", None)
    app.set("importShow", False)


@app.change("subsurfaceImportTS")
def modeler_state_changed():
    viz.update_from_modeler()


@app.change("importShow", "exportShow")
def update_io():
    if app.dirty("importShow"):
        app.set("exportShow", False)
    if app.dirty("exportShow"):
        app.set("importShow", False)


# -----------------------------------------------------------------------------
# Method calls
# -----------------------------------------------------------------------------


@app.trigger("compute")
def compute():
    print("trigger::compute")
    modeler.compute_geo_model()
    viz.compute()

@app.trigger("resetCamera")
def resetCamera():
    viz.resetCamera()

@app.trigger("grid")
def update_grid(action, grid):
    # print('trigger::grid', action, grid)
    if action == "save":
        extent = [float(x) for x in grid.get("extent")]
        resolution = [int(x) for x in grid.get("resolution")]
        modeler.update_grid(extent, resolution)
        viz.update_grid()
        workflow.update_grid()

        # extract geometry
        # modeler.compute_model()
        viz.compute()
    else:
        # reset client values to server state
        modeler.dirty("grid")


@app.trigger("ss_select")
def ss_select(type, id):
    modeler.select(type, id)


@app.trigger("ss_move")
def ss_move(type, direction):
    modeler.move(type, direction)


@app.trigger("ss_new")
def ss_new(type, data):
    modeler.add(type, data)
    # Reset placeholder for client
    app.set(f"{type.lower()}New", DEFAULT_NEW[type], force=True)


@app.trigger("ss_remove")
def ss_remove(type, id):
    modeler.remove(type, id)


def export_state():
    if app.get("exportShow"):
        app.set("exportShow", False)
    else:
        modeler.export()
        app.set("exportShow", True)
        app.set("importShow", False)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    app.on_ready = viz.update_views
    app.run_server()
