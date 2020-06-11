import folium
from pyproj import Transformer
import json

from flask_app.models import Scene


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
coords = get_coords_from_first()
map_ = folium.Map(location=coords, zoom_start=10)

## Test adding footprint to map
scene = Scene.query.first()
foot = scene.geo[0].footprint
foot_geojson = json.loads(foot)

folium.GeoJson(foot_geojson, name='test_footprint').add_to(map_)


## Test adding raster to map


map_.save('map.html')



