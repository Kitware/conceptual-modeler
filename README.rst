conceptual modeler
==================

Modeling is an iterative process that is rarely correct the first time unless it’s really simple. Typically, we assign input data to a grid (or mesh), but if we need to adjust or change the mesh, then we need to start over from scratch.

The conceptual modeler provides for the graphical definition of structure, properties, and boundary conditions interactively or from prepared data. This tool allows researchers to interactively describe the surface and subsurface system before simulation, integrate raw data from third-party tools they already know how to use, leverage powerful tools from Python for data preparation, and evolve the model as objectives change or their understanding improves of the subsurface by collecting additional data.

The meshes and simulation scenarios are separate from the conceptual modeler and generated in another component.

The conceptual modeler fuses data from multiple sources to create a geometric model utilizing GemPy (https://www.gempy.org/). GemPy is a Python-based, community-driven, open-source geomodeling library. It is capable of constructing complex 3D geological models including various features such as fold structures, fault networks, and unconformities, based on an underlying powerful implicit approach.

Mac M1 Setup
------------------

.. code-block:: console

    brew install pyqt5 gdal

    conda create --name conceptual-modeler python=3.9 -y
    conda activate conceptual-modeler
    conda install -c conda-forge theano -y
    # conda install -c anaconda mkl-service # Not available on arm...
    # conda install -c conda-forge pyqt -y
    conda install -c anaconda numpy -y
    ln -s /opt/homebrew/Cellar/pyqt@5/5.15.6/lib/python3.9/site-packages/PyQt5 .venv/lib/python3.9/site-packages

    pip install -r ./requirements.txt
