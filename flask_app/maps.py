from config import Grass
from flask_app.models import Scene

import folium
from pyproj import Transformer
from osgeo import gdal
import os


def get_coords_from_first():

    ## Get first scene in database
    scene = Scene.query.first()

    ## Get projection and bounds
    epsg = scene.geo[0].epsg
    n1 = scene.geo[0].bounds_north
    s1 = scene.geo[0].bounds_south
    w1 = scene.geo[0].bounds_west
    e1 = scene.geo[0].bounds_east

    ## Calculate center
    x = n1 + ((s1 - n1) / 2)
    y = w1 + ((e1 - w1) / 2)

    ## Transform into EPSG:4326
    transformer = Transformer.from_crs(str('epsg:' + epsg), "epsg:4326")
    lon_lat = transformer.transform(x, y)

    return lon_lat


######################

## Test adding footprint to map
#scene = Scene.query.first()
#foot = scene.geo[0].footprint
#foot_geojson = json.loads(foot)

#folium.GeoJson(foot_geojson, name='test_footprint').add_to(map_)


## Test adding raster to map
coords = get_coords_from_first()
map_ = folium.Map(location=coords, zoom_start=10)

cog = os.path.join(Grass.path_out, "cog_4326\\test_cog.tif")
tif = os.path.join(Grass.path_out, "cog_4326\\test_geotiff.tif")

ds = gdal.Open(cog, gdal.GA_ReadOnly)
rb = ds.GetRasterBand(1)
img_array = rb.ReadAsArray()

lat_min = 36.732445
lat_max = 37.266466
lon_min = -6.594324
lon_max = -6.147788
bounds = [[lat_min, lon_min], [lat_max, lon_max]]

[[36.732445, -6.594324], [37.266466, -6.147788]]

map_.add_child(folium.raster_layers.ImageOverlay(image=img_array,
                                                 bounds=bounds,
                                                 opacity=0.75))

map_.save('map_cog.html')


