from flask import render_template
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import folium
from flask_webapp import app


@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Marco'}
    return render_template('test.html', user=user)

@app.route('/map')
def map():
    start_coords = (46.9540700, 142.7360300)
    folium_map = folium.Map(location=start_coords, zoom_start=14)
    return folium_map._repr_html_()

"""
@app.route('/list')
def list():
    con = sqlite3.connect('D:/GEO450_data/sqlite/scenes.db')
    con.row_factory = sqlite3.Row

    cur = con.cursor()
    cur.execute('select filepath from datasets')

    rows = cur.fetchall()

    keys = ['outname_base', 'scene']
    names = ['identifier', 'location']
    # keys = rows[0].keys()

    return render_template('list.html', keys=keys, rows=rows, names=names)
"""
