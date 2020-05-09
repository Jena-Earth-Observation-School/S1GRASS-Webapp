from osgeo import gdal, osr
from osgeo.gdalconst import GA_ReadOnly
import os, re
import sqlite3
from sqlite3 import Error

def create_db(dir_path):
    """Creates an empty SQLite database in a subdirectory of the provided path.
    :param dir_path: Path to data directory.
    :return: SQLite database
    """
    db_name = "scenes.db"
    db_path = dir_path + "\\sqlite"
    db_path_name = db_path + "\\" + db_name
    if not os.path.exists(db_path):
        os.makedirs(db_path)

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

    conn = None
    try:
        conn = sqlite3.connect(db_path_name)

        key_string = ', '.join(
            [f'{key} {key_dict[key]}' for key in key_dict.keys()])
        meta_string = ', '.join(
            [f'{key} {meta_dict[key]}' for key in meta_dict.keys()])
        geo_string = ', '.join(
            [f'{key} {geo_dict[key]}' for key in geo_dict.keys()])

        # Dataset table
        conn.execute(
            f'CREATE TABLE datasets ({key_string}, filepath VARCHAR[max], '
            f'PRIMARY KEY({", ".join(key_dict.keys())}))')

        # Key table
        key_rows = [(key, ) for key in key_dict.keys()]
        conn.execute(f'CREATE TABLE keys (key VARCHAR[255])')
        conn.executemany('INSERT INTO keys VALUES (?)', key_rows)
        conn.commit()

        # Metadata table
        conn.execute(f'CREATE TABLE metadata ({key_string}, {meta_string}, '
                     f'PRIMARY KEY ({", ".join(key_dict.keys())}))')

        # Geometry table
        conn.execute(f'CREATE TABLE geometry ({key_string}, {geo_string}, '
                     f'PRIMARY KEY ({", ".join(key_dict.keys())}))')

    except Error as e:
        print(e)


def fill_db(dir_path):
    """

    :param dir_path: Path to data directory.
    :return:
    """
    db_name = "scenes.db"
    db_path_name = dir_path + "\\sqlite\\" + db_name

    conn = None
    try:
        conn = sqlite3.connect(db_path_name)



    except Error as e:
        print(e)


def data_dict(dir_path):
    """Creates a dictionary with information about each valid .tif file in
    the data directory. The extracted information is then used to fill the
    SQLite database.
    :param dir_path: Path to data directory.
    :return: Dictionary
    """
    scenes = [dir_path + "\\" + f for f in os.listdir(dir_path) if
                 re.search(r'^S1['r'AB'r'].*\.tif', f)]

    data_dict = {}
    for scene in scenes:
        data = gdal.Open(scene, GA_ReadOnly)

        proj = osr.SpatialReference(wkt=data.GetProjection())
        band = data.GetRasterBand(1)
        band_min, band_max = band.ComputeRasterMinMax(True)

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


def _get_bounds_res(file):
    """Gets information about extent/bounds, as well as x- and y-resolution
    of a raster file.
    :param file: osgeo.gdal.Dataset
    :return: List containing extracted information.
    """
    ulx, xres, xskew, uly, yskew, yres = file.GetGeoTransform()
    lrx = ulx + (file.RasterXSize * xres)
    lry = uly + (file.RasterYSize * yres)

    return [lrx, lry, ulx, uly, xres, yres]


def _get_filename_info(file_path):
    """Gets information about a raster file based on pyroSAR's file naming
    scheme: https://pyrosar.readthedocs.io/en/latest/general/filenaming.html
    :param path: Path to a raster file (e.g. "D:\\data_dir\\filename.tif)."
    :return: List containing extracted information.
    """
    filename = os.path.basename(file_path)

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

    if "VV" in filename:
        pol = "VV"
    elif "VH" in filename:
        pol = "VH"
    else:
        pol = "-"
        print("Could not find polarisation type for: ", filename)

    date = filename[12:27].replace("_", "")

    return [sensor, acq_mode, orbit, pol, date]



data_path = "D:\\GEO450_data"

create_db(data_path)

######################

db_name = "scenes.db"
db_path_name = data_path + "\\sqlite\\" + db_name

conn = sqlite3.connect(db_path_name)

conn.execute()


#################
scene = scenes_s1[10]
data = gdal.Open(scene, GA_ReadOnly)
proj = osr.SpatialReference(wkt=data.GetProjection())
epsg = proj.GetAttrValue('AUTHORITY',1)

