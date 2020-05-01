from pyroSAR import Archive, identify
from spatialist.ancillary import finder
from osgeo import gdal, osr
from osgeo.gdalconst import GA_ReadOnly
import os
from shapely.geometry import box
import numpy as np


filename = './data/Spain_Donana_2015/S1A__IW___D_20150601T062638_154_VV_grd_mli_norm_geo_db.tif'
archive_s1 = './data/Spain_Donana_2015/'
dbname = 'scenes.db'
scenes_s1 = finder(archive_s1, [r'^S1[AB].*\.tif'], regex=True,
                        recursive=True)

with Archive(dbname) as archive:
    archive.insert(scenes_s1)


#################
dataset = gdal.Open(filename, GA_ReadOnly)
samples = dataset.RasterXSize
lines = dataset.RasterYSize
bands = dataset.RasterCount
projection = dataset.GetProjection()
geotransform = dataset.GetGeoTransform()
origin = (geotransform[0], geotransform[3])
resolution = (geotransform[1], geotransform[5])

band = dataset.GetRasterBand(1)
band_dtype = gdal.GetDataTypeName(band.DataType)
band_min, band_max = band.ComputeRasterMinMax(True)

########

metadata = os.popen('gdalinfo ./data/Spain_Donana_2015/S1A__IW___D_20150601T062638_154_VV_grd_mli_norm_geo_db.tif').read()
print(metadata)

################
raster = gdal.Open(filename)

def bounds_raster(path):
    raster = gdal.Open(path)
    ulx, xres, xskew, uly, yskew, yres  = raster.GetGeoTransform()
    lrx = ulx + (raster.RasterXSize * xres)
    lry = uly + (raster.RasterYSize * yres)
    return box(lrx,lry,ulx,uly)

##################



#####################

##########
from osgeo import gdal, ogr

def raster2array(rasterfn):
    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(1)
    return band.ReadAsArray()

def getNoDataValue(rasterfn):
    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(1)
    return band.GetNoDataValue()

def array2raster(rasterfn,newRasterfn,array):
    raster = gdal.Open(rasterfn)
    geotransform = raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    cols = raster.RasterXSize
    rows = raster.RasterYSize

    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Float32)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromWkt(raster.GetProjectionRef())
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()


rasterfn = './data/Spain_Donana_2015/S1A__IW___D_20150601T062638_154_VV_grd_mli_norm_geo_db.tif'
newValue = 1
newRasterfn = './data/test.tif'

# Convert Raster to array
rasterArray = raster2array(rasterfn)

# Get no data value of array
noDataValue = getNoDataValue(rasterfn)

# Updata no data value in array with new value
rasterArray[rasterArray != noDataValue] = newValue
rasterArray[rasterArray == noDataValue] = 0

# Write updated array to new raster
array2raster(rasterfn,newRasterfn,rasterArray)

##################

gdal.UseExceptions()

newraster = gdal.Open("./data/test.tif")
srcband = newraster.GetRasterBand(1)

dst_layername = "./data/newraster_poly"
drv = ogr.GetDriverByName("ESRI Shapefile")
dst_ds = drv.CreateDataSource( dst_layername + ".shp" )
dst_layer = dst_ds.CreateLayer(dst_layername, srs = None)

gdal.Polygonize(srcband, None, dst_layer, -1, [], callback=None )

