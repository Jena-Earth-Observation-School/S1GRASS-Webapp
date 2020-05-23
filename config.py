import os

###### CHANGE DATA DIRECTORY HERE ######

data_dir = "D:/GEO450_data"

########################################

data_dir = os.path.abspath(data_dir)

if not os.path.exists(data_dir):
    raise ImportError(data_dir, " does not exist. Please change the "
                                "variable 'data_dir' in 'config.py' to a"
                                "path containing the datasets you want to "
                                "work with.")

basedir = os.path.abspath(os.path.dirname(__file__))
sqlite_dir = os.path.join(basedir, 'sqlite')
grass_dir = os.path.join(basedir, 'grass')

if not os.path.exists(sqlite_dir):
    os.makedirs(sqlite_dir)

if not os.path.exists(grass_dir):
    os.makedirs(grass_dir)


class Config(object):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' \
                              + os.path.join(sqlite_dir, 's1_webapp.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DataPath(object):
    path = data_dir
