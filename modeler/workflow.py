class WorkflowManager:
    def __init__(self, app):
        self._app = app
        self._active_step = "grid"
        self._steps = [
            {"icon": "mdi-grid", "disabled": False, "value": "grid", "label": "Grid"},
            {
                "icon": "mdi-chart-timeline-variant-shimmer",
                "disabled": False,
                "value": "subsurface",
                "label": "Sub-surface",
            },
            {
                "icon": "mdi-image-filter-hdr",
                "disabled": False,
                "value": "topography",
                "label": "Topography",
            },
             {
                "icon": "mdi-cube-scan",
                "disabled": False,
                "value": "visualization",
                "label": "Visualization",
            },
        ]
        app.state.update(self.state)

    def update_grid(self):
        self._steps[1]["disabled"] = False
        self.dirty("steps")

    @property
    def state(self):
        return {
            "activeStep": self._active_step,
            "steps": self._steps,
        }

    def dirty(self, *args):
        state = self.state
        for name in args:
            self._app.set(name, None)
            self._app.set(name, state[name])
