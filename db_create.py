from osgeo import gdal, osr
from osgeo.gdalconst import GA_ReadOnly
import os, re
import sqlite3
from sqlite3 import Error

def create_db(path):
    """
    Creates an empty SQLite database in a subdirectory of the provided path
    called "sqlite".
    """
    db_name = "scenes.db"
    db_path = path + "\\sqlite"
    db_path_name = db_path + "\\" + db_name
    if not os.path.exists(db_path):
        os.makedirs(db_path)

    key_dict = {"sensor": "VARCHAR(255)",
                "orbit": "VARCHAR(255)",
                "date": "DATETIME"}
    meta_dict = {"acquisition mode": "VARCHAR(255)",
                 "polarisation": "VARCHAR(255)",
                 "shape": "VARCHAR(255)",
                 "resolution": "VARCHAR(255)",
                 "nodata_val": "VARCHAR(255)",
                 "band_dtype": "VARCHAR(255)",
                 "band_min": "REAL",
                 "band_max": "REAL",
                 "band_mean": "REAL"}
    geo_dict = {"projection_wkt": "VARCHAR(3000)",
                "bounds_south": "REAL",
                "bounds_north": "REAL",
                "bounds_west": "REAL",
                "bounds_east": "REAL",
                "footprint": "VARCHAR(3000)"}

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
            f'CREATE TABLE datasets ({key_string}, filepath VARCHAR(3000), '
            f'PRIMARY KEY({", ".join(key_dict.keys())}))')

        # Key table
        key_rows = [(key, ) for key in key_dict.keys()]
        conn.execute(f'CREATE TABLE keys (key VARCHAR(255))')
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


data_path = "D:\\GEO450_data"
create_db(data_path)

#################

scenes_s1 = [data_path + "\\" + f for f in os.listdir(data_path) if re.search(
    r'^S1['r'AB'r'].*\.tif', f)]

file1 = scenes_s1[10]
file2 = scenes_s1[26]

#################
## Get Information using GDAL

dataset = gdal.Open(file1, GA_ReadOnly)
geotransform = dataset.GetGeoTransform()
band = dataset.GetRasterBand(1)

cols = dataset.RasterXSize  # int
rows = dataset.RasterYSize  # int
bands = dataset.RasterCount  # int
proj_wkt = dataset.GetProjection()  # str
origin = (geotransform[0], geotransform[3])  # tuple
resolution = (geotransform[1], geotransform[5])  # tuple
band_dtype = gdal.GetDataTypeName(band.DataType)  # str
band_min, band_max = band.ComputeRasterMinMax(True)  # float, float
nodata_val = band.GetNoDataValue()  # float


def bounds_raster(dataset):
    ulx, xres, xskew, uly, yskew, yres = dataset.GetGeoTransform()
    lrx = ulx + (dataset.RasterXSize * xres)
    lry = uly + (dataset.RasterYSize * yres)
    return [lrx, lry, ulx, uly]


bounds = bounds_raster(dataset)

# src = osr.SpatialReference()
# src.ImportFromWkt(proj_wkt)

####################
## Get information from file names
## https://pyrosar.readthedocs.io/en/latest/general/filenaming.html

test_name = "S1A__IW___A_20150806T181746_74_VV_grd_mli_norm_geo_db.tif"

sensor = test_name[0:4]  # sensor
test_name[5:9]  # acquisition mode
test_name[10:11]  # orbit (asc / desc)
test_name[12:27]  # date

sensor.replace("_", "")



