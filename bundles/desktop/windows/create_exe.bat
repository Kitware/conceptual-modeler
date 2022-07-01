pyinstaller ^
  --hidden-import vtkmodules.all ^
  --collect-data pywebvue ^
  --onefile ^
  --windowed ^
  --icon conceptual-modeler.ico ^
  .\run.py
