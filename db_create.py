from pyroSAR import Archive

filename = './data/Spain_Donana_2015.zip'
dbname = 'scenes.db'

with Archive(dbname) as archive:
    archive.insert(filename)

