DEFAULT_NEW_STACK = {"name": "", "feature": "Erosion"}
DEFAULT_NEW_SURFACE = {"name": ""}

DEFAULT_NEW = {
    "Stack": DEFAULT_NEW_STACK,
    "Surface": DEFAULT_NEW_SURFACE,
}

shared_state = {
    # SubSurface client models
    "stackNew": DEFAULT_NEW_STACK,
    "surfaceNew": DEFAULT_NEW_SURFACE,
    # Handling data injestion
    "importShow": False,
    "importFile": None,
    "importType": None,
    "importTypes": [
        {"text": "Full Conceptual Modeler state", "value": "model.json"},
        {"text": "Grid as CSV", "value": "grid.csv"},
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
            # view action
            "resetCamera": "mdi-crop-free",
            "scaleZ": "mdi-arrow-expand-vertical",
            "resetScale": "mdi-focus-field-vertical",
            # control menu
            "addSurface": "mdi-layers-plus",
            "grid": "mdi-grid",
            "fault": "mdi-slash-forward",
            "faults": "mdi-abjad-hebrew",
            "surface": "mdi-texture-box",
            "surfaces": "mdi-layers-outline",
            "onlap": "mdi-wave",
            "onlaps": "mdi-waves",
            "stack": "mdi-chart-timeline-variant",
            "stacks": "mdi-chart-timeline-variant-shimmer",
            "topography": "mdi-image-filter-hdr",
            "point": "mdi-record-circle-outline",
            "points": "mdi-chart-bubble",
            "orientation": "mdi-compass-outline",
            "compute": "mdi-desktop-classic",
            # app layout
            "singleView": "mdi-border-all-variant",
            "multiView": "mdi-border-all",
        },
    },
}
