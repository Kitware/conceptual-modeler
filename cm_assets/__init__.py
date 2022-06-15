from pathlib import Path

# Compute local path to serve
serve_path = str(Path(__file__).with_name("serve").resolve())

# Serve directory for JS/CSS files
serve = {"__global": serve_path}

# List of CSS files to load (usually from the serve path above)
styles = [
    "__global/assets/style.css",
]
