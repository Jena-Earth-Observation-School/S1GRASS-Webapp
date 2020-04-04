import sqlite3
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

"""
protect forms against attacks
generated with:
import secrets
secrets.token_hex(16)
"""
app.config['SECRET_KEY'] = 'ade2d304eef78f4449e8cfbe86ef0269'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

#db.Model.metadata.reflect(db.engine) #??

"""
create databases:
from main import db
db.create_all()

# delete all entries in db:
db.drop_all()
"""

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/list')
def list():
    con = sqlite3.connect('scenes.db')
    con.row_factory = sqlite3.Row

    cur = con.cursor()
    cur.execute('select * from data')

    rows = cur.fetchall()

    keys = ['outname_base', 'scene']
    names = ['identifier', 'location']
    # keys = rows[0].keys()

    return render_template('list.html', keys=keys, rows=rows, names=names)


if __name__ == '__main__':
    app.run(debug=True)