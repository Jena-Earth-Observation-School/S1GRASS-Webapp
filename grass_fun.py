from config import Grass
from flask_app.models import Scene, Metadata

from grass_session import Session, get_grass_gisbase
import grass.script as gscript
import grass.script.setup as gsetup
from progress.bar import Bar
import os
import sys
import numpy as np
from pathlib import Path
from osgeo import ogr
from osgeo import osr
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import file_html


def grass_main(scenes, epsg):
    """This workflow will be triggered every time new scenes are added to the
    database. If it's triggered for the first time, a GRASS project will be
    set up first using the most common CRS / EPSG code of the dataset in a
    subdirectory of the provided data directory. Then a GRASS session is
    started and each scene in the list provided by the parameter 'scenes' will
    be imported and an average raster will be calculated and exported to
    display in the main map of the webapp.

    :param scenes: List of scenes that was created while running db_main().
    Each scene is listed as the full path.
    :param epsg: Most common CRS in the dataset. Also created while running
    db_main().
    """
    ## Setup GRASS if it hasn't been done already
    location_orig = os.path.join(Grass.path, f'Grass_db_{epsg}')
    if not os.path.isdir(location_orig):
        print(f"~~ Setting up 'Grass_db_{epsg}'...")
        setup_grass(crs=epsg)

    ## Start GRASS session and import scenes
    start_grass_session(crs=epsg)
    import_to_grass(scenes)

    ## Create average raster
    create_avg_raster()


def setup_grass(version=None, path=None, crs=None, name=None):
    """Sets up a GRASS project.

    :param version: GRASS version (e.g. 'grass78') [str]
    :param path: Path where Grass should be set up. Default is a
    subdirectory of the provided data directory. [str]
    :param crs: EPSG code (e.g. '32629') to set the projection. The main
    workflow (see grass_main()) uses the most common CRS of all files in a
    dataset. [str]
    :param name: Name of the GRASS project. Default is 'GRASS_db_{crs}'. [str]

    :returns: New GRASS project that can be started using
    start_grass_session().
    """
    if crs is None:
        raise ValueError("Please provide a valid EPSG code.")

    ## Set parameter defaults
    if version is None:
        version = 'grass78'
    if path is None:
        path = Grass.path
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

    ## Open a GRASS session and create mapset if it doesn't exist already
    with Session(gisdb=gisdb,
                 location=name,
                 create_opts='EPSG:' + crs) as session:
        pass

    return print(f"~~ The GRASS project '{name}' was successfully created.")


def start_grass_session(crs=None, name=None, quiet=False):
    """Starts a GRASS session, provided it has been setup before (see
    setup_grass()). This will only search for GRASS projects located in
    Grass.path, which by default is a subdirectory of the provided data
    directory!

    :param crs: EPSG code the GRASS project was set up in (e.g.
    '32629'). This parameter is used to identify automatically generated
    GRASS projects that contain the EPSG code in their name. For other
    projects, the parameter 'name' can be used instead. [str]
    :param name: If the GRASS project cannot be identified with the EPSG
    code it was set up in, then the name of the project can be passed with
    this parameter instead (e.g. 'my-awesome-grass-project') [str]
    :param quiet:

    :returns: GRASS session
    """
    ## (There's probably a better way to do the following if-statements,
    ## but I guess it works...)
    if crs is None and name is None:
        raise ValueError("Please provide either a valid EPSG code using the "
                         "parameter 'crs' or the name of a GRASS project by "
                         "using the parameter 'name'.")

    if crs is not None and name is None:
        location = os.path.join(Grass.path, f'GRASS_db_{crs}')
        if not os.path.isdir(location):
            raise ValueError(
                f"A GRASS Location with the name 'GRASS_db_{crs}' has not "
                f"been set up yet.")
        project_name = f'GRASS_db_{crs}'

    elif name is not None and crs is None:
        location = os.path.join(Grass.path, name)
        if not os.path.isdir(location):
            raise ValueError(
                f"A GRASS Location with name the '{name}' has not been set "
                f"up yet.")
        project_name = name
    else:
        raise ValueError("The parameters 'crs' and 'name' cannot be passed "
                         "at the same time.")

    gisbase = get_grass_gisbase()
    gisdb = Grass.path
    project_name = project_name
    mapset = 'PERMANENT'

    gsetup.init(gisbase, gisdb, project_name, mapset)
    if not quiet:
        print(f"~~ Current GRASS GIS environment: \n {gscript.gisenv()}")


def import_to_grass(scenes):
    """Import of multiple scenes into the currently active GRASS session.

    :param scenes: List of scenes that should be imported. Each entry in
    the list is a full path (e.g.
    'D:\\GEO450_data\\S1A__IW___A_20150320T182611_147_VV_grd_mli_norm_geo_db
    .tif')

    :returns: Newly imported scenes in the GRASS session.
    """

    if len(scenes) > 30:
        print(f"~~ {len(scenes)} scenes will be imported to the current "
              f"GRASS project. Grab a coffee, this might take a few minutes..."
              )

    bar = Bar('Importing', max=len(scenes))
    for scene in scenes:
        ## Define filename
        base = os.path.basename(scene)
        scene_name = base[:-len(Path(base).suffix)]

        ## Run GRASS Import module
        gscript.run_command("r.in.gdal", input=scene, output=scene_name,
                            flags="e", quiet=True)
        bar.next()
    bar.finish()


def create_avg_raster():
    """Important part of the main GRASS workflow. An average
    raster of all scenes in the database is created to display on the main map
    of the webapp. This file will be updated if new scenes have been added
    to the database.

    :returns: 'avg_raster.tif' as a Cloud-Optimized-Geotiff
    """
    print("~~ Creating average raster:")

    ## Define filename and path of the output
    filename = 'avg_raster'
    out_path = os.path.join(Grass.path_out, f'{filename}.tif')

    ## Get all scenes currently stored in the database
    all_scenes = Scene.query.all()

    ## List basename of all scenes
    scenes = []
    for s in all_scenes:
        base = os.path.basename(s.filepath)
        scenes.append(base[:-len(Path(base).suffix)])

    ## Set computational region
    gscript.run_command('g.region', raster=scenes)

    ## Use r.series to create aggregation of all scenes
    gscript.run_command('r.series', input=scenes,
                        output=filename, method='average',
                        overwrite=True)

    ## Rescale to range from 1 to 255 (0 is going to be used for nodata values)
    gscript.run_command('r.rescale', input=filename,
                        output=f'{filename}_255',
                        to='1,255', overwrite=True)

    ## Modify color table
    gscript.run_command('r.colors', map=f'{filename}_255',
                        color='viridis', flags='e')

    gscript.run_command("r.out.gdal",
                        input=f'{filename}_255',
                        output=out_path, format='GTiff',
                        createopt="TILED=YES,COMPRESS=DEFLATE",
                        overviews=5, quiet=False, nodata=0, overwrite=True)


def export_cog(scene):
    """Export a scene as a Cloud Optimized GeoTiff.

    :param scene: full path e.g.
    'D:\\GEO450_data\\S1A__IW___A_20150320T182611_
    147_VV_grd_mli_norm_geo_db.tif' [str]

    :return out_path: Path to the exported file. [str]
    """
    ## Create output directory if it doesn't exist already
    out_dir = Grass.path_out

    ## Define filename and full output path
    base = os.path.basename(scene)
    scene_name = base[:-len(Path(base).suffix)]
    out_path = os.path.join(out_dir, scene_name)

    ## Get nodata value of the file from the database
    s = Scene.query.filter_by(filepath=scene).first()
    meta = s.meta.all()
    nodata_val = float(meta[0].nodata)

    ## Run GRASS output module
    gscript.run_command("r.out.gdal", input=scene_name,
                        output=out_path, format='GTiff',
                        createopt="TILED=YES,COMPRESS=DEFLATE",
                        nodata=nodata_val, overviews=3, quiet=False,
                        flags="m")

    return out_path


def transform_coord(lat, lng, proj):
    """Transforms leaflet map coordinates from WGS84/EPSG:4326 into the
    the projection of the GRASS project.

    :param lat: Latitude coordinate. [str or float]
    :param lng: Longitude coordinate. [str or float]
    :param proj: Projection / EPSG code to transform into. [str or int]

    :return coord_out: Transformed coordinates (x, y). [str]
    """

    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)

    target = osr.SpatialReference()
    if type(proj) is str:
        target.ImportFromEPSG(int(proj))
    else:
        target.ImportFromEPSG(proj)

    transform = osr.CoordinateTransformation(source, target)

    point = ogr.CreateGeometryFromWkt(f"POINT ({lat} {lng})")
    point.Transform(transform)

    x_coord = point.GetX()
    y_coord = point.GetY()

    coord_out = f"{x_coord},{y_coord}"

    return coord_out


def get_timeseries(coordinate):
    """Uses the r.what module in GRASS GIS to extract a timeseries for a
    given coordinate.

    :param coordinate: Output of transform_coord(). Location to generate
    timeseries for. Must be in the same projection as the GRASS project. [str]

    :return values_list: List of extracted values.
    :return dates_list: List of dates associated with values_list.
    """
    ## Get all scenes in database
    all_scenes = Scene.query.all()

    ## List basename of all scenes
    scenes = []
    for s in all_scenes:
        base = os.path.basename(s.filepath)
        scenes.append(base[:-len(Path(base).suffix)])

    ## Set computational region
    gscript.run_command('g.region', raster=scenes)

    ## Query all scenes using r.what
    values = gscript.parse_command('r.what', map=scenes,
                                   coordinates=coordinate,
                                   null_value='nan',
                                   separator='comma')
    ## Format output
    values = list(values)[0]
    values = values.split(",")
    values_list = values[3:]
    values_list = [np.nan if x == 'nan' else float(x) for x in values_list]

    ## Get list of dates from database for the x-axis
    dates_list = [date for (date,) in Scene.query.with_entities(
        Scene.date).all()]

    return values_list, dates_list


def create_plot(latitude, longitude, projection):
    """Uses get_timeseries() to extract a timeseries for a given location by
    querying all raster layers currently available in the database / GRASS
    project. Limits of the y-axis are always set to the overall minimum and
    maximum values of all available rasters to make the generated plots of a
    given session comparable. The plot is automatically exported in
    html, so it can directly be embedded in the webapp.

    :param latitude: Latitude coordinate. [str or float]
    :param longitude: Longitude coordinate. [str or float]
    :param projection: Projection / EPSG code of the GRASS project. [str or
    int]

    :returns: Plot in html format.
    """

    ## Transform coordinates
    coord = transform_coord(lat=latitude, lng=longitude, proj=projection)

    ## Do GRASS stuff
    #start_grass_session(crs=projection, quiet=True)
    y_values, x_dates = get_timeseries(coord)

    ## Set y min and max based on all scenes in database
    y_min = min(Metadata.query.with_entities(Metadata.band_min).all()).band_min
    y_max = max(Metadata.query.with_entities(Metadata.band_max).all()).band_max

    ## Create plot
    p = figure(x_axis_label='Time', y_axis_label='Backscatter (dB)',
               x_axis_type='datetime', y_range=(y_min, y_max))

    p.line(x_dates, y_values, line_width=2, line_color='black')

    p.circle(x_dates, y_values, fill_color='black', line_color='black', size=5,
             legend_label=f"Time series for location: "
                          f"{round(float(latitude), 2)},"
                          f"{round(float(longitude), 2)}")

    html = file_html(p, CDN)

    return html


"""
##################### PROJECT GRAVEYARD ######################################
(some of this might be useful again in the future...?)

##################################
## REPROJECTING scenes by using two Mapsets and importing from one to 
the other with r.proj. Solution is based on the Inline method example here:
https://grass.osgeo.org/grass78/manuals/r.proj.html
 
def reproject_scene(scene, crs_in=None):
    \"""Reproject scenes from CRS that is defined by the parameter 'crs_in' and
    into the CRS of the GRASS session that currently is running.
    :param scene: full path e.g.
    'D:\\GEO450_data\\S1A__IW___A_20150320T182611_147_VV_grd_mli_norm_geo_db.tif'
    :param crs_in: Source CRS (e.g. '32629') [Str]
    :return: Scene imported and reprojected into destination CRS.
    \"""
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
                        mapset='PERMANENT', memory=500, quiet=False,
                        overwrite=True)


##################################
## FOOTPRINT creation for each raster as GeoJSON (and reprojection into WGS84)

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
    \"""All calculations in GRASS are done in the original projection but WGS84
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
    
##################################
## ADDING outputs to the database

def add_grass_output_to_db(info_dict):
    \"""

    :param info_dict:
    :return:
    \"""

    info = info_dict

    for key in info.keys():
        if key == 'all':
            go = GrassOutput(description=info[key]['description'],
                             filepath=info[key]['filepath'],
                             s1_scene=None)
            db.session.add(go)
            db.session.commit()

        else:
            s = Scene.query.filter_by(filepath=key).first()

            go = GrassOutput(description=info[key]['description'],
                             filepath=info[key]['filepath'],
                             s1_scene=s)
            db.session.add(go)
            db.session.commit()
"""
