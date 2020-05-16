from osgeo import gdal, osr
from osgeo.gdalconst import GA_ReadOnly
import os
import re
import sqlite3
from sqlite3 import Error
gdal.UseExceptions()


def db_main(dir_path):
    """Either creates & fills a new sqlite database or updates an
    existing database in a subdirectory of dir_path called "sqlite".
    :param dir_path: Path to data directory.
    :return: Newly created or updated existing database.
    """
    # Create data dictionary
    data = data_dict(dir_path)

    # Define subdirectory to store database
    db_path = dir_path + "\\sqlite"

    # If subdirectory doesn't exist yet: create & fill database. If
    # subdirectory (and presumably a database) already exist then
    # still fill the database, which should ignore already existing entries
    # and add new ones.
    if not os.path.exists(db_path):
        create_db(db_path)
        fill_db(db_path, data)

    else:
        fill_db(db_path, data)


def data_dict(dir_path):
    """Creates a dictionary with information about each valid Sentinel-1
    .tif (!) file in the data directory. The extracted information is then
    used to fill the SQLite database.
    :param dir_path: Path to data directory.
    :return data_dict: Dictionary
    """
    scenes = [dir_path + "\\" + f for f in os.listdir(dir_path) if
              re.search(r'^S1[AB].*\.tif', f)]

    if len(scenes) == 0:
        raise ImportError("No valid Sentinel-1 GeoTiffs were found in the "
                          "directory: ", dir_path)

    data_dict = {}
    for scene in scenes:
        data = gdal.Open(scene, GA_ReadOnly)
        band = data.GetRasterBand(1)

        try:
            band_min, band_max = band.ComputeRasterMinMax(True)

            proj = osr.SpatialReference(wkt=data.GetProjection())
            bounds = _get_bounds_res(data)
            file_info = _get_filename_info(scene)

            data_dict[scene] = {"sensor": file_info[0],
                                "orbit": file_info[2],
                                "date": file_info[4],
                                "acquisition_mode": file_info[1],
                                "polarisation": file_info[3],
                                "shape": (data.RasterXSize, data.RasterYSize,
                                          data.RasterCount),
                                "proj_epsg": proj.GetAttrValue('AUTHORITY', 1),
                                "bounds_south": bounds[0],
                                "bounds_north": bounds[2],
                                "bounds_west": bounds[3],
                                "bounds_east": bounds[1],
                                "xy_resolution": (bounds[4], bounds[5]),
                                "nodata_val": band.GetNoDataValue(),
                                "band_dtype": gdal.GetDataTypeName(band.DataType),
                                "band_min": band_min,
                                "band_max": band_max,
                                "footprint": "insert_footprint_here"}
        except RuntimeError:
            print(os.path.basename(scene))
            print("No valid pixels were found in sampling. File will be "
                  "ignored.")
            continue

    return data_dict


def create_db(db_path, db_name=None):
    """Creates an empty SQLite database in a subdirectory of the provided path.
    :param db_path: Path to sqlite subdirectory.
    :param db_name: Name of database to be created.
    :return: Empty SQLite database.
    """
    if not os.path.exists(db_path):
        os.makedirs(db_path)

    if db_name is None:
        db_name = "scenes.db"

    db_path_name = db_path + "\\" + db_name

    key_dict = {"sensor": "VARCHAR[255]",
                "orbit": "VARCHAR[255]",
                "date": "DATETIME"}
    meta_dict = {"acquisition_mode": "VARCHAR[255]",
                 "polarisation": "VARCHAR[255]",
                 "shape": "VARCHAR[255]",
                 "xy_resolution": "VARCHAR[255]",
                 "nodata_val": "VARCHAR[255]",
                 "band_dtype": "VARCHAR[255]",
                 "band_min": "REAL",
                 "band_max": "REAL"}
    geo_dict = {"proj_epsg": "VARCHAR[255]",
                "bounds_south": "REAL",
                "bounds_north": "REAL",
                "bounds_west": "REAL",
                "bounds_east": "REAL",
                "footprint": "VARCHAR[max]"}

    conn = _create_connection(db_path_name)
    with conn:
        cursor = conn.cursor()

        key_string = ', '.join(
            [f'{key} {key_dict[key]}' for key in key_dict.keys()])
        meta_string = ', '.join(
            [f'{key} {meta_dict[key]}' for key in meta_dict.keys()])
        geo_string = ', '.join(
            [f'{key} {geo_dict[key]}' for key in geo_dict.keys()])

        # Dataset table
        cursor.execute(
            f'CREATE TABLE datasets ({key_string}, filepath VARCHAR[max], '
            f'PRIMARY KEY({", ".join(key_dict.keys())}))')

        # Key table
        key_rows = [(key, ) for key in key_dict.keys()]
        cursor.execute(f'CREATE TABLE keys (key VARCHAR[255])')
        cursor.executemany('INSERT INTO keys VALUES (?)', key_rows)
        conn.commit()

        # Metadata table
        cursor.execute(f'CREATE TABLE metadata ({key_string}, {meta_string}, '
                     f'PRIMARY KEY ({", ".join(key_dict.keys())}))')

        # Geometry table
        cursor.execute(f'CREATE TABLE geometry ({key_string}, {geo_string}, '
                     f'PRIMARY KEY ({", ".join(key_dict.keys())}))')

    conn.close()


def fill_db(db_path, db_dict):
    """Fills the empty database that was created using create_db() with
    information from db_dict.
    :param db_path: Path to sqlite subdirectory.
    :param db_dict: Dictionary created by data_dict().
    :return: Filled/Updated SQLite database
    """

    db_path_name = db_path + "\\scenes.db"

    conn = _create_connection(db_path_name)
    with conn:
        cursor = conn.cursor()
        for key in db_dict.keys():

            cursor.execute("""INSERT OR IGNORE INTO datasets(sensor, orbit, 
            date, filepath) VALUES (?, ?, ?, ?)""",
                           (db_dict[key]["sensor"],
                            db_dict[key]["orbit"],
                            db_dict[key]["date"],
                            key))

            cursor.execute("""INSERT OR IGNORE INTO geometry(sensor, orbit, 
                        date, proj_epsg, bounds_south, bounds_north, 
                        bounds_west, bounds_east) VALUES (?, ?, ?, 
                        ?, ?, ?, ?, ?)""",
                           (db_dict[key]["sensor"],
                            db_dict[key]["orbit"],
                            db_dict[key]["date"],
                            db_dict[key]["proj_epsg"],
                            db_dict[key]["bounds_south"],
                            db_dict[key]["bounds_north"],
                            db_dict[key]["bounds_west"],
                            db_dict[key]["bounds_east"]))

            cursor.execute("""INSERT OR IGNORE INTO metadata(sensor, orbit, 
                        date, acquisition_mode, polarisation, shape, 
                        xy_resolution, nodata_val, band_dtype, band_min, 
                        band_max) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                           (db_dict[key]["sensor"],
                            db_dict[key]["orbit"],
                            db_dict[key]["date"],
                            db_dict[key]["acquisition_mode"],
                            db_dict[key]["polarisation"],
                            str(db_dict[key]["shape"]),
                            str(db_dict[key]["xy_resolution"]),
                            db_dict[key]["nodata_val"],
                            db_dict[key]["band_dtype"],
                            db_dict[key]["band_min"],
                            db_dict[key]["band_max"]))

    conn.close()


def _create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file.
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)

    except Error as e:
        print(e)

    return conn


def _get_bounds_res(dataset):
    """Gets information about extent as well as x- and y-resolution of a loaded
    raster file.
    :param file: osgeo.gdal.Dataset
    :return: List containing extracted information.
    """
    ulx, xres, xskew, uly, yskew, yres = dataset.GetGeoTransform()
    lrx = ulx + (dataset.RasterXSize * xres)
    lry = uly + (dataset.RasterYSize * yres)

    return [lrx, lry, ulx, uly, xres, yres]


def _get_filename_info(path):
    """Gets information about a raster file based on pyroSAR's file naming
    scheme: https://pyrosar.readthedocs.io/en/latest/general/filenaming.html
    :param path: Path to a raster file (e.g. "D:\\data_dir\\filename.tif)."
    :return: List containing extracted information.
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

    date = filename[12:27].replace("_", "")

    return [sensor, acq_mode, orbit, pol, date]


#########################################################################
data_path = "D:\\GEO450_data"

db_main(data_path)




