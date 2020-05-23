import os

basedir = os.path.abspath(os.path.dirname(__file__))
sqlite_dir = os.path.join(basedir, 'sqlite')
grass_dir = os.path.join(basedir, 'grass')

if not os.path.exists(sqlite_dir):
    os.makedirs(sqlite_dir)

if not os.path.exists(grass_dir):
    os.makedirs(grass_dir)

class Config(object):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' \
                              + os.path.join(sqlite_dir, 'webapp.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
