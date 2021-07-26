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

shared_state = {
    # SubSurface client models
    "stackNew": DEFAULT_NEW_STACK,
    "surfaceNew": DEFAULT_NEW_SURFACE,
    "pointNew": DEFAULT_NEW_POINT,
    "orientationNew": DEFAULT_NEW_ORIENTATION,
    # Handling data injestion
    "fileName": "",
    "exportShow": False,
    "importShow": False,
    "computeShow": True,
    "importFile": None,
    "importType": None,
    "importTypes": [
        {"text": "Full Conceptual Modeler state", "value": "full-model.json"},
        {"text": "Grid as CSV", "value": "grid.csv"},
        {"text": "Stacks as CSV", "value": "stacks.csv"},
        {"text": "Surfaces as CSV", "value": "surfaces.csv"},
        {"text": "Points as CSV", "value": "points.csv"},
        {"text": "Orientations as CSV", "value": "orientations.csv"},
    ],
    # GemPy structures
    # Visualization
    # UI state
    "viewLayout": "singleView",
}

vuetify = {
    "icons": {
        "iconfont": "mdi",
        "values": {
            # common
            "opened": "mdi-chevron-down",
            "closed": "mdi-chevron-up",
            "save": "mdi-database-arrow-down-outline",
            "load": "mdi-database-arrow-up-outline",
            "up": "mdi-arrow-up",
            "down": "mdi-arrow-down",
            "add": "mdi-plus",
            "delete": "mdi-minus",
            "apply": "mdi-check",
            "cancel": "mdi-cancel",
            "pole": "mdi-sign-pole",
            "download": "mdi-content-save-outline",
            # view action
            "resetCamera": "mdi-crop-free",
            "scaleZ": "mdi-arrow-expand-vertical",
            "resetScale": "mdi-focus-field-vertical",
            # control menu
            "addSurface": "mdi-layers-plus",
            "grid": "mdi-grid",
            "fault": "mdi-slash-forward",
            "faults": "mdi-abjad-hebrew",
            "surface": "mdi-rhombus-outline",
            "surfaces": "mdi-layers-outline",
            "onlap": "mdi-wave",
            "onlaps": "mdi-waves",
            "stack": "mdi-chart-timeline-variant",
            "stacks": "mdi-chart-timeline-variant-shimmer",
            "topography": "mdi-image-filter-hdr",
            "point": "mdi-circle",
            "points": "mdi-chart-bubble",
            "orientation": "mdi-compass",
            "orientations": "mdi-math-compass",
            "compute": "mdi-desktop-classic",
            "square": "mdi-square",
            "cube": "mdi-cube-scan",
            # app layout
            "singleView": "mdi-border-all-variant",
            "multiView": "mdi-border-all",
        },
    },
}
