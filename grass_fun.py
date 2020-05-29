from config import Grass

import os
import sys
from pathlib import Path
from osgeo import osr
from grass_session import Session, get_grass_gisbase
import grass.script as gscript
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
        path = Grass.path
    if name is None:
        name = 'GRASS_db'
    if crs is None:
        crs = '4326'
    else:  # not 100% sure about this, but seems to work fine...
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
    os.environ['PROJ_LIB'] = os.path.join(os.environ['GISBASE'], 'share\\proj')

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
    print(gscript.gisenv())


def get_footprint(raster, out_path=None):
    """
    bla
    :param raster: full path e.g.
    'D:\\GEO450_data\\S1A__IW___A_20150320T182611_147_VV_grd_mli_norm_geo_db.tif'
    :return: Footprint as a GeoJSON file located in out_path\footprints
    """

    if out_path is None:
        out_path = os.path.join(Grass.path, 'output\\footprints')
        if not os.path.exists(out_path):
            os.makedirs(out_path)

    ras_name = os.path.basename(raster)
    ras_name = ras_name[:-len(Path(ras_name).suffix)]
    ras_name_suffix = ras_name + '.geojson'
    ras_name_foot = ras_name + "_footprint"
    out_name = os.path.join(out_path, ras_name_suffix)

    try:
        # Set computational region
        gscript.run_command('g.region', raster=ras_name)
    except:
        # Import file, then set computational region and continue
        import_raster(raster, ras_name)
        gscript.run_command('g.region', raster=ras_name)

    # Create temporary raster file with all values set to 1
    gscript.mapcalc("ras_tmp = (abs($a) > 0) * 1", a=ras_name, overwrite=True)

    # Create temporary vector file from "ras_tmp"
    gscript.run_command("r.to.vect", input="ras_tmp", output="vec_tmp",
                      type="area")

    # Create convex hull from vec_tmp
    gscript.run_command("v.hull", input="vec_tmp",
                      output=ras_name_foot,
                      overwrite=True)

    # Export as GeoJSON
    gscript.run_command("v.out.ogr", input=ras_name_foot,
                      output=out_name, format="GeoJSON", overwrite=True)

    # Remove tmp-files from mapset
    gscript.run_command("g.remove", type="raster", name="ras_tmp", flags="f")
    gscript.run_command("g.remove", type="vector", name="vec_tmp", flags="f")
    gscript.run_command("g.remove", type="vector", name=ras_name_foot,
                      flags="f")

    return out_name


def import_raster(path, name):

    gscript.run_command("r.in.gdal", input=path, output=name, flags="e")

