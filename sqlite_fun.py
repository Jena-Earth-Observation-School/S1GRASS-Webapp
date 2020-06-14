from config import Data, Database
from flask_app import db
from flask_app.models import Scene, Metadata, Geometry

from osgeo import gdal, osr
from osgeo.gdalconst import GA_ReadOnly
#import json
import os
import re
import shutil
import dateutil.parser
gdal.UseExceptions()


def db_main():
    """This workflow first uses flask-migrate to initialize the database
    scheme and sets up the database. It will then search the provided data
    directory for Sentinel-1 GeoTiffs. Information will be extracted from all
    scenes that haven't been imported to the database yet and added to the
    database. The most common CRS in the dataset will also be determined,
    which is used to set up GRASS.
    """

    ## Initialize database if it hasn't been done already.
    if not os.path.isdir("./migrations"):
        os.system('flask db init')

    ## Setup database scheme if it hasn't been done already.
    file = os.path.join(Database.path, "s1_webapp.db")
    if not os.path.isfile(file):
        os.system('flask db migrate')
        os.system('flask db upgrade')

    ## Create a list of files that haven't been stored in the database yet.
    ## Either this will just list all files because nothing has been
    ## added to the db yet or it will update the db with new files.
    scenes_list = create_filename_list()

    ## Create dictionary with all necessary information.
    data_dict, epsg_list = create_data_dict(scenes=scenes_list)

    ## Create new list of scenes in case any were rejected while running
    ## create_data_dict()
    scene_list_new = list(data_dict.keys())

    ## Add extracted information to database.
    add_data_to_db(data_dict)

    ## Get most common epsg from epsg_list
    epsg = max(set(epsg_list), key=epsg_list.count)

    return scene_list_new, epsg


def create_filename_list(path=None):
    """Creates a list of files that haven't been stored in the database yet.
    The list will be used in 'create_data_dict()' to extract all necessary
    information from those files.
    :param path: Full path of a raster file
    (e.g. "D:\\data_dir\\filename.tif").
    :return: Scenes that haven't been stored in the database yet. [List]
    """

    ## Define path to data directory
    if path is None:
        path = Data.path

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


def create_data_dict(scenes=None, footprint=True):
    """Creates a dictionary with information about each valid Sentinel-1
    .tif (!) file in the data directory. The extracted information is then
    used to fill the SQLite database.
    :param scenes: List of scenes created with get_filename_list().
    :param footprint: Calculates footprint using GRASS if set to
    True. (DEACTIVATED)
    :return data_dict: Extracted information [dict]
    """

    ## Loop over each scene, extract information and store in dict. Also
    # store EPSG code of each scene in a list.
    data_dict = {}
    epsg_list = []
    for scene in scenes:
        data = gdal.Open(scene, GA_ReadOnly)
        band = data.GetRasterBand(1)

        try:
            band_min, band_max = band.ComputeRasterMinMax(True)

            ## Get information that is stored in the filename itself (#pyroSAR)
            file_info = _get_filename_info(scene)

            ## Get extent and resolution
            bounds = _get_extent_resolution(data)

            ## Get EPSG and append to list
            epsg = _get_epsg(scene)
            epsg_list.append(epsg)

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

    return data_dict, epsg_list


def add_data_to_db(info_dict):
    """Adds information that was extracted using 'create_data_dict()' to the
    database.
    :param info_dict: Dictionary that contains information to be added to
    the database.
    """
    info = info_dict

    for scene in info.keys():
        s = Scene(sensor=info[scene]['sensor'],
                  orbit=info[scene]['orbit'],
                  date=info[scene]['date'],
                  filepath=scene)
        m = Metadata(acq_mode=info[scene]['acquisition_mode'],
                     polarisation=info[scene]['polarisation'],
                     resolution=info[scene]['resolution'],
                     nodata=info[scene]['nodata_val'],
                     band_min=info[scene]['band_min'],
                     band_max=info[scene]['band_max'],
                     s1_scene=s)
        g = Geometry(columns=info[scene]['columns'],
                     rows=info[scene]['rows'],
                     epsg=info[scene]['epsg'],
                     bounds_south=info[scene]['bounds_south'],
                     bounds_north=info[scene]['bounds_north'],
                     bounds_west=info[scene]['bounds_west'],
                     bounds_east=info[scene]['bounds_east'],
                     footprint=info[scene]['footprint'],
                     s1_scene=s)

        db.session.add(s)
        db.session.add(m)
        db.session.add(g)
        db.session.commit()


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
