from spatialist.ancillary import finder
from osgeo import gdal, osr
from osgeo.gdalconst import GA_ReadOnly
import os

data_path = "D:\\GEO450_data"
file1 = data_path + \
        "\\S1A__IW___A_20150107T182611_147_VV_grd_mli_norm_geo_db.tif"
file2 = data_path + \
        "\\S1A__IW___A_20150303T181753_74_VV_grd_mli_norm_geo_db.tif"

dbname = 'test.db'
scenes_s1 = finder(data_path, [r'^S1[AB].*\.tif'], regex=True,
                        recursive=True)

#################
## Get Information using GDAL

dataset = gdal.Open(file1, GA_ReadOnly)
geotransform = dataset.GetGeoTransform()
band = dataset.GetRasterBand(1)

cols = dataset.RasterXSize #int
rows = dataset.RasterYSize #int
bands = dataset.RasterCount #int
proj_wkt = dataset.GetProjection() #str
origin = (geotransform[0], geotransform[3]) #tuple
resolution = (geotransform[1], geotransform[5]) #tuple
band_dtype = gdal.GetDataTypeName(band.DataType) #str
band_min, band_max = band.ComputeRasterMinMax(True) #float, float
nodata_val = band.GetNoDataValue() #float

def bounds_raster(dataset):
    ulx, xres, xskew, uly, yskew, yres  = dataset.GetGeoTransform()
    lrx = ulx + (dataset.RasterXSize * xres)
    lry = uly + (dataset.RasterYSize * yres)
    return [lrx,lry,ulx,uly]


bounds = bounds_raster(dataset)

#src = osr.SpatialReference()
#src.ImportFromWkt(proj_wkt)

####################
## Get information from file names
## https://pyrosar.readthedocs.io/en/latest/general/filenaming.html

# sensor, orbit
# acquisition mode
# polarisation
# date

from pyroSAR import identify

id = identify(file1)
print(id.outname_base())

