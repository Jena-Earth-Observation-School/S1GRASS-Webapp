from config import Data, Grass
from grass_fun import *
from flask_app import db
from flask_app.models import Scene, Metadata, Geometry

from osgeo import gdal, osr
from osgeo.gdalconst import GA_ReadOnly
import json
import os
import re
gdal.UseExceptions()


def main():
    pass


def data_dict(dir_path):
    """Creates a dictionary with information about each valid Sentinel-1
    .tif (!) file in the data directory. The extracted information is then
    used to fill the SQLite database.
    :param dir_path: Path to data directory.
    :return data_dict: Dictionary
    """
    # Search for Sentinel-1 scenes using regular expression
    scenes = [dir_path + "\\" + f for f in os.listdir(dir_path) if
              re.search(r'^S1[AB].*\.tif', f)]

    if len(scenes) == 0:
        raise ImportError("No Sentinel-1 GeoTiffs were found in the "
                          "directory: ", dir_path)

    ## Get EPSG-code from one of the scenes and setup GRASS (sloppy
    ## try-except-clause just in case, but I'd assume that the user actually
    ## uses valid files anyway...)
    try:
        epsg = _get_epsg(scenes[0])
    except:
        epsg = _get_epsg(scenes[1])

    setup_grass(crs=epsg)

    # Loop over each scene, extract information and store in dict
    data_dict = {}
    for scene in scenes:
        data = gdal.Open(scene, GA_ReadOnly)
        band = data.GetRasterBand(1)

        try:
            band_min, band_max = band.ComputeRasterMinMax(True)

            proj = osr.SpatialReference(wkt=data.GetProjection())
            bounds = _get_bounds_res(data)
            file_info = _get_filename_info(scene)

            # Get footprint using GRASS
            foot_path = get_footprint(scene)
            with open(foot_path) as foot:
                footprint = json.load(foot)

            data_dict[scene] = {"sensor": file_info[0],
                                "orbit": file_info[2],
                                "date": file_info[4],
                                "acquisition_mode": file_info[1],
                                "polarisation": file_info[3],
                                "columns": data.RasterXSize,
                                "rows": data.RasterYSize,
                                "epsg": str(proj.GetAttrValue('AUTHORITY', 1)),
                                "bounds_south": bounds[0],
                                "bounds_north": bounds[2],
                                "bounds_west": bounds[3],
                                "bounds_east": bounds[1],
                                "resolution": int(bounds[4]),
                                "nodata_val": int(band.GetNoDataValue()),
                                "band_min": band_min,
                                "band_max": band_max,
                                "footprint": str(footprint)}
        except RuntimeError:
            print(os.path.basename(scene))
            print("No valid pixels were found in sampling. File will be "
                  "ignored.")
            continue

    return data_dict


def _get_bounds_res(dataset):
    """Gets information about extent as well as x- and y-resolution of a loaded
    raster file.
    :param dataset: osgeo.gdal.Dataset
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


def _get_epsg(path):

    data = gdal.Open(path, GA_ReadOnly)
    proj = osr.SpatialReference(wkt=data.GetProjection())
    epsg = str(proj.GetAttrValue('AUTHORITY', 1))

    return epsg


if __name__ == "__main__":

    path = Data.path
    main(path)


###################

def test_main(path):

    ## flask db init (not a problem if db & migration stuff already exists!)

    data = data_dict(Data.path)

    db_scenes = Scene.query.all()

    if len(db_scenes) is 0:
        ## Add all scenes to database

    else:
        ## 1. Check which scenes are already in the database
        ## 2. Search for new scenes in data directory
        ## 3. Create dictionary with information for these new scenes
        ## 4. Add new scenes to database

    ## flask db migrate
    ## flask db upgrade

######

db_scenes = Scene.query.all()
data = data_dict(Data.path)

## Fill db with ALL keys from dict
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
                 band_max=data[scene]['band_max'])
    g = Geometry(columns=data[scene]['columns'],
                 rows=data[scene]['rows'],
                 epsg=data[scene]['epsg'],
                 bounds_south=data[scene]['bounds_south'],
                 bounds_north=data[scene]['bounds_north'],
                 bounds_west=data[scene]['bounds_west'],
                 bounds_east=data[scene]['bounds_east'],
                 footprint=data[scene]['footprint'])

    db.session.add(s)
    db.session.add(m)
    db.session.add(g)
    db.session.commit()



###################
