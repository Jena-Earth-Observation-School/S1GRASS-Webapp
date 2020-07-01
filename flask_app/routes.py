from flask import render_template, send_from_directory
import os

from flask_app import app
from config import Grass
from sqlite_fun import db_main
from grass_fun import grass_main
from flask_app.tables import *
from flask_app.models import Scene


@app.before_first_request
def initialize():

    ## Create (or update) SQLite database
    scenes, epsg = db_main()

    if len(scenes) > 0:
        ## Setup (or update) GRASS database
        grass_main(scenes, epsg)
    else:
        pass


@app.route('/')
@app.route('/home')
def index():
    return render_template('home.html')


@app.route('/overview')
def overview():

    ## Create table (html)
    table = create_overview_table()

    ## Title for the html page
    title = "Scenes currently stored in the database:"

    return render_template('table.html', table=table, title=title)


@app.route('/meta/<scene_id>')
def meta(scene_id):

    ## Get scene by id
    s = Scene.query.filter_by(id=scene_id).\
        first_or_404("A scene with this ID is currently "
                     "not stored in the database.")

    ## Create table (html)
    table = create_meta_table(s)

    ## Title for the html page
    title = "Metadata for scene #" + scene_id

    ##
    path = os.path.dirname(s.filepath)
    filename = os.path.basename(s.filepath)

    return render_template('table_meta.html', table=table, title=title,
                           path=path, filename=filename)


@app.route('/serve/<path:path>/<path:filename>')
def serve_file(path, filename):
    return send_from_directory(path, filename,
                               as_attachment=True)


@app.route('/map')
def load_map():

    path = os.path.join(Grass.path_out, '4326\\aggregation')
    filename = 'avg_raster.tif'

    return render_template('map.html', path=path, filename=filename)
