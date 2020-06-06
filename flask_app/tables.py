from flask_table import Table, Col
import os

from flask_app.models import Scene


class OverviewTable(Table):
    classes = ['table table-striped']
    id = Col('ID')
    filename = Col('Filename')


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

    ## Query all metadata for the given scene
    meta = scene.meta.all()

    ## Generate items to be listed
    items = [dict(attr='Scene ID', val=scene.id),
             dict(attr='Date', val=scene.date),
             dict(attr='Sensor', val=scene.sensor),
             dict(attr='Orbit', val=scene.orbit),
             dict(attr='Acquisition Mode', val=meta[0].acq_mode),
             dict(attr='Polarisation', val=meta[0].polarisation),
             dict(attr='Resolution (m)', val=meta[0].resolution),
             dict(attr='Band Min', val=meta[0].band_min),
             dict(attr='Band Max', val=meta[0].band_max)]

    ## Populate the table
    table = MetaTable(items)

    ##  Return table as html
    return table.__html__()