import os
import sys
from osgeo import osr
from grass_session import Session, get_grass_gisbase


def setup_grass(version=None, path=None, name=None, crs=None):
    """
    bla
    """

    try:
        import grass.script as gscript
        import grass.script.setup as gsetup
    except ImportError:
        raise ImportError(
            "GRASS GIS doesn't seem to be installed.")

    if version is None:
        version = 'grass78'
    if path is None:
        path = './grass/'
    if name is None:
        name = 'my_awesome_grass_db'

    if crs is None:
        crs = '4326'
    else:
        if osr.SpatialReference().ImportFromEPSG(int(crs)) == 6:
            raise ValueError("The provided EPSG code is not valid.")

    # General GRASS setup
    os.environ['GRASSBIN'] = version
    gisbase = get_grass_gisbase()
    os.environ['GISBASE'] = gisbase
    sys.path.append(os.path.join(os.environ['GISBASE'], 'bin'))
    sys.path.append(os.path.join(os.environ['GISBASE'], 'lib'))
    sys.path.append(os.path.join(os.environ['GISBASE'], 'scripts'))
    sys.path.append(os.path.join(os.environ['GISBASE'], 'etc', 'python'))
    # os.environ['PROJ_LIB'] = 'C:\\OSGeo4W64\\share\\proj'

    # User-defined settings
    gisdb = path
    location = name
    mapset = 'PERMANENT'

    # Open a GRASS session and create mapset if it doesn't exist already
    with Session(gisdb=gisdb,
                 location=location,
                 create_opts='EPSG:' + crs) as session:
        pass

    # Launch session
    gsetup.init(gisbase, gisdb, location, mapset)
    print('Current GRASS GIS 7 environment:')
    print(gscript.gisenv())


def get_footprint(ras_name):
    if "grass.script" not in sys.modules:
        setup_grass()
        print("Beware: PyGRASS was loaded with standard settings!")

    # Change from raster name (ras_name) to raster file and import using
    # "r.in.gdal" first ?

    # Create temporary raster file with all values set to 1
    gscript.mapcalc("ras_tmp = (abs($a) >= 1) * 1", a=ras_name, overwrite=True)

    # Create temporary vector file from "ras_tmp"
    gscript.run_command("r.to.vect", input="ras_tmp", output="vec_tmp",
                        type="area")

    # Create convex hull from vec_tmp
    gscript.run_command("v.hull", input="vec_tmp", output="vec_tmp_hull",
                        overwrite=True)

    # Output... ?


setup_grass(name='Spain_Donana', crs='32629')

###############################################################################

data_path = "./data/test_data"
file1 = "./data/test_data" \
        "/S1A__IW___A_20150107T182611_147_VV_grd_mli_norm_geo_db.tif"
file2 = "./data/test_data" \
        "/S1A__IW___A_20150303T181753_74_VV_grd_mli_norm_geo_db.tif"

# Check if any raster files have already been imported
for rast in gscript.list_strings(type='rast'):
    print(rast)

# Import files
# For next session... FILES ARE NOT IMPORTED PROPERLY!
gscript.run_command("r.in.gdal", input=file1, output="test1")
gscript.run_command("r.in.gdal", input=file2, output="test2")

# Print basic info
gscript.run_command("r.info", map="test2")

# Test footprint generation
gscript.mapcalc("ras_tmp = (abs($a) >= 1) * 1", a="test1", overwrite=True)
gscript.run_command("r.to.vect", input="ras_tmp", output="vec_tmp",
                    type="area", overwrite=True)
gscript.run_command("v.hull", input="vec_tmp", output="vec_tmp_hull",
                    overwrite=True)
