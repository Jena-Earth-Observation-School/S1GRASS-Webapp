from flask_table import Table, Col, LinkCol
import os

from flask_app.models import Scene


class OverviewTable(Table):
    classes = ['table table-striped']
    id = Col('ID')
    filename = Col('Filename')
    metadata = LinkCol('Metadata', 'meta', url_kwargs=dict(scene_id='id'))


class MetaTable(Table):
    classes = ['table table-striped']
    attr = Col('Attribute')
    val = Col('Value')


def create_overview_table():

    ## Query all scenes in the database
    db_scenes = Scene.query.all()

    ## Generate items to be listed
    items = []
    for scene in db_scenes:
        scene_info = {'id': scene.id,
                      'filename': os.path.basename(scene.filepath)}

        items.append(scene_info)

    ## Populate the table
    table = OverviewTable(items)

    ##  Return table as html
    return table.__html__()


def create_meta_table(scene):

    ## Query metadata for the given scene
    meta = scene.meta.all()
    geo = scene.geo.all()

    ## Generate items to be listed
    items = [dict(attr='Scene ID', val=scene.id),
             dict(attr='Date', val=scene.date),
             dict(attr='Sensor', val=scene.sensor),
             dict(attr='Orbit', val=scene.orbit),
             dict(attr='Acquisition Mode', val=meta[0].acq_mode),
             dict(attr='Polarisation', val=meta[0].polarisation),
             dict(attr='Resolution (m)', val=meta[0].resolution),
             dict(attr='Band Min', val=meta[0].band_min),
             dict(attr='Band Max', val=meta[0].band_max),
             dict(attr='Columns, Rows', val=f"{geo[0].columns}, "
                                            f"{geo[0].rows}"),
             dict(attr='EPSG', val=geo[0].epsg),
             dict(attr='Bounds North', val=geo[0].bounds_north),
             dict(attr='Bounds South', val=geo[0].bounds_south),
             dict(attr='Bounds East', val=geo[0].bounds_east),
             dict(attr='Bounds West', val=geo[0].bounds_west)]

    ## Populate the table
    table = MetaTable(items)

    ##  Return table as html
    return table.__html__()
