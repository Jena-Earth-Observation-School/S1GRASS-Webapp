from flask_app import app, db
from flask_app.models import Scene, Metadata, Geometry, GrassOutput

@app.shell_context_processor
def make_shell_context():
    return {'db': db,
            'Scene': Scene,
            'Metadata': Metadata,
            'Geometry': Geometry,
            'GrassOutput': GrassOutput}
