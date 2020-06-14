from config import Grass
from flask_app import db
from flask_app.models import Scene, GrassOutput

import os
import sys
from pathlib import Path
from grass_session import Session, get_grass_gisbase
import grass.script as gscript
import grass.script.setup as gsetup


def grass_main(scenes, epsg):
    """This workflow first sets up GRASS if the corresponding directories
    can't be found in Grass.path. Then each scene in the list provided by
    the parameter 'scenes' will be imported into the GRASS Location that was
    set up using the most common original CRS of the data and then
    reprojected and imported into another GRASS Location that was set up
    in WGS84.
    :param scenes: List of scenes that was created while running db_main().
    Each scene is listed as the full path.
    :param epsg: Most common CRS in the dataset. Also created while running
    db_main().
    """
    ## Setup two GRASS Locations if it hasn't been done already. One with the
    ## most common original CRS and another in WGS84 for displaying in the
    ## webapp.
    location_orig = os.path.join(Grass.path, f'GRASS_db_{epsg}')
    location_4326 = os.path.join(Grass.path, 'Grass_db_4326')

    if not os.path.isdir(location_orig):
        setup_grass(crs=epsg)
    if not os.path.isdir(location_4326):
        setup_grass(crs='4326')

    ## Import scenes into GRASS Location in the original CRS
    start_grass_session(crs=epsg)
    for scene in scenes:
        import_to_grass(scene)

    ## Reproject scenes by importing into GRASS Location in WGS84. Each
    ## scene will then be exported as a Cloud Optimized GeoTiff and a
    ## dictionary with information to store in the database will be generated.
    start_grass_session(crs='4326')
    info_dict = {}
    for scene in scenes:
        reproject_scene(scene=scene, crs_in=epsg)
        cog_path = export_cog(scene=scene, crs='4326')

        info_dict[scene] = {'description': 'export_cog_4326',
                            'filepath': cog_path}

    ## Add information from info_dict to the database
    add_grass_output_to_db(info_dict)


def setup_grass(version=None, path=None, crs=None, name=None):

    if version is None:
        version = 'grass78'
    if path is None:
        path = Grass.path
    if crs is None:
        raise ValueError("Please provide a valid EPSG code.")
    if name is None:
        name = f'GRASS_db_{crs}'

    ## General GRASS setup
    os.environ['GRASSBIN'] = version
    gisbase = get_grass_gisbase()
    os.environ['GISBASE'] = gisbase
    sys.path.append(os.path.join(os.environ['GISBASE'], 'bin'))
    sys.path.append(os.path.join(os.environ['GISBASE'], 'lib'))
    sys.path.append(os.path.join(os.environ['GISBASE'], 'scripts'))
    sys.path.append(os.path.join(os.environ['GISBASE'], 'etc', 'python'))
    os.environ['PROJ_LIB'] = os.path.join(os.environ['GISBASE'], 'share\\proj')

    ## User-defined settings
    gisdb = path
    mapset = 'PERMANENT'

    ## Open a GRASS session and create mapset if it doesn't exist already
    with Session(gisdb=gisdb,
                 location=name,
                 create_opts='EPSG:' + crs) as session:
        pass


def start_grass_session(crs=None):
    """Starts a GRASS session with a GRASS Location that already exists and
    was set up with the provided CRS.
    :param crs: EPSG code (e.g. '32629') [Str]
    :return: GRASS session
    """
    location = os.path.join(Grass.path, f'GRASS_db_{crs}')
    if not os.path.isdir(location):
        raise ValueError(f"A GRASS Location in EPSG {crs} has not been set "
                         f"up yet. Please run 'setup_grass(crs='{crs}')' "
                         f"first")
    if crs is None:
        raise ValueError("Please provide a valid EPSG code.")

    gisbase = get_grass_gisbase()
    gisdb = Grass.path
    name = f'GRASS_db_{crs}'
    mapset = 'PERMANENT'

    gsetup.init(gisbase, gisdb, name, mapset)
    print('Current GRASS GIS 7 environment:')
    print(gscript.gisenv())


def import_to_grass(scene):
    """Initial import of scenes into the GRASS location of original
    projection (e.g. EPSG 32629)
    :param scene: full path e.g.
    'D:\\GEO450_data\\S1A__IW___A_20150320T182611_147_VV_grd_mli_norm_geo_db.tif'
    """
    ## Define filename
    base = os.path.basename(scene)
    scene_name = base[:-len(Path(base).suffix)]

    ## Run GRASS Import module
    try:
        gscript.run_command("r.in.gdal", input=scene, output=scene_name,
                            flags="e", quiet=True)
    except:
        pass


def reproject_scene(scene, crs_in=None):
    """Reproject scenes from CRS that is defined by the parameter 'crs_in' and
    into the CRS of the GRASS session that is currently is running. Also
    export the scene as a Cloud Optimized GeoTiff.
    :param scene: full path e.g.
    'D:\\GEO450_data\\S1A__IW___A_20150320T182611_147_VV_grd_mli_norm_geo_db.tif'
    :param crs_in: Source CRS (e.g. '32629') [Str]
    :return: Scene imported and reprojected into destination CRS.
    """
    if crs_in is None:
        raise ValueError("Please provide a valid EPSG code for 'crs_in'.")

    ## Define filename
    base = os.path.basename(scene)
    scene_name = base[:-len(Path(base).suffix)]

    ## Parse r.proj to get information about the bounds of the scene once
    ## projected into the destination projection
    region = gscript.parse_command('r.proj', input=scene_name,
                                   location=f'GRASS_db_{crs_in}',
                                   mapset="PERMANENT", flags="g", quiet=True,
                                   parse=(gscript.parse_key_val, {'sep': '=',
                                                                  'vsep': ' '})
                                   )

    ## Use parsed information to set the region
    gscript.run_command('g.region', n=region['n'], s=region['s'],
                        w=region['w'], e=region['e'],
                        rows=region['rows'], cols=region['cols'])

    ## Import & reproject
    gscript.run_command('r.proj', input=scene_name,
                        location=f'GRASS_db_{crs_in}',
                        mapset='PERMANENT', memory=500, quiet=True)


def export_cog(scene, crs):
    """Export as a Cloud Optimized GeoTiff.
    :param scene: full path e.g.
    'D:\\GEO450_data\\S1A__IW___A_20150320T182611_
    147_VV_grd_mli_norm_geo_db.tif' [Str]
    :param crs: CRS of the current GRASS session. [Str]
    :return: Path to the exported file. [Str]
    """
    ## Create output directory if it doesn't exist already
    out_dir = os.path.join(Grass.path, f'output\\cog_{crs}')
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    ## Define filename and full output path
    base = os.path.basename(scene)
    scene_name = base[:-len(Path(base).suffix)]
    scene_name_new = f'{scene_name}_{crs}.tif'
    out_path = os.path.join(out_dir, scene_name_new)

    ## Run GRASS output module
    gscript.run_command("r.out.gdal", input=scene_name,
                        output=out_path, format='GTiff',
                        createopt="TILED=YES,COMPRESS=DEFLATE",
                        overviews=4, quiet=True)

    return out_path


def add_grass_output_to_db(info_dict):
    """

    :param info_dict:
    :return:
    """

    info = info_dict

    for scene in info.keys():

        s = Scene.query.filter_by(filepath=scene)

        go = GrassOutput(description=info[scene]['description'],
                         filepath=info[scene]['filepath'],
                         s1_scene=s)
        db.session.add(go)
        db.session.commit()


"""
import subprocess
from osgeo import osr

def get_footprint(raster):
    \"""Uses GRASS to calculate the exact footprint (not extent!) of a raster.
    :param raster: full path e.g.
    'D:\\GEO450_data\\S1A__IW___A_20150320T182611_147_VV_grd_mli_norm_geo_db.tif'
    :return: Path of the generated GeoJSON file
    \"""
    ## Create output folder if it doesn't exist already.
    out_path = os.path.join(Grass.path, 'output\\footprints')
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    ## Define filenames and -paths.
    ras_name = os.path.basename(raster)
    ras_name = ras_name[:-len(Path(ras_name).suffix)]
    ras_name_suffix = ras_name + '.geojson'
    ras_name_foot = ras_name + "_footprint"
    out_name = os.path.join(out_path, ras_name_suffix)

    ## Check if for the given scene a geojson-file already exists. If so,
    ## then skip calculation. Else calculate footprint and save geojson-file.
    file_list = os.listdir(out_path)
    if any(ras_name in file for file in file_list):
        print("Footprint for", ras_name, "already exists.")
        return out_name

    else:
        try:
            ## Set computational region
            gscript.run_command('g.region', raster=ras_name)
        except:
            ## Import file, then set computational region and continue
            gscript.run_command("r.in.gdal", input=raster, output=ras_name,
                                flags="e")
            gscript.run_command('g.region', raster=ras_name)

        ## Create temporary raster file with all values set to 1
        gscript.mapcalc("ras_tmp = (abs($a) > 0) * 1", a=ras_name, overwrite=True)

        ## Create temporary vector file from "ras_tmp"
        gscript.run_command("r.to.vect", input="ras_tmp", output="vec_tmp",
                          type="area")

        ## Create convex hull from vec_tmp
        gscript.run_command("v.hull", input="vec_tmp",
                          output=ras_name_foot,
                          overwrite=True)

        ## Export as GeoJSON
        gscript.run_command("v.out.ogr", input=ras_name_foot,
                          output=out_name, format="GeoJSON", overwrite=True)

        ## Remove tmp-files from mapset
        gscript.run_command("g.remove", type="raster", name="ras_tmp", flags="f")
        gscript.run_command("g.remove", type="vector", name="vec_tmp", flags="f")
        gscript.run_command("g.remove", type="vector", name=ras_name_foot,
                          flags="f")

        return out_name


def reproject_geojson(geojson_path, epsg):
    \"""All calculations in GRASS are done in the original projection but 
WGS84
    is usually needed for the web (e.g. in Leaflet maps). It's easier to
    just reproject into EPSG 4326 for web-stuff right away instead
    of having this problem later on. And it's also way easier to just do it
    with a simple ogr2ogr command instead of working with multiple GRASS
    locations in different projections and creating a mess...

    :param geojson_path: Path to GeoJSON file that is supposed to be
    reprojected. In the process of generating the database, the output of
    get_footprint() is used as the input path.
    :param epsg: EPSG code of the input file.
    :return: Path of the reprojected GeoJSON file
    \"""

    ## Define filenames and -paths
    foot_in = geojson_path
    base = os.path.basename(geojson_path)
    foot_out = base[:-len(Path(base).suffix)]
    foot_out = foot_out + '_4326.geojson'
    foot_out = os.path.join(os.path.dirname(geojson_path), foot_out)

    ## Define ogr2ogr command
    ogr_call = str(f'ogr2ogr -f "GeoJSON" {foot_out} {foot_in} -s_srs EPSG:'
                   f'{epsg} -t_srs EPSG:4326')

    ## Execute ogr2ogr command
    subprocess.call(ogr_call, shell=True)

    ## Delete original file
    os.remove(foot_in)

    ## Return new path
    return foot_out

"""
