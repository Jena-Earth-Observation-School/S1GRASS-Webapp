import os

######## CHANGE DATA DIRECTORY HERE (No need to change anything else) #########

data_dir = "D:/GEO450_data"

###############################################################################

## Convert to normalized path (just in case) and print error message if it
## doesn't exist
data_dir = os.path.abspath(data_dir)

if not os.path.exists(data_dir):
    raise ImportError(f"{data_dir} does not exist. Please change the "
                      "variable 'data_dir' in 'config.py' to a"
                      "path containing the datasets you want to "
                      "work with.")

## Save sqlite and grass stuff in subdirectories of the data directory,
## so the user can also access and work with both outside of this webapp.
sqlite_dir = os.path.join(data_dir, 'sqlite')
grass_dir = os.path.join(data_dir, 'grass')
grass_dir_out = os.path.join(grass_dir, 'output')

if not os.path.exists(sqlite_dir):
    os.makedirs(sqlite_dir)
if not os.path.exists(grass_dir):
    os.makedirs(grass_dir)
if not os.path.exists(grass_dir_out):
    os.makedirs(grass_dir_out)


## Configurations that are imported in __init__.py
class Config(object):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' \
                              + os.path.join(sqlite_dir, 's1_webapp.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    os.environ['GRASSBIN'] = 'grass78'


## Save paths as classes so they can easily imported elsewhere (e.g. as
## 'Data.path' or 'Grass.path')
class Data(object):
    path = data_dir

class Grass(object):
    path = grass_dir
    path_out = grass_dir_out

class Database(object):
    path = sqlite_dir
