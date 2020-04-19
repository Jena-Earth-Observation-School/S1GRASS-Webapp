import os
import sys
from grass_session import Session, get_grass_gisbase
import grass.script as gscript
import grass.script.setup as gsetup

def setup_grass(version=None, dir=None, name=None, crs=None):
    """
    bla
    """
    if version is None:
        version = 'grass78'
    if dir is None:
        dir = './grass/'
    if name is None:
        name = 'my_awesome_grass_db'
    if crs is None:
        crs = '4326'

    # General GRASS setup
    grassbin = version
    os.environ['GRASSBIN'] = grassbin
    gisbase = get_grass_gisbase()
    os.environ['GISBASE'] = gisbase
    sys.path.append(os.path.join(os.environ['GISBASE'], 'bin'))
    sys.path.append(os.path.join(os.environ['GISBASE'], 'lib'))
    sys.path.append(os.path.join(os.environ['GISBASE'], 'scripts'))
    sys.path.append(os.path.join(os.environ['GISBASE'], 'etc', 'python'))
    #os.environ['PROJ_LIB'] = 'C:\\OSGeo4W64\\share\\proj'

    # User-defined settings
    gisdb = dir
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


setup_grass(name='Spain_Donana', crs='32629')

##################################################################################

data_path = "./data/test_data"
test_file = "./data/test_data" \
            "/S1A__IW___A_20150107T182611_147_VV_grd_mli_norm_geo_db.tif "

# Check if any raster files have already been imported
for rast in gscript.list_strings(type = 'rast'):
    print(rast)

map = "test_ras"

gscript.run_command("r.in.gdal", input=test_file, output=map)
gscript.run_command("r.info", map=map)

