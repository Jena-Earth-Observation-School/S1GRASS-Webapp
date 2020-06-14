from datetime import datetime
from flask_app import db

class Scene(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor = db.Column(db.String(3), index=True)
    orbit = db.Column(db.String(10), index=True)
    date = db.Column(db.DateTime, index=True, unique=True)
    filepath = db.Column(db.String(1000), index=True, unique=True)
    time_added = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    meta = db.relationship('Metadata', backref='s1_scene', lazy='dynamic')
    geo = db.relationship('Geometry', backref='s1_scene', lazy='dynamic')
    grass_out = db.relationship('GrassOutput', backref='s1_scene',
                                lazy='dynamic')

    def __repr__(self):
        return '<Scene {}>'.format(self.filepath)


class Metadata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scene_id = db.Column(db.Integer, db.ForeignKey('scene.id'))
    acq_mode = db.Column(db.String(2), index=True)
    polarisation = db.Column(db.String(2), index=True)
    resolution = db.Column(db.Integer)
    nodata = db.Column(db.Integer)
    band_min = db.Column(db.Float)
    band_max = db.Column(db.Float)

    def __repr__(self):
        return '<Metadata of scene {}>'.format(self.scene_id)


class Geometry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scene_id = db.Column(db.Integer, db.ForeignKey('scene.id'), index=True)
    columns = db.Column(db.Integer)
    rows = db.Column(db.Integer)
    epsg = db.Column(db.String(25), index=True)
    bounds_south = db.Column(db.Float)
    bounds_north = db.Column(db.Float)
    bounds_west = db.Column(db.Float)
    bounds_east = db.Column(db.Float)
    footprint = db.Column(db.Text)

    def __repr__(self):
        return '<Geometry of scene {}>'.format(self.scene_id)


class GrassOutput(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scene_id = db.Column(db.Integer, db.ForeignKey('scene.id'), index=True)
    description = db.Column(db.Text, index=True)
    filepath = db.Column(db.Text, index=True, unique=True)

    def __repr__(self):
        return '<GRASS output of scene {}>'.format(self.scene_id)

