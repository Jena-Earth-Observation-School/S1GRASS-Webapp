from flask import render_template, send_from_directory

from flask_app import app
from config import Grass
from sqlite_fun import db_main
from grass_fun import grass_main
from flask_app.tables import *
from flask_app.models import Scene


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

    ## Dynamic title for the html page
    title = "Metadata for scene #" + scene_id

    ## Get filepath to render the file on a map
    filepath = s.filepath

    return render_template('table_meta.html', table=table, title=title,
                           filepath=filepath)


@app.route('/map')
def main_map():

    filepath = os.path.join(Grass.path_out, 'avg_raster.tif')

    return render_template('map.html', filepath=filepath)


@app.route('/serve//<path:filepath>')
def serve_file(filepath):

    path = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    return send_from_directory(path, filename,
                               as_attachment=True)
