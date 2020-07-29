from config import Data, Database
from flask_app import db
from flask_app.models import Scene, Metadata, Geometry

from osgeo import gdal, osr
from osgeo.gdalconst import GA_ReadOnly
import os
import re
import shutil
import dateutil.parser
gdal.UseExceptions()


def db_main():
    """This workflow first uses flask-migrate to initialize the SQLite database
    scheme and sets up the database. It will then search the provided data
    directory for files in GeoTIFF format. Information will be extracted
    from all scenes that haven't been imported to the database yet and added to
    the database. The most common CRS in the dataset will also be determined,
    which is used in grass_main() (see grass_fun.py).
    """

    ## Initialize database if it hasn't been done already.
    if not os.path.isdir("./migrations"):
        os.system('flask db init')

    ## Setup database scheme if it hasn't been done already.
    file = os.path.join(Database.path, "s1_webapp.db")
    if not os.path.isfile(file):
        os.system('flask db migrate')
        os.system('flask db upgrade')
        print("~~~~")

    ## Create a list of files that haven't been stored in the database yet.
    ## Either this will just list all files because nothing has been
    ## added to the db yet or it will update the db with new files.
    scenes_list = create_filename_list()

    if len(scenes_list) == 0:
        print(f"~~ The database is up-to-date. No new files were found in "
              f"{Data.path}")
        epsg = None

        return scenes_list, epsg

    else:
        ## Create dictionary with all necessary information.
        data_dict, common_epsg = create_data_dict(scenes=scenes_list)

        ## Create new list of scenes in case any were rejected while running
        ## create_data_dict()
        scenes_list_new = list(data_dict.keys())

        ## Add extracted information to database.
        add_data_to_db(data_dict)

        print(
            f"~~ {len(scenes_list_new)} new files have been added to the "
            f"SQLite database and will now be imported to GRASS.")

        epsg = common_epsg

        return scenes_list_new, epsg


def create_filename_list(path=None):
    """Creates a list of files that haven't been stored in the database yet.
    The list will be used in 'create_data_dict()' to extract all necessary
    information from those files.

    :param path: Full path of a raster file
        (e.g. "D:\\data_dir\\filename.tif").

    :return: Scenes that haven't been stored in the database yet. [list]
    """

    ## Define path to data directory
    if path is None:
        path = Data.path

    ## Search for GeoTIFF files using regular expression
    scenes = [f"{path}\\{f}" for f in os.listdir(path) if
              re.search(r'.*\.tif', f)]

    if len(scenes) == 0:
        raise ImportError("No files in GeoTIFF format were found in the "
                          "directory: ", path)

    ## Scenes already in database
    db_scenes = Scene.query.all()

    ## Only return scenes that are not in the database yet!
    ## If no scenes in database, then all found scenes can be returned.
    ## Else scenes that are already in the database need to be sorted out
    ## first.
    if len(db_scenes) == 0:
        return scenes
    else:
        scenes_new = []
        for scene in scenes:
            if any(scene in db_scene.filepath for db_scene in db_scenes):
                continue
            else:
                scenes_new.append(scene)

        return scenes_new


def create_data_dict(scenes=None):
    """Creates a dictionary with information about each valid file in the
    data directory. The extracted information is then used to fill the
    SQLite database.

    :param scenes: List of scenes created with get_filename_list().

    :return data_dict: Extracted information [dict]
    :return common_epsg: Most common EPSG code for the dataset [int]
    """

    ## Loop over each scene, extract information and store in dict. Also
    ## store EPSG code of each scene in a separate list.
    any_reject = False  # will be set to True if any scenes are rejected
    num_reject = 0  # will be counted up, if any scenes are rejected
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
                                "band_max": band_max}

        except RuntimeError:
            ## File was opened in GDAL. Overwrite with 'None' to close.
            data = None

            ## Create subdirectory for rejected files
            reject_dir = os.path.join(Data.path, 'reject')
            if not os.path.exists(reject_dir):
                os.makedirs(reject_dir)

            olddir = scene
            newdir = os.path.join(reject_dir, os.path.basename(scene))
            shutil.move(olddir, newdir)

            num_reject += 1
            any_reject = True

            continue

    ## Get most common epsg from epsg_list
    common_epsg = max(set(epsg_list), key=epsg_list.count)

    ## Print number of scenes that were rejected (if any were rejected)
    if any_reject:
        print(f"~~ Could not extract necessary data from {num_reject} "
              f"scenes with GDAL. These scenes were moved to the "
              f"subdirectory '/reject'.")

    return data_dict, common_epsg


def add_data_to_db(info_dict):
    """Adds information that was extracted using 'create_data_dict()' to the
    database.

    :param info_dict: Information to be added to the database. [dict]
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
                     s1_scene=s)

        db.session.add(s)
        db.session.add(m)
        db.session.add(g)
        db.session.commit()


def _get_filename_info(path):
    """Gets information about a raster file based on pyroSAR's file naming
    scheme: https://pyrosar.readthedocs.io/en/latest/general/filenaming.html

    :param path: Full path of a raster file
        (e.g. "D:\\data_dir\\filename.tif")

    :return: Extracted information. [list]
    """
    filename = os.path.basename(path)

    sensor = filename[0:4].replace("_", "")
    acq_mode = filename[5:9].replace("_", "")
    orb = filename[10:11]

    if orb == "A":
        orbit = "ascending"
    elif orb == "D":
        orbit = "descending"
    else:
        raise ValueError("Information about the orbit (ascending or "
                         "descending) was expected at index [10:11] of the "
                         "filename. "
                         "\n Please check if your files are "
                         "named according to the naming scheme of pyroSAR: "
                         "\n https://pyrosar.readthedocs.io/en/latest/general/"
                         "filenaming.html")

    d = filename[12:27].replace("_", "")
    date = dateutil.parser.parse(d)

    if "_VV_" in filename:
        pol = "VV"
    elif "_VH_" in filename:
        pol = "VH"
    else:
        pol = None
        print(f"Could not find polarisation in filename: {filename}")

    return [sensor, acq_mode, orbit, pol, date]


def _get_extent_resolution(dataset):
    """Gets information about extent as well as x- and y-resolution of a loaded
    raster file.

    :param dataset: osgeo.gdal.Dataset

    :return: Extracted information. [list]
    """
    ulx, xres, xskew, uly, yskew, yres = dataset.GetGeoTransform()
    lrx = ulx + (dataset.RasterXSize * xres)
    lry = uly + (dataset.RasterYSize * yres)

    return [lrx, lry, ulx, uly, xres, yres]


def _get_epsg(path):
    """Gets EPSG code from a raster file using GDAL.

    :param path: Full path of a raster file
        (e.g. "D:\\data_dir\\filename.tif").

    :return: EPSG code. [str]
    """

    data = gdal.Open(path, GA_ReadOnly)
    proj = osr.SpatialReference(wkt=data.GetProjection())
    epsg = str(proj.GetAttrValue('AUTHORITY', 1))

    return epsg
