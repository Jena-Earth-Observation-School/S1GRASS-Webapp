from flask import render_template
from flask_webapp import app


"""
protect forms against attacks
generated with:
import secrets
secrets.token_hex(16)
"""
#app.config['SECRET_KEY'] = 'ade2d304eef78f4449e8cfbe86ef0269'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////sqlite/scenes.db'
#db = SQLAlchemy(app)


@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Marco'}
    return render_template('test.html', user=user)


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

#if __name__ == '__main__':
#    app.run(debug=False)