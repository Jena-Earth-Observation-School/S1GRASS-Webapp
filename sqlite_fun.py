from config import Data, Database
from grass_fun import *
from flask_app import db
from flask_app.models import Scene, Metadata, Geometry

from osgeo import gdal, osr
from osgeo.gdalconst import GA_ReadOnly
import json
import os
import re
import shutil
import dateutil.parser
gdal.UseExceptions()


def db_main():

    ## Initialize database if it hasn't been done already.
    if not os.path.isdir("./migrations"):
        os.system('flask db init')

    ## Setup database scheme if it hasn't been done already.
    file = os.path.join(Database.path, "s1_webapp.db")
    if not os.path.isfile(file):
        os.system('flask db migrate')
        os.system('flask db upgrade')

    ## Create dictionary with all necessary information. This also includes
    ## setting up GRASS and importing / reprojecting all files.
    data = create_data_dict()

    ## Add extracted information to database.
    add_data_to_db(data)


def create_data_dict(dir_path=None, footprint=True):
    """Creates a dictionary with information about each valid Sentinel-1
    .tif (!) file in the data directory. The extracted information is then
    used to fill the SQLite database.
    :param dir_path: Path to data directory.
    :param footprint: Calculates footprint using GRASS if set to
    True.
    :return data_dict: Extracted information [dict]
    """

    ## Define path to data directory
    if dir_path is None:
        dir_path = Data.path

    ## List all Sentinel-1 GeoTiffs
    scenes = _get_filename_list(dir_path)

    ## Get EPSG-code from one of the scenes and setup GRASS (sloppy
    ## try-except-clause just in case the first file is faulty. Might need
    # to think of something else here.)
    try:
        epsg = _get_epsg(scenes[0])
    except:
        epsg = _get_epsg(scenes[1])

    ## Setup two GRASS Locations. One with the original crs and another in
    ## WGS84.
    setup_grass(crs=epsg)
    setup_grass(crs='4326')

    ## Loop over each scene, extract information and store in dict
    data_dict = {}
    for scene in scenes:
        data = gdal.Open(scene, GA_ReadOnly)
        band = data.GetRasterBand(1)

        try:
            band_min, band_max = band.ComputeRasterMinMax(True)

            ## Get information that is stored in the filename itself (#pyroSAR)
            file_info = _get_filename_info(scene)

            ## Get extent and resolution
            bounds = _get_extent_resolution(data)

            """
            ## If footprint is True: Calculate footprint using GRASS.
            if footprint:
                foot_path = get_footprint(scene)

                ## Reproject into EPSG 4326
                new_foot_path = reproject_geojson(foot_path, epsg)

                ## Load footprint and store as string in the db
                with open(new_foot_path) as foot:
                    f_json = json.load(foot)
                    f_string = json.dumps(f_json)
            else:
                f_string = None
            """
            f_string = None

            data_dict[scene] = {"sensor": file_info[0],
                                "orbit": file_info[2],
                                "date": file_info[4],
                                "acquisition_mode": file_info[1],
                                "polarisation": file_info[3],
                                "columns": data.RasterXSize,
                                "rows": data.RasterYSize,
                                "epsg": epsg,
                                "bounds_south": bounds[0],
                                "bounds_north": bounds[2],
                                "bounds_west": bounds[3],
                                "bounds_east": bounds[1],
                                "resolution": int(bounds[4]),
                                "nodata_val": int(band.GetNoDataValue()),
                                "band_min": band_min,
                                "band_max": band_max,
                                "footprint": f_string}

        except RuntimeError:
            print(os.path.basename(scene))
            print("No valid pixels were found in sampling. File will be "
                  "moved to subdirectory 'reject'.")

            ## File was opened in GDAL. Overwrite with 'None' to close.
            data = None

            ## Create subdirectory for rejected files that for some reason
            ## are faulty and can't be used
            reject_dir = os.path.join(Data.path, "reject")
            if not os.path.exists(reject_dir):
                os.makedirs(reject_dir)
            olddir = scene
            newdir = os.path.join(reject_dir, os.path.basename(scene))

            shutil.move(olddir, newdir)

            continue

    return data_dict


def add_data_to_db(data_dict):
    """Adds information that was extracted using 'create_data_dict()' to the
    database.
    :param data_dict: Dictionary that contains information to be added to
    the database.
    """
    data = data_dict

    for scene in data.keys():
        s = Scene(sensor=data[scene]['sensor'],
                  orbit=data[scene]['orbit'],
                  date=data[scene]['date'],
                  filepath=scene)
        m = Metadata(acq_mode=data[scene]['acquisition_mode'],
                     polarisation=data[scene]['polarisation'],
                     resolution=data[scene]['resolution'],
                     nodata=data[scene]['nodata_val'],
                     band_min=data[scene]['band_min'],
                     band_max=data[scene]['band_max'],
                     s1_scene=s)
        g = Geometry(columns=data[scene]['columns'],
                     rows=data[scene]['rows'],
                     epsg=data[scene]['epsg'],
                     bounds_south=data[scene]['bounds_south'],
                     bounds_north=data[scene]['bounds_north'],
                     bounds_west=data[scene]['bounds_west'],
                     bounds_east=data[scene]['bounds_east'],
                     footprint=data[scene]['footprint'],
                     s1_scene=s)

        db.session.add(s)
        db.session.add(m)
        db.session.add(g)
        db.session.commit()


def _get_filename_list(path):
    """Creates a list of files that haven't been stored in the database yet.
    The list will be used in 'create_data_dict()' to extract all necessary
    information from those files.
    :param path: Full path of a raster file
    (e.g. "D:\\data_dir\\filename.tif").
    :return: Scenes that haven't been stored in the database yet. [List]
    """
    ## Search for Sentinel-1 scenes using regular expression
    scenes = [path + "\\" + f for f in os.listdir(path) if
              re.search(r'^S1[AB].*\.tif', f)]

    if len(scenes) == 0:
        raise ImportError("No Sentinel-1 GeoTiffs were found in the "
                          "directory: ", path)

    ## Scenes already in database
    db_scenes = Scene.query.all()

    ## Only return scenes that are not in the database yet!
    if len(db_scenes) is 0:
        return scenes

    else:
        scenes_new = []
        for scene in scenes:
            if any(scene in db.filepath for db in db_scenes):
                continue
            else:
                scenes_new.append(scene)

        return scenes_new


def _get_filename_info(path):
    """Gets information about a raster file based on pyroSAR's file naming
    scheme: https://pyrosar.readthedocs.io/en/latest/general/filenaming.html
    :param path: Full path of a raster file
    (e.g. "D:\\data_dir\\filename.tif").
    :return: Extracted information. [List]
    """
    filename = os.path.basename(path)

    sensor = filename[0:4].replace("_", "")
    acq_mode = filename[5:9].replace("_", "")
    orb = filename[10:11].replace("_", "")
    if orb == "A":
        orbit = "ascending"
    elif orb == "D":
        orbit = "descending"
    else:
        raise ValueError("filename[10:11] should contain "
                         "information about the orbit (ascending or "
                         "descending). \n Please check if your files are "
                         "named according to the naming scheme of PyroSAR: \n"
                         "https://pyrosar.readthedocs.io/en/latest/general/filenaming.html")
    if "_VV_" in filename:
        pol = "VV"
    elif "_VH_" in filename:
        pol = "VH"
    else:
        pol = None
        print("Could not find polarisation type for: ", filename)

    d = filename[12:27].replace("_", "")
    date = dateutil.parser.parse(d)

    return [sensor, acq_mode, orbit, pol, date]


def _get_extent_resolution(dataset):
    """Gets information about extent as well as x- and y-resolution of a loaded
    raster file.
    :param dataset: osgeo.gdal.Dataset
    :return: Extracted information. [List]
    """
    ulx, xres, xskew, uly, yskew, yres = dataset.GetGeoTransform()
    lrx = ulx + (dataset.RasterXSize * xres)
    lry = uly + (dataset.RasterYSize * yres)

    return [lrx, lry, ulx, uly, xres, yres]


def _get_epsg(path):
    """ Gets EPSG code from a raster file using GDAL.
    :param path: Full path of a raster file
    (e.g. "D:\\data_dir\\filename.tif").
    :return: EPSG code. [Str]
    """

    data = gdal.Open(path, GA_ReadOnly)
    proj = osr.SpatialReference(wkt=data.GetProjection())
    epsg = str(proj.GetAttrValue('AUTHORITY', 1))

    return epsg
