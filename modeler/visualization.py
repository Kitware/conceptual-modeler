from collections import defaultdict

from vtkmodules.vtkCommonCore import (
    vtkFloatArray, 
    vtkLookupTable, 
    vtkPoints,
)
from vtkmodules.vtkCommonDataModel import (
    vtkCellArray,
    vtkImageData, 
    vtkPolyData,
    vtkTriangle,
)
from vtkmodules.vtkFiltersCore import (
    vtkContourFilter,
    vtkDelaunay2D,
    vtkGlyph3D,
    vtkThreshold,
)
from vtkmodules.vtkFiltersGeometry import (
    vtkDataSetSurfaceFilter,
)
from vtkmodules.vtkFiltersModeling import (
    vtkOutlineFilter,
)
from vtkmodules.vtkFiltersSources import (
    vtkArrowSource,
    vtkSphereSource,
)
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkDataSetMapper,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)
from vtkmodules.vtkRenderingAnnotation import (
    vtkCubeAxesActor,
)

from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch #noqa

import vtkmodules.vtkRenderingOpenGL2 #noqa

CMOCEAN_TOPO = [[0.156102, 0.102608, 0.172722, 1.0],
                [0.161488, 0.108633, 0.183442, 1.0],
                [0.166812, 0.114599, 0.194259, 1.0],
                [0.172070, 0.120513, 0.205186, 1.0],
                [0.177260, 0.126379, 0.216231, 1.0],
                [0.182375, 0.132204, 0.227402, 1.0],
                [0.187413, 0.137992, 0.238706, 1.0],
                [0.192367, 0.143747, 0.250149, 1.0],
                [0.197232, 0.149476, 0.261734, 1.0],
                [0.202003, 0.155183, 0.273466, 1.0],
                [0.206673, 0.160872, 0.285344, 1.0],
                [0.211235, 0.166549, 0.297369, 1.0],
                [0.215682, 0.172220, 0.309540, 1.0],
                [0.220003, 0.177889, 0.321859, 1.0],
                [0.224182, 0.183563, 0.334343, 1.0],
                [0.228216, 0.189249, 0.346959, 1.0],
                [0.232091, 0.194957, 0.359692, 1.0],
                [0.235779, 0.200694, 0.372581, 1.0],
                [0.239276, 0.206471, 0.385562, 1.0],
                [0.242547, 0.212301, 0.398653, 1.0],
                [0.245582, 0.218199, 0.411796, 1.0],
                [0.248331, 0.224182, 0.425003, 1.0],
                [0.250772, 0.230270, 0.438204, 1.0],
                [0.252866, 0.236488, 0.451345, 1.0],
                [0.254568, 0.242864, 0.464356, 1.0],
                [0.255832, 0.249430, 0.477140, 1.0],
                [0.256615, 0.256220, 0.489577, 1.0],
                [0.256873, 0.263268, 0.501525, 1.0],
                [0.256605, 0.270601, 0.512796, 1.0],
                [0.255825, 0.278233, 0.523219, 1.0],
                [0.254598, 0.286156, 0.532637, 1.0],
                [0.253038, 0.294336, 0.540950, 1.0],
                [0.251282, 0.302717, 0.548142, 1.0],
                [0.249468, 0.311235, 0.554277, 1.0],
                [0.247716, 0.319830, 0.559470, 1.0],
                [0.246112, 0.328450, 0.563865, 1.0],
                [0.244722, 0.337055, 0.567603, 1.0],
                [0.243579, 0.345620, 0.570813, 1.0],
                [0.242698, 0.354131, 0.573602, 1.0],
                [0.242095, 0.362574, 0.576065, 1.0],
                [0.241760, 0.370949, 0.578273, 1.0],
                [0.241690, 0.379255, 0.580286, 1.0],
                [0.241878, 0.387491, 0.582154, 1.0],
                [0.242309, 0.395663, 0.583913, 1.0],
                [0.242970, 0.403774, 0.585594, 1.0],
                [0.243846, 0.411829, 0.587222, 1.0],
                [0.244926, 0.419832, 0.588818, 1.0],
                [0.246193, 0.427789, 0.590397, 1.0],
                [0.247631, 0.435705, 0.591971, 1.0],
                [0.249228, 0.443585, 0.593549, 1.0],
                [0.250967, 0.451434, 0.595140, 1.0],
                [0.252835, 0.459257, 0.596747, 1.0],
                [0.254818, 0.467058, 0.598376, 1.0],
                [0.256905, 0.474842, 0.600029, 1.0],
                [0.259083, 0.482613, 0.601706, 1.0],
                [0.261340, 0.490375, 0.603407, 1.0],
                [0.263666, 0.498132, 0.605133, 1.0],
                [0.266052, 0.505887, 0.606881, 1.0],
                [0.268488, 0.513643, 0.608647, 1.0],
                [0.270968, 0.521404, 0.610429, 1.0],
                [0.273486, 0.529172, 0.612224, 1.0],
                [0.276035, 0.536950, 0.614026, 1.0],
                [0.278614, 0.544740, 0.615830, 1.0],
                [0.281219, 0.552545, 0.617632, 1.0],
                [0.283850, 0.560365, 0.619424, 1.0],
                [0.286507, 0.568202, 0.621202, 1.0],
                [0.289194, 0.576059, 0.622958, 1.0],
                [0.291913, 0.583934, 0.624685, 1.0],
                [0.294673, 0.591829, 0.626376, 1.0],
                [0.297480, 0.599744, 0.628025, 1.0],
                [0.300345, 0.607679, 0.629624, 1.0],
                [0.303280, 0.615633, 0.631165, 1.0],
                [0.306300, 0.623605, 0.632641, 1.0],
                [0.309421, 0.631594, 0.634045, 1.0],
                [0.312664, 0.639599, 0.635370, 1.0],
                [0.316048, 0.647616, 0.636607, 1.0],
                [0.319599, 0.655645, 0.637752, 1.0],
                [0.323343, 0.663680, 0.638796, 1.0],
                [0.327310, 0.671720, 0.639734, 1.0],
                [0.331529, 0.679760, 0.640561, 1.0],
                [0.336035, 0.687795, 0.641270, 1.0],
                [0.340864, 0.695820, 0.641857, 1.0],
                [0.346054, 0.703829, 0.642321, 1.0],
                [0.351645, 0.711816, 0.642659, 1.0],
                [0.357676, 0.719774, 0.642872, 1.0],
                [0.364189, 0.727695, 0.642956, 1.0],
                [0.371227, 0.735570, 0.642919, 1.0],
                [0.378828, 0.743390, 0.642768, 1.0],
                [0.387032, 0.751146, 0.642506, 1.0],
                [0.395875, 0.758827, 0.642151, 1.0],
                [0.405388, 0.766422, 0.641715, 1.0],
                [0.415597, 0.773921, 0.641223, 1.0],
                [0.426520, 0.781312, 0.640696, 1.0],
                [0.438163, 0.788586, 0.640169, 1.0],
                [0.450529, 0.795733, 0.639674, 1.0],
                [0.463599, 0.802746, 0.639255, 1.0],
                [0.477347, 0.809617, 0.638954, 1.0],
                [0.491733, 0.816345, 0.638818, 1.0],
                [0.506705, 0.822928, 0.638896, 1.0],
                [0.522200, 0.829370, 0.639235, 1.0],
                [0.538148, 0.835675, 0.639876, 1.0],
                [0.554478, 0.841852, 0.640859, 1.0],
                [0.571112, 0.847911, 0.642217, 1.0],
                [0.587984, 0.853865, 0.643971, 1.0],
                [0.605019, 0.859727, 0.646144, 1.0],
                [0.622168, 0.865510, 0.648740, 1.0],
                [0.639376, 0.871228, 0.651766, 1.0],
                [0.656593, 0.876895, 0.655221, 1.0],
                [0.673793, 0.882521, 0.659096, 1.0],
                [0.690948, 0.888119, 0.663382, 1.0],
                [0.708034, 0.893699, 0.668068, 1.0],
                [0.725036, 0.899269, 0.673139, 1.0],
                [0.741942, 0.904839, 0.678582, 1.0],
                [0.758747, 0.910416, 0.684380, 1.0],
                [0.775447, 0.916005, 0.690518, 1.0],
                [0.792044, 0.921612, 0.696981, 1.0],
                [0.808541, 0.927240, 0.703754, 1.0],
                [0.824944, 0.932893, 0.710822, 1.0],
                [0.841242, 0.938579, 0.718173, 1.0],
                [0.857456, 0.944297, 0.725795, 1.0],
                [0.873599, 0.950045, 0.733675, 1.0],
                [0.889651, 0.955834, 0.741802, 1.0],
                [0.905651, 0.961657, 0.750169, 1.0],
                [0.921585, 0.967521, 0.758765, 1.0],
                [0.937480, 0.973419, 0.767584, 1.0],
                [0.953323, 0.979361, 0.776620, 1.0],
                [0.969149, 0.985336, 0.785870, 1.0],
                [0.984937, 0.991355, 0.795327, 1.0],
                [0.052375, 0.145255, 0.077520, 1.0],
                [0.056226, 0.152346, 0.080403, 1.0],
                [0.060071, 0.159396, 0.083248, 1.0],
                [0.063852, 0.166423, 0.085997, 1.0],
                [0.067565, 0.173431, 0.088641, 1.0],
                [0.071214, 0.180422, 0.091187, 1.0],
                [0.074799, 0.187398, 0.093631, 1.0],
                [0.078322, 0.194362, 0.095978, 1.0],
                [0.081782, 0.201317, 0.098225, 1.0],
                [0.085182, 0.208264, 0.100373, 1.0],
                [0.088525, 0.215204, 0.102426, 1.0],
                [0.091810, 0.222139, 0.104384, 1.0],
                [0.095038, 0.229072, 0.106245, 1.0],
                [0.098210, 0.236003, 0.108010, 1.0],
                [0.101329, 0.242933, 0.109682, 1.0],
                [0.104393, 0.249865, 0.111259, 1.0],
                [0.107448, 0.256791, 0.112744, 1.0],
                [0.110626, 0.263695, 0.114100, 1.0],
                [0.113953, 0.270574, 0.115290, 1.0],
                [0.117477, 0.277425, 0.116291, 1.0],
                [0.121300, 0.284232, 0.117094, 1.0],
                [0.125534, 0.290978, 0.117668, 1.0],
                [0.130388, 0.297632, 0.117991, 1.0],
                [0.136178, 0.304140, 0.118042, 1.0],
                [0.143482, 0.310393, 0.117905, 1.0],
                [0.153052, 0.316219, 0.118066, 1.0],
                [0.164744, 0.321554, 0.119583, 1.0],
                [0.177122, 0.326605, 0.122838, 1.0],
                [0.189319, 0.331554, 0.127327, 1.0],
                [0.201147, 0.336469, 0.132581, 1.0],
                [0.212620, 0.341372, 0.138326, 1.0],
                [0.223781, 0.346270, 0.144400, 1.0],
                [0.234683, 0.351167, 0.150712, 1.0],
                [0.245365, 0.356062, 0.157202, 1.0],
                [0.255861, 0.360957, 0.163828, 1.0],
                [0.266254, 0.365846, 0.170365, 1.0],
                [0.276638, 0.370720, 0.176604, 1.0],
                [0.287012, 0.375582, 0.182545, 1.0],
                [0.297380, 0.380433, 0.188175, 1.0],
                [0.307739, 0.385278, 0.193506, 1.0],
                [0.318088, 0.390119, 0.198539, 1.0],
                [0.328430, 0.394959, 0.203279, 1.0],
                [0.338764, 0.399799, 0.207730, 1.0],
                [0.349092, 0.404640, 0.211899, 1.0],
                [0.359416, 0.409484, 0.215794, 1.0],
                [0.369739, 0.414332, 0.219424, 1.0],
                [0.380063, 0.419185, 0.222799, 1.0],
                [0.390390, 0.424041, 0.225929, 1.0],
                [0.400722, 0.428903, 0.228825, 1.0],
                [0.411063, 0.433770, 0.231497, 1.0],
                [0.421414, 0.438641, 0.233957, 1.0],
                [0.431778, 0.443518, 0.236215, 1.0],
                [0.442155, 0.448400, 0.238282, 1.0],
                [0.452549, 0.453286, 0.240168, 1.0],
                [0.462962, 0.458178, 0.241877, 1.0],
                [0.473396, 0.463074, 0.243410, 1.0],
                [0.483851, 0.467975, 0.244787, 1.0],
                [0.494328, 0.472882, 0.246015, 1.0],
                [0.504833, 0.477794, 0.247079, 1.0],
                [0.515361, 0.482711, 0.248007, 1.0],
                [0.525918, 0.487634, 0.248792, 1.0],
                [0.536503, 0.492562, 0.249438, 1.0],
                [0.547117, 0.497497, 0.249954, 1.0],
                [0.557764, 0.502437, 0.250332, 1.0],
                [0.568440, 0.507385, 0.250586, 1.0],
                [0.579152, 0.512338, 0.250708, 1.0],
                [0.589898, 0.517299, 0.250702, 1.0],
                [0.600678, 0.522266, 0.250576, 1.0],
                [0.611498, 0.527241, 0.250312, 1.0],
                [0.622353, 0.532223, 0.249931, 1.0],
                [0.633268, 0.537205, 0.249403, 1.0],
                [0.644249, 0.542177, 0.248839, 1.0],
                [0.655324, 0.547128, 0.248215, 1.0],
                [0.666466, 0.552068, 0.247596, 1.0],
                [0.677704, 0.556985, 0.246951, 1.0],
                [0.689038, 0.561876, 0.246304, 1.0],
                [0.700471, 0.566740, 0.245699, 1.0],
                [0.712013, 0.571569, 0.245187, 1.0],
                [0.723693, 0.576344, 0.244836, 1.0],
                [0.735517, 0.581050, 0.244916, 1.0],
                [0.747526, 0.585630, 0.246201, 1.0],
                [0.757750, 0.590850, 0.254791, 1.0],
                [0.763582, 0.598154, 0.269506, 1.0],
                [0.768501, 0.605966, 0.284134, 1.0],
                [0.773107, 0.613968, 0.298553, 1.0],
                [0.777565, 0.622075, 0.312774, 1.0],
                [0.781922, 0.630259, 0.326860, 1.0],
                [0.786205, 0.638505, 0.340848, 1.0],
                [0.790443, 0.646800, 0.354744, 1.0],
                [0.794657, 0.655133, 0.368546, 1.0],
                [0.798834, 0.663510, 0.382316, 1.0],
                [0.803009, 0.671916, 0.396012, 1.0],
                [0.807153, 0.680364, 0.409705, 1.0],
                [0.811304, 0.688839, 0.423346, 1.0],
                [0.815460, 0.697342, 0.436954, 1.0],
                [0.819606, 0.705880, 0.450567, 1.0],
                [0.823757, 0.714448, 0.464169, 1.0],
                [0.827920, 0.723044, 0.477760, 1.0],
                [0.832091, 0.731670, 0.491355, 1.0],
                [0.836253, 0.740332, 0.505012, 1.0],
                [0.840445, 0.749016, 0.518680, 1.0],
                [0.844665, 0.757725, 0.532363, 1.0],
                [0.848918, 0.766457, 0.546062, 1.0],
                [0.853212, 0.775212, 0.559766, 1.0],
                [0.857544, 0.783992, 0.573488, 1.0],
                [0.861915, 0.792797, 0.587231, 1.0],
                [0.866325, 0.801629, 0.600999, 1.0],
                [0.870782, 0.810486, 0.614785, 1.0],
                [0.875293, 0.819368, 0.628582, 1.0],
                [0.879850, 0.828277, 0.642411, 1.0],
                [0.884460, 0.837214, 0.656261, 1.0],
                [0.889132, 0.846177, 0.670127, 1.0],
                [0.893856, 0.855169, 0.684031, 1.0],
                [0.898654, 0.864185, 0.697937, 1.0],
                [0.903510, 0.873232, 0.711886, 1.0],
                [0.908445, 0.882305, 0.725843, 1.0],
                [0.913453, 0.891406, 0.739827, 1.0],
                [0.918535, 0.900536, 0.753841, 1.0],
                [0.923702, 0.909694, 0.767876, 1.0],
                [0.928960, 0.918879, 0.781926, 1.0],
                [0.934312, 0.928091, 0.795994, 1.0],
                [0.939765, 0.937330, 0.810076, 1.0],
                [0.945319, 0.946597, 0.824179, 1.0],
                [0.950980, 0.955892, 0.838298, 1.0],
                [0.956756, 0.965214, 0.852428, 1.0],
                [0.962652, 0.974564, 0.866567, 1.0],
                [0.968665, 0.983942, 0.880726, 1.0],
                [0.974789, 0.993352, 0.894923, 1.0]]

def areEqual(arr1, arr2, n, m):
 
    # If lengths of array are not
    # equal means array are not equal
    if (n != m):
        return False
 
    # Create a defaultdict count to
    # store counts
    count = defaultdict(int)
 
    # Store the elements of arr1
    # and their counts in the dictionary
    for i in arr1:
        count[i] += 1
 
    # Traverse through arr2 and compare
    # the elements and its count with
    # the elements of arr1
    for i in arr2:
 
        # Return false if the element
        # is not in arr2 or if any element
        # appears more no. of times than in arr1
        if (count[i] == 0):
            return False
 
        # If element is found, decrement
        # its value in the dictionary
        else:
            count[i] -= 1
 
    # Return true if both arr1 and
    # arr2 are equal
    return True

class Representation:
    Points = 0
    Wireframe = 1
    Surface = 2
    SurfaceWithEdges = 3

def hextorgb(hcolor):
    h = hcolor.lstrip('#')
    rstring = h[0:2]
    r = int(rstring, 16)
    gstring = h[2:4]
    g = int(gstring, 16)
    bstring = h[4:6]
    b = int(bstring, 16)
    return [r/255.0, g/255.0, b/255.0]

def vector_magnitude(vector):
    sum = 0
    for i in range(len(vector)):
        sum = vector[i]*vector[i] + sum    
    return pow(sum,0.5)

class ViewView:
    def __init__(self, name="default"):
        self.name = name
        self.renderer = vtkRenderer()
        self.renderWindow = vtkRenderWindow()
        self.renderWindow.AddRenderer(self.renderer)
        self.renderWindowInteractor = vtkRenderWindowInteractor()
        self.renderWindowInteractor.SetRenderWindow(self.renderWindow)
        self.renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

        self.axes = vtkCubeAxesActor()
        self._scene = {}

        self.renderer.SetBackground(0.2, 0.4, 0.6)
        self.camera.SetViewUp(0.0, 0.0, 1.0)
        self.camera.SetPosition(50.0, 50.0 - 1.0, 50.0)
        self.camera.SetFocalPoint(50.0, 50.0, 50.0)

    def getRenderWindow(self):
        return self.renderWindow

    def resetCamera(self):
        self.renderer.ResetCamera()

    @property
    def camera(self):
        return self.renderer.GetActiveCamera()

    def add(self, name, source):
        if name in self._scene:
            print(f"Trying to add name({name}) twice in {self.name}")
            return None

        actor = vtkActor()
        mapper = vtkDataSetMapper()
        lut = vtkLookupTable()
        lut.SetTableRange(0.0, 1.0)
        lut.SetNumberOfTableValues(2)
        lut.SetNumberOfColors(2)
        lut.Build()
        lut.SetTableValue(0, 1.0, 1.0, 1.0, 1.0)
        lut.SetTableValue(1, 0.0, 0.0, 0.0, 1.0)
        if source.IsA("vtkDataSet"):
            mapper.SetInputData(source)
        else:
            mapper.SetInputConnection(source.GetOutputPort())
        mapper.SetLookupTable(lut)
        mapper.SetScalarRange(0.0, 1.0)
        mapper.SetScalarModeToUseCellData()
        mapper.SetColorModeToMapScalars()
        actor.SetMapper(mapper)
        self.renderer.AddActor(actor)
        item = {
            "name": name,
            "source": source,
            "mapper": mapper,
            "actor": actor,
        }
        self._scene[name] = item
        return item

    def add_topography_surface(self, point_list):
        f = [0.0]
        points = vtkPoints()
        vertices = vtkCellArray()
        field = vtkFloatArray()
        field.SetName("elevation")
        field.SetNumberOfComponents(1);
        for p in point_list:
            f[0] = p[2]
            field.InsertNextTuple(f)
            point_id = points.InsertNextPoint(p)
            vertices.InsertNextCell(1)
            vertices.InsertCellPoint(point_id)
        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetVerts(vertices)
        polydata.GetPointData().AddArray(field)
        polydata.GetPointData().SetActiveScalars('elevation')
        polydata.Modified()

        delaunay = vtkDelaunay2D()
        delaunay.SetInputData(polydata)
        delaunay.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(delaunay.GetOutputPort())

        lut = vtkLookupTable()
        lut.SetTableRange(0.0, 1.0)
        lut.SetNumberOfTableValues(256)
        lut.SetNumberOfColors(256)
        lut.Build()
        for i in range(256):
            lut.SetTableValue(i, CMOCEAN_TOPO[i])

        mapper.SetLookupTable(lut)
        mapper.SetScalarRange(-11034.0, 8848.0)
        mapper.SetScalarModeToUsePointData()
        mapper.SetColorModeToMapScalars()
        mapper.Update()

        actor = vtkActor()
        actor.SetMapper(mapper)

        self.renderer.AddActor(actor)

        name = "topography_surface"
        item = {
            "name": name,
            "source": delaunay,
            "mapper": mapper,
            "actor": actor,
        }
        self._scene[name] = item
        return item

    def add_topography_contours(self, point_list):
        f = [0.0]
        points = vtkPoints()
        vertices = vtkCellArray()
        field = vtkFloatArray()
        field.SetName("elevation")
        field.SetNumberOfComponents(1);
        for p in point_list:
            f[0] = p[2]
            field.InsertNextTuple(f)
            point_id = points.InsertNextPoint(p)
            vertices.InsertNextCell(1)
            vertices.InsertCellPoint(point_id)
        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetVerts(vertices)
        polydata.GetPointData().AddArray(field)
        polydata.GetPointData().SetActiveScalars('elevation')
        polydata.Modified()

        delaunay = vtkDelaunay2D()
        delaunay.SetInputData(polydata)
        delaunay.Update()

        field_range = field.GetRange()

        contour = vtkContourFilter()
        contour.SetInputConnection(delaunay.GetOutputPort())
        contour.GenerateValues(10, field_range)
        contour.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(contour.GetOutputPort())

        lut = mapper.GetLookupTable()
        lut.SetHueRange(0.666, 0.0)
        lut.SetSaturationRange(1.0, 1.0)
        lut.SetValueRange(1.0, 1.0)
        lut.Build()

        mapper.SetScalarVisibility(True)
        mapper.SetScalarRange(field_range)
        mapper.Update()

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetLineWidth(3)

        self.renderer.AddActor(actor)

        name = "topography_contours"
        item = {
            "name": name,
            "source": contour,
            "mapper": mapper,
            "actor": actor,
        }
        self._scene[name] = item
        return item
    
    def add_surface_points(self, surface, color, radius, point_list):
        points = vtkPoints()
        vertices = vtkCellArray()
        for p in point_list:
            point_id = points.InsertNextPoint(p)
            vertices.InsertNextCell(1)
            vertices.InsertCellPoint(point_id)
        points_polydata = vtkPolyData()
        points_polydata.SetPoints(points)
        points_polydata.SetVerts(vertices)
        points_polydata.Modified()

        sphereSource = vtkSphereSource()
        sphereSource.SetRadius(radius)
        sphereSource.Update()

        glyph3D = vtkGlyph3D()
        glyph3D.SetSourceConnection(sphereSource.GetOutputPort())
        glyph3D.SetInputData(points_polydata)
        glyph3D.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(glyph3D.GetOutputPort())
        mapper.Update()

        actor = vtkActor()
        actor.SetMapper(mapper)
        rgbcolor = hextorgb(color)
        actor.GetProperty().SetColor(rgbcolor[0],rgbcolor[1],rgbcolor[2])

        self.renderer.AddActor(actor)

        name = surface+"_points"
        item = {
            "name": name,
            "source": glyph3D,
            "mapper": mapper,
            "actor": actor,
        }
        self._scene[name] = item
        return item

    def add_surface_orientations(self, surface, color, radius, orientation_list):
        points = vtkPoints()
        vertices = vtkCellArray()
        direction = vtkFloatArray()
        direction.SetName('direction')
        direction.SetNumberOfComponents(3)
        direction.SetNumberOfTuples(len(orientation_list))
        magnitude = vtkFloatArray()
        magnitude.SetName('magnitude')
        magnitude.SetNumberOfTuples(len(orientation_list))
        index = 0
        for o in orientation_list:
            p = [o[0], o[1], o[2]]
            d = [o[3], o[4], o[5]]
            point_id = points.InsertNextPoint(p)
            vertices.InsertNextCell(1)
            vertices.InsertCellPoint(point_id)
            direction.SetTuple(index, d)
            m = vector_magnitude(d)
            magnitude.SetTuple1(index, m)
            index += 1

        points_polydata = vtkPolyData()
        points_polydata.SetPoints(points)
        points_polydata.SetVerts(vertices)
        points_polydata.GetPointData().AddArray(direction)
        points_polydata.GetPointData().SetActiveVectors('direction')
        points_polydata.GetPointData().AddArray(magnitude)
        points_polydata.GetPointData().SetActiveScalars('magnitude')
        points_polydata.Modified()

        arrowSource = vtkArrowSource()
        arrowSource.SetTipRadius(0.5)
        arrowSource.SetShaftRadius(0.25)
        arrowSource.Update()

        glyph3D = vtkGlyph3D()
        glyph3D.SetSourceConnection(arrowSource.GetOutputPort())
        glyph3D.SetInputData(points_polydata)
        glyph3D.SetVectorModeToUseVector()
        glyph3D.SetScaleFactor(radius*2.0)
        glyph3D.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(glyph3D.GetOutputPort())
        mapper.Update()

        actor = vtkActor()
        actor.SetMapper(mapper)
        rgbcolor = hextorgb(color)
        actor.GetProperty().SetColor(rgbcolor[0],rgbcolor[1],rgbcolor[2])
        self.renderer.AddActor(actor)

        name = surface+"_orientations"
        item = {
            "name": name,
            "source": glyph3D,
            "mapper": mapper,
            "actor": actor,
        }
        self._scene[name] = item
        return item

    def add_surface(self, surface, color, vertices, simplices):
        surface_points = vtkPoints()
        surface_polydata = vtkPolyData()
        surface_triangles = vtkCellArray()
        for v in vertices:
            surface_points.InsertNextPoint(v)
        for s in simplices:
            triangle = vtkTriangle()
            triangle.GetPointIds().SetId(0, s[0])
            triangle.GetPointIds().SetId(1, s[1])
            triangle.GetPointIds().SetId(2, s[2])
            surface_triangles.InsertNextCell(triangle)

        surface_polydata.SetPoints(surface_points)
        surface_polydata.SetPolys(surface_triangles)
        surface_polydata.Modified()

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(surface_polydata)
        mapper.Update()

        actor = vtkActor()
        actor.SetMapper(mapper)
        rgbcolor = hextorgb(color)
        actor.GetProperty().SetColor(rgbcolor[0],rgbcolor[1],rgbcolor[2])

        self.renderer.AddActor(actor)
        
        name = surface+"_surface"
        item = {
            "name": name,
            "source": surface_polydata,
            "mapper": mapper,
            "actor": actor,
        }
        self._scene[name] = item
        return item

    def add_skin(self, source, surface, color, valuerange):
        thresholdfilter = vtkThreshold()
        thresholdfilter.SetInputData(source)
        thresholdfilter.ThresholdBetween(valuerange[0], valuerange[1])
        thresholdfilter.Update()

        surfacefilter = vtkDataSetSurfaceFilter()
        surfacefilter.SetInputConnection(thresholdfilter.GetOutputPort())
        surfacefilter.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(surfacefilter.GetOutput())
        mapper.ScalarVisibilityOff()
        mapper.Update()

        actor = vtkActor()
        actor.SetMapper(mapper)
        rgbcolor = hextorgb(color)
        actor.GetProperty().SetColor(rgbcolor[0],rgbcolor[1],rgbcolor[2])

        self.renderer.AddActor(actor)
        
        name = surface+"_skin"
        item = {
            "name": name,
            "source": surfacefilter,
            "mapper": mapper,
            "actor": actor,
        }
        self._scene[name] = item
        return item

    def add_cube_axes(self, source):
        bounds = source.GetBounds()
        self.axes.SetBounds( bounds[0], bounds[1], bounds[2], bounds[3], bounds[4], bounds[5])
        self.axes.SetCamera(self.renderer.GetActiveCamera())
        self.axes.SetXLabelFormat("%6.1f")
        self.axes.SetYLabelFormat("%6.1f")
        self.axes.SetZLabelFormat("%6.1f")
        self.axes.SetFlyModeToOuterEdges()
        self.renderer.AddActor(self.axes)

    def update_cube_axes(self, source):
        bounds = source.GetBounds()
        self.axes.SetBounds( bounds[0], bounds[1], bounds[2], bounds[3], bounds[4], bounds[5])

    def get_cube_axes_visibility(self):
        self.axes.GetVisibility()

    def set_cube_axes_visibility(self, visibility):
        self.axes.SetVisibility(visibility)

    def get(self, name):
        return self._scene.get(name, None)

    def get_list(self):
        print(self._scene)

    def remove(self, name):
        item = self.get(name)
        if item:
            self.renderer.RemoveActor(item["actor"])
            self._scene.pop(name)


class VtkViewer:
    def __init__(self, app, subsurface):
        self._app = app
        self._subsurface = subsurface
        self._current_actors = []
        self._computed = False
        self._temp_pipelines = []
        self._slice_x = 0
        self._slice_y = 0
        self._slice_z = 0

        self._grid = vtkImageData()
        self._litho_field = vtkFloatArray()
        self._litho_field.SetName("litho")
        self._grid.GetCellData().SetScalars(self._litho_field)
        self._filter_threshold = vtkThreshold()
        self._filter_threshold.SetInputData(self._grid)
        self._filter_threshold.ThresholdByUpper(0.0)
        #  Outline
        self._filter_outline = vtkOutlineFilter()
        self._filter_outline.SetInputData(self._grid)

        # View
        self.update_grid(dirtying=False)

        self._view = ViewView("view3D")
        self._view.add("outline", self._filter_outline)
        self._view.add("grid", self._filter_threshold)
        self._current_actors.append("grid")
        self._current_actors.append("topography")
        self.set_representation("grid", Representation.SurfaceWithEdges)
        self.set_opacity("grid", 0.2)
        self.set_visibility("grid", False)
        self._view.add_cube_axes(self._grid)
        self._view.resetCamera()

        # Append visualization state in application
        self.dirty()

    def getRenderWindow(self, view_name):
        return self._view.getRenderWindow()

    def resetCamera(self):
        self._view.resetCamera()
    
    def update_xfig(self, **kwargs):
        return self._subsurface.update_xfig(**kwargs)

    def update_yfig(self, **kwargs):
        return self._subsurface.update_yfig(**kwargs)

    def update_zfig(self, **kwargs):
        return self._subsurface.update_zfig(**kwargs)

    @property
    def resolutions(self):
        dims = self._grid.GetDimensions()
        return (dims[0] - 1, dims[1] - 1, dims[2] - 1)

    @property
    def extents(self):
        resolutions = self.resolutions
        origin = self._grid.GetOrigin()
        spacing = self._grid.GetSpacing()
        return (origin[0], origin[0] + spacing[0] * resolutions[0], 
                origin[1], origin[1] + spacing[1] * resolutions[1], 
                origin[2], origin[2] + spacing[2] * resolutions[2])

    @property
    def state(self):
        bounds = self._grid.GetBounds()
        resolutions = self.resolutions
        pipelines_html = self.pipelines_html()
        return {
            "pipelines": pipelines_html,
            "opacity": [],
            "visibility": [],
            "slice_x": self._slice_x,
            "slice_y": self._slice_y,
            "slice_z": self._slice_z,
            "interaction2D": [
                {
                    "button": 1,
                    "action": "Pan",
                },
                {
                    "button": 2,
                    "action": "Zoom",
                },
                {
                    "button": 3,
                    "action": "Zoom",
                    "scrollEnabled": True,
                },
                {
                    "button": 1,
                    "action": "ZoomToMouse",
                    "shift": True,
                },
                {
                    "button": 1,
                    "action": "ZoomToMouse",
                    "alt": True,
                },
            ],
        }

    def dirty(self, *args):
        state = self.state
        for name in args:
            if name in state:
                self._app.push_state(name, state[name])
            else:
                print(f"Unable to dirty missing key {name}")

        # Push all if no args provided
        if len(args) == 0:
            for name in state:
                self._app.push_state(name, state[name])

    def get_ordered_surfaces(self):
        ordered_surfaces = []
        stacks = self._subsurface.state_handler.stacks.ids
        stacks.reverse()
        for stack in stacks:
            stack_object = self._subsurface.state_handler.find_stack_by_id(stack)
            surfaces = stack_object.surfaces.ids
            surfaces.reverse()
            ordered_surfaces.extend(surfaces)
        return ordered_surfaces

    def pipelines_html(self):
        self._temp_pipelines = []
        # Add grid
        pipeline_counter = self.add_grid_pipeline(1)
        # Add topography
        topology_pipeline_id = pipeline_counter
        pipeline_counter = self.add_topography_pipeline(topology_pipeline_id)
        pipeline_counter = self.add_topography_surface_pipeline(pipeline_counter, topology_pipeline_id)
        pipeline_counter = self.add_topography_contours_pipeline(pipeline_counter, topology_pipeline_id)
        # Add surfaces except basement
        if self._computed:
            ordered_surfaces = self.get_ordered_surfaces()
            # remove basement from list
            ordered_surfaces.remove('Surface_1')
            for surfaceid in ordered_surfaces:
                surface = self._subsurface.state_handler.find_surface_by_id(surfaceid)
                base_pipeline_id = pipeline_counter
                pipeline_counter = self.add_base_pipeline(base_pipeline_id, surface)
                pipeline_counter = self.add_skin_pipeline(pipeline_counter, surface, base_pipeline_id)
                pipeline_counter = self.add_surface_pipeline(pipeline_counter, surface, base_pipeline_id)
                pipeline_counter = self.add_points_pipeline(pipeline_counter, surface, base_pipeline_id)
                pipeline_counter = self.add_orientations_pipeline(pipeline_counter, surface, base_pipeline_id)
        # Add basement
        surface = self._subsurface.state_handler.find_surface_by_id('Surface_1')
        basement_pipeline_id = pipeline_counter
        pipeline_counter = self.add_base_pipeline(basement_pipeline_id, surface)
        pipeline_counter = self.add_skin_pipeline(pipeline_counter, surface, basement_pipeline_id)
        return self._temp_pipelines

    def add_grid_pipeline(self, uniqueid):
        grid_pipeline = {
            "uniqueid": uniqueid,
            "name": "grid", 
            "color": "#e0e0e0", 
            "pipeline": "grid",
            "parent": 0,
            "actions": []
        }
        self.add_pipeline_parent(grid_pipeline)
        return uniqueid + 1

    def add_topography_pipeline(self, uniqueid):
        topography_pipeline = {
            "uniqueid": uniqueid,
            "name": "topography", 
            "color": "#4e342e", 
            "pipeline": "topography",
            "parent": 0,
            "actions": ["collapsable"]
        }
        self.add_pipeline_parent(topography_pipeline)
        return uniqueid + 1

    def add_topography_surface_pipeline(self, uniqueid, parent):
        topography_surface_pipeline = {
            "uniqueid": uniqueid,
            "name": "surface", 
            "color": "#4e342e", 
            "pipeline": "topography_surface",
            "parent": parent
        }
        if topography_surface_pipeline["pipeline"] in self._current_actors:
            self.add_pipeline_child(topography_surface_pipeline)
            return uniqueid + 1
        else:
            return uniqueid

    def add_topography_contours_pipeline(self, uniqueid, parent):
        topography_contours_pipeline = {
            "uniqueid": uniqueid,
            "name": "contours", 
            "color": "#4e342e", 
            "pipeline": "topography_contours",
            "parent": parent
        }
        if topography_contours_pipeline["pipeline"] in self._current_actors:
            self.add_pipeline_child(topography_contours_pipeline)
            return uniqueid + 1
        else:
            return uniqueid

    def add_base_pipeline(self, uniqueid, surface):
        base_pipeline = {
            "uniqueid": uniqueid,
            "name": surface.name, 
            "color": surface.color, 
            "pipeline": surface.name,
            "parent": 0,
            "actions": ["collapsable"]
        }
        self.add_pipeline_parent(base_pipeline)
        return uniqueid + 1

    def add_skin_pipeline(self, uniqueid, surface, parent):
        skin_pipeline = {
            "uniqueid": uniqueid,
            "name": "skin", 
            "color": surface.color, 
            "pipeline": surface.id+"_skin",
            "parent": parent
        }
        if skin_pipeline["pipeline"] in self._current_actors:
            self.add_pipeline_child(skin_pipeline)
            return uniqueid + 1
        else:
            return uniqueid

    def add_surface_pipeline(self, uniqueid, surface, parent):
        surface_pipeline = {
            "uniqueid": uniqueid,
            "name": "surface", 
            "color": surface.color, 
            "pipeline": surface.id+"_surface",
            "parent": parent
        }
        if surface_pipeline["pipeline"] in self._current_actors:
            self.add_pipeline_child(surface_pipeline)
            return uniqueid + 1
        else:
            return uniqueid

    def add_points_pipeline(self, uniqueid, surface, parent):
        points_pipeline = {
            "uniqueid": uniqueid,
            "name": "points", 
            "color": surface.color, 
            "pipeline": surface.id+"_points",
            "parent": parent
        }
        if points_pipeline["pipeline"] in self._current_actors:
            self.add_pipeline_child(points_pipeline)
            return uniqueid + 1
        else:
            return uniqueid

    def add_orientations_pipeline(self, uniqueid, surface, parent):
        orientations_pipeline = {
            "uniqueid": uniqueid,
            "name": "orientations", 
            "color": surface.color, 
            "pipeline": surface.id+"_orientations",
            "parent": parent
        }
        if orientations_pipeline["pipeline"] in self._current_actors:
            self.add_pipeline_child(orientations_pipeline)
            return uniqueid + 1
        else:
            return uniqueid

    def add_pipeline_parent(self, item):
        self._temp_pipelines.append({
                            "id": str(item["uniqueid"]), 
                            "parent": str(item["parent"]), 
                            "visible": self.get_pipeline_visibility(item["uniqueid"], item["pipeline"]), 
                            "name": item["name"], 
                            "color": item["color"], 
                            "pipeline": item["pipeline"],
                            "collapsed": self.get_pipeline_collapsed(item["uniqueid"], item["pipeline"]),
                            "actions": item["actions"],
                        })

    def add_pipeline_child(self, item):
        self._temp_pipelines.append({
                                "id": str(item["uniqueid"]), 
                                "parent": str(item["parent"]), 
                                "visible": self.get_pipeline_visibility(item["uniqueid"], item["pipeline"]), 
                                "name": item["name"], 
                                "color": item["color"], 
                                "pipeline": item["pipeline"],
                                "collapsed": self.get_pipeline_collapsed(item["uniqueid"], item["pipeline"]),
                            })

    def get_pipeline_visibility(self, id, pipeline):
        return self._app.pipeline_manager.get_visible(id, pipeline)
    
    def set_visibility(self, name, on_off):
        item = self._view.get(name)
        if item:
            item.get("actor").SetVisibility(on_off)
            return 1
        else:
            print(name, " is a group of pipelines")
            return 0

    def get_pipeline_collapsed(self, id, pipeline):
        return self._app.pipeline_manager.get_collapsed(id, pipeline)

    def set_cube_axes_visibility(self, visibility):
        if self._view.get_cube_axes_visibility() == visibility:
            return 0
        else:
            self._view.set_cube_axes_visibility(visibility)
            return 1

    def set_opacity(self, pipeline, value):
        item = self._view.get(pipeline)
        if item:
            property = item.get("actor").GetProperty()
            if property.GetOpacity() == value:
                return 0
            else:
                property.SetOpacity(value)
                return 1
        return 0

    def get_opacity(self, pipeline):
        item = self._view.get(pipeline)
        if item:
            property = item.get("actor").GetProperty()
            return property.GetOpacity()
        return 0.0

    def set_representation(self, pipeline, mode):
        item = self._view.get(pipeline)
        if item:
            property = item.get("actor").GetProperty()
            representation = property.GetRepresentation()
            edges = property.GetEdgeVisibility()
            current_mode = representation
            if current_mode == Representation.Surface and edges:
                current_mode = Representation.SurfaceWithEdges
            if current_mode == mode:
                return 0
            else:
                if mode == Representation.Points:
                    property.SetRepresentationToPoints()
                    property.SetPointSize(5)
                    property.EdgeVisibilityOff()
                    return 1
                elif mode == Representation.Wireframe:
                    property.SetRepresentationToWireframe()
                    property.SetPointSize(1)
                    property.EdgeVisibilityOff()
                    return 1
                elif mode == Representation.Surface:
                    property.SetRepresentationToSurface()
                    property.SetPointSize(1)
                    property.EdgeVisibilityOff()
                    return 1
                elif mode == Representation.SurfaceWithEdges:
                    property.SetRepresentationToSurface()
                    property.SetPointSize(1)
                    property.EdgeVisibilityOn()
                    return 1
        return 0

    def get_representation(self, pipeline):
        item = self._view.get(pipeline)
        if item:
            property = item.get("actor").GetProperty()
            representation = property.GetRepresentation()
            edges = property.GetEdgeVisibility()
            current_mode = representation
            if current_mode == Representation.Surface and edges:
                current_mode = Representation.SurfaceWithEdges
            return current_mode
        return Representation.Surface

    def compute(self, computing=True, dirtying=True):
        current_actors = []
        current_actors.append("grid")
        current_actors.append("topography")
        
        if "topography_surface" in self._current_actors:
            current_actors.append("topography_surface")
        if "topography_contours" in self._current_actors:
            current_actors.append("topography_contours")

        for name in self._current_actors:
            if name not in ["grid", "topography", "topography_surface", "topography_contours"]:
                self._view.remove(name)
        
        self._current_actors = current_actors

        self.update_cube_axes()

        if computing:
            self._computed = True
            self.update_lithography()
            self.update_skin()
            self.update_surface()
            self.update_surface_points()
            self.update_surface_orientations()
            if dirtying:
                self.dirty("pipelines")

    def update_grid(self, dirtying=True):
        grid = self._subsurface._state_handler.grid
        resolution = grid.resolution
        extent = grid.extent
        resolutions = self.resolutions
        extents = self.extents
        if (areEqual(resolution, resolutions, len(resolution), len(resolutions)) and 
            areEqual(extent, extents, len(extent), len(extents))):
            return 0
        else:
            self._grid.SetDimensions(
                resolution[0] + 1, resolution[1] + 1, resolution[2] + 1
            )
            self._grid.SetSpacing(
                (extent[1] - extent[0]) / (resolution[0]),
                (extent[3] - extent[2]) / (resolution[1]),
                (extent[5] - extent[4]) / (resolution[2]),
            )
            self._grid.SetOrigin(
                extent[0],
                extent[2],
                extent[4],
            )
            self._litho_field.SetNumberOfTuples(self._grid.GetNumberOfCells())
            self._litho_field.Fill(0)

            # Update slice origin
            self._slice_x = int(resolution[0] * 0.5)
            self._slice_y = int(resolution[1] * 0.5)
            self._slice_z = int(resolution[2] * 0.5)

            if dirtying:
                self.dirty("slice_x", "slice_y", "slice_z")
            return 1

    def update_lithography(self):
        litho = self._subsurface._geo_model.solutions.lith_block
        blank = self._subsurface._geo_model._grid.regular_grid.mask_topo
        i_max, j_max, k_max = self.resolutions
        if litho.size == i_max * j_max * k_max:
            self._litho_field.Fill(0)
            lithography = litho.reshape(i_max, j_max, k_max)
            if blank.size == i_max * j_max * k_max:
                blanking = blank.reshape(i_max, j_max, k_max)
                index = 0
                for k in range(k_max):
                    for j in range(j_max):
                        for i in range(i_max):
                            if blanking[i, j, k]:
                                self._litho_field.SetTuple1(index, -1)
                            else:
                                self._litho_field.SetTuple1(index, lithography[i, j, k])
                            index += 1
            else:
                index = 0
                for k in range(k_max):
                    for j in range(j_max):
                        for i in range(i_max):
                            self._litho_field.SetTuple1(index, lithography[i, j, k])
                            index += 1
            self.update_lut()
            self._litho_field.Modified()
            self._filter_threshold.Update()
            self.field_ready = True

    def update_lut(self):
        item = self._view.get("grid")
        colors = self._subsurface._geo_model.surfaces.colors.colordict
        surfaces = self.get_ordered_surfaces()
        scalarMin = 0.0
        scalarMax = len(surfaces)
        lut = vtkLookupTable()
        lut.SetTableRange(scalarMin, scalarMax)
        lut.SetNumberOfTableValues(len(surfaces) + 1)
        lut.SetNumberOfColors(len(surfaces) + 1)
        lut.Build()
        lut.SetTableValue(0, 1.0, 1.0, 1.0, 1.0)
        for i in range(1,len(surfaces) + 1):
            rgbcolor = hextorgb(colors[surfaces[i-1]])
            lut.SetTableValue(i, rgbcolor[0], rgbcolor[1], rgbcolor[2], 1.0)
        item["mapper"].SetScalarRange(scalarMin, scalarMax)
        item["mapper"].SetLookupTable(lut)
        item["mapper"].SetScalarModeToUseCellData()
        item["mapper"].SetColorModeToMapScalars()
        item["mapper"].ScalarVisibilityOn()
        item["mapper"].Update()

    def update_cube_axes(self):
        self._view.update_cube_axes(self._grid)

    def update_topography(self, dirtying=True):
        self._view.remove("topography_surface")
        self._view.remove("topography_contours")
        points = self._subsurface._geo_model._grid.topography.values
        name = "topography_surface"
        if "topography_contours" not in self._current_actors:
            self._current_actors.append(name)
        self._view.add_topography_surface(points)
        self.set_visibility(name, False)
        name = "topography_contours"
        if "topography_contours" not in self._current_actors:
            self._current_actors.append(name)
        self._view.add_topography_contours(points)
        self.set_visibility(name, False)
        if dirtying:
            self.dirty("pipelines")

    def update_surface_points(self):
        spacing = self._grid.GetSpacing()
        radius = min(spacing)
        surfaces = self.get_ordered_surfaces()
        # remove basement from list
        surfaces.remove('Surface_1')
        for surface in surfaces:
            surface_filter = self._subsurface._geo_model._surface_points.df.surface == surface
            points = self._subsurface._geo_model._surface_points.df[surface_filter][["X", "Y", "Z"]].values
            surface_filter = self._subsurface._geo_model._surfaces.df.surface == surface
            the_surface_df = self._subsurface._geo_model._surfaces.df[surface_filter]
            color = the_surface_df.color.tolist()[0]
            name = surface+"_points"
            self._current_actors.append(name)
            self._view.add_surface_points(surface, color, radius, points)
            self.set_visibility(name, False)

    def update_surface_orientations(self):
        spacing = self._grid.GetSpacing()
        radius = min(spacing)
        surfaces = self.get_ordered_surfaces()
        # remove basement from list
        surfaces.remove('Surface_1')
        for surface in surfaces:
            surface_filter = self._subsurface._geo_model._orientations.df.surface == surface
            orientations = self._subsurface._geo_model._orientations.df[surface_filter][["X", "Y", "Z", "G_x", "G_y", "G_z"]].values
            surface_filter = self._subsurface._geo_model._surfaces.df.surface == surface
            the_surface_df = self._subsurface._geo_model._surfaces.df[surface_filter]
            color = the_surface_df.color.tolist()[0]
            name = surface+"_orientations"
            self._current_actors.append(name)
            self._view.add_surface_orientations(surface, color, radius, orientations)
            self.set_visibility(name, False)

    def update_surface(self):
        surfaces = self.get_ordered_surfaces()
        # remove basement from list
        surfaces.remove('Surface_1')
        for surface in surfaces:
            surface_filter = self._subsurface._geo_model._surfaces.df.surface == surface
            the_surface_df = self._subsurface._geo_model._surfaces.df[surface_filter]
            vertices = the_surface_df.vertices.values.tolist()[0]
            simplices = the_surface_df.edges.values.tolist()[0]
            color = the_surface_df.color.tolist()[0]
            name = surface+"_surface"
            self._current_actors.append(name)
            self._view.add_surface(surface, color, vertices, simplices)
            self.set_visibility(name, False)
            self.set_opacity(name, 0.2)

    def update_skin(self):
        surfaces = self.get_ordered_surfaces()
        for surface in surfaces:
            surface_object = self._subsurface._state_handler.find_surface_by_id(surface)
            if surface_object.stack.feature.value != "Fault":
                surface_filter = self._subsurface._geo_model._surfaces.df.surface == surface
                the_surface_df = self._subsurface._geo_model._surfaces.df[surface_filter]
                value = the_surface_df.id.tolist()[0]
                color = the_surface_df.color.tolist()[0]
                valuerange = [float(value) - 0.5, float(value) + 0.5]
                name = surface+"_skin"
                self._current_actors.append(name)
                self._view.add_skin(self._grid, surface, color, valuerange)
                self.set_visibility(name, False)
                self.set_opacity(name, 0.2)
