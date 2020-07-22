from flask_app import app
from config import Grass
from sqlite_fun import db_main
from grass_fun import grass_main, start_grass_session, create_plot
from flask_app.tables import create_overview_table, create_meta_table
from flask_app.models import Scene

from flask import render_template, send_from_directory
import re
import os
from datetime import datetime


@app.before_first_request
def initialize():
    """This will trigger db_main() and grass_main() (for more details see
    function descriptions in sqlite_fun.py and grass_fun.py) when the
    webapp is opened to either create the SQLite database and setup GRASS for
    the first time, which might take a few minutes (depending on number and
    size of valid scenes) OR update both with new scenes OR to do nothing,
    because setup has already been done and there are no new scenes in the
    directory.
    """

    ## Create (or update) SQLite database
    scenes, epsg = db_main()

    ## Only execute grass_main() if new scenes were found. Scenes will be
    ## imported to the GRASS database and avg_raster.tif will be recalculated.
    if len(scenes) > 0:
        grass_main(scenes, epsg)
    else:
        ## Search for already existing GRASS project and start session
        l_dir = os.listdir(Grass.path)
        r = re.compile("GRASS.*")
        grass_project = list(filter(r.match, l_dir))[0]
        start_grass_session(name=grass_project)


@app.route('/')
@app.route('/home')
def index():

    all_scenes = Scene.query.all()

    date_min = all_scenes[0].date
    date_max = all_scenes[len(all_scenes) - 1].date

    date_min = date_min.strftime("%Y-%m-%d")
    date_max = date_max.strftime("%Y-%m-%d")

    return render_template('home.html', n_scenes=len(all_scenes),
                           date_min=date_min, date_max=date_max)


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

    ## Dynamic title for the html page
    title = "Metadata for scene #" + scene_id

    ## Get filepath to render raster on map
    filepath = s.filepath

    return render_template('table_meta.html', table=table, title=title,
                           filepath=filepath)


@app.route('/map')
def main_map():

    filepath = os.path.join(Grass.path_out, 'avg_raster.tif')

    return render_template('map.html', filepath=filepath)


@app.route('/serve/<path:filepath>')
def serve_file(filepath):

    path = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    return send_from_directory(path, filename,
                               as_attachment=True)


@app.route('/plot/<string:lat>/<string:lng>/<string:proj>')
def plot(lat, lng, proj):

    html_plot = create_plot(latitude=lat, longitude=lng, projection=proj)

    return html_plot
