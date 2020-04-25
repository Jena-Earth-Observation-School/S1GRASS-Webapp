import os
import sys
from osgeo import osr
from grass_session import Session, get_grass_gisbase
import grass.script as grass
import grass.script.setup as gsetup


def setup_grass(version=None, path=None, name=None, crs=None):
    """
    bla
    :param version:
    :param path:
    :param name:
    :param crs:
    :return:
    """
    if version is None:
        version = 'grass78'
    if path is None:
        path = './grass/'
        if not os.path.exists(path):
            os.makedirs(path)
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
    os.environ['PROJ_LIB'] = 'C:/Program Files/GRASS GIS 7.8/share/proj'

    # User-defined settings
    gisdb = path
    mapset = 'PERMANENT'

    # Open a GRASS session and create mapset if it doesn't exist already
    with Session(gisdb=gisdb,
                 location=name,
                 create_opts='EPSG:' + crs) as session:
        pass

    # Launch session
    gsetup.init(gisbase, gisdb, name, mapset)
    print('Current GRASS GIS 7 environment:')
    print(grass.gisenv())


def get_footprint(ras_name, out_path=None):
    """
    bla
    :param ras_name:
    :param out_path:
    :return:
    """
    if "grass.script" not in sys.modules:
        setup_grass()
        print("Beware: PyGRASS was loaded with standard settings!")

    if out_path is None:
        out_path = './out/'
        if not os.path.exists(out_path):
            os.makedirs(out_path)

    out_name = out_path + ras_name + ".geojson"

    # Set computational region
    grass.run_command('g.region', raster=ras_name)

    # Create temporary raster file with all values set to 1
    grass.mapcalc("ras_tmp = (abs($a) >= 1) * 1", a=ras_name, overwrite=True)

    # Create temporary vector file from "ras_tmp"
    grass.run_command("r.to.vect", input="ras_tmp", output="vec_tmp",
                      type="area")

    # Create convex hull from vec_tmp
    grass.run_command("v.hull", input="vec_tmp", output="vec_tmp_hull",
                      overwrite=True)

    # Export as GeoJSON
    grass.run_command("v.out.ogr", input="vec_tmp_hull",
                      output=out_name, format="GeoJSON", overwrite=True)

    # Remove tmp-files from mapset
    grass.run_command("g.remove", type="raster", name="ras_tmp", flags="f")
    grass.run_command("g.remove", type="vector", name="vec_tmp", flags="f")
    grass.run_command("g.remove", type="vector", name="vec_tmp_hull",
                      flags="f")

    return print("Done! :)")


"""
os.environ['GRASSBIN'] = "grass78"

PERMANENT=Session()
PERMANENT.open(gisdb="D:\\grass_test",
               location="just_a_test_bro", mapset="PERMANENT", create_opts="")
"""

setup_grass(name='Test', crs='32629')

###############################################################################

data_path = "./data/test_data"
file1 = "./data/test_data" \
        "/S1A__IW___A_20150107T182611_147_VV_grd_mli_norm_geo_db.tif"
file2 = "./data/test_data" \
        "/S1A__IW___A_20150303T181753_74_VV_grd_mli_norm_geo_db.tif"

# Check if any raster files have already been imported
for rast in grass.list_strings(type='rast'):
    print(rast)

# Import files
grass.run_command("r.in.gdal", input=file1, output="test1", flags="e")
grass.run_command("r.in.gdal", input=file2, output="test2")

# Print basic info
grass.run_command("r.info", map="test1")

# Test footprint generation
grass.run_command('g.region', raster='test1')

grass.mapcalc("ras_tmp = (abs($a) >= 1) * 1", a="test2", overwrite=True)

grass.run_command("r.to.vect", input="ras_tmp", output="vec_tmp",
                  type="area", overwrite=True)

grass.run_command("v.hull", input="vec_tmp", output="vec_tmp_hull",
                  overwrite=True)

grass.run_command("v.out.ogr", input="vec_tmp_hull",
                  output="./out/test_hull_out2.geojson",
                  format="GeoJSON", overwrite=True)
