import os
from pywebvue import App
from modeler.SharedState import shared_state
from modeler.GemPy import GemPyModeler
from modeler.Visualization import VtkViewer

# -----------------------------------------------------------------------------
# Web App setup
# -----------------------------------------------------------------------------

app = App("Conceptual Modeler", backend="vtk", debug=False)
app.layout = "./template.html"
app.vue_use = ["vuetify", "vtk"]

# -----------------------------------------------------------------------------
# Server setup
# -----------------------------------------------------------------------------

modeler = GemPyModeler(app)
viz = VtkViewer(app, modeler)

# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    app.run_server()
