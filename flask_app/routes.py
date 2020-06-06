from flask import render_template
import folium

from flask_app.tables import *
from flask_app import app
from flask_app.models import Scene


@app.route('/')
@app.route('/home')
def index():
    return render_template('home.html')


@app.route('/map')
def map():
    start_coords = (46.9540700, 142.7360300)
    folium_map = folium.Map(location=start_coords, zoom_start=14)
    return folium_map._repr_html_()


@app.route('/overview')
def overview():

    ## Create table (html)
    table = create_overview_table()

    return render_template('table.html', table=table)


@app.route('/meta/<scene_id>')
def meta(scene_id):

    ## Get scene from database
    s = Scene.query.filter_by(id=scene_id).first_or_404()

    ## Create table (html)
    table = create_meta_table(s)

    return render_template('table.html', table=table)