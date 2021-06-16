# conceptual modeler

## Setup

```
# Python environment (3.8.5)
python3.8 -m venv py-env
source ./py-env/bin/activate

# Install gdal
sudo apt-get install gdal-bin
sudo apt-get install libgdal-dev
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
ogrinfo --version

# Make sure the version reported by `ogrinfo` match gdal in requirements.txt
pip install -r ./server/requirements.txt

# Download the wheel that match your system on https://gitlab.kitware.com/vtk/vtk/-/pipeline_schedules
pip install ~/vtk-9.0.20210616.dev0-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
```

## Run application

```
# Python process
python ./app.py --port 1234

# open http://localhost:1234/
```
