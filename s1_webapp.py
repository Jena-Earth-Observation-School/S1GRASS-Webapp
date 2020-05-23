from flask_webapp import app, db
from flask_webapp.models import Scene, Metadata, Geometry

@app.shell_context_processor
def make_shell_context():
    return {'db': db,
            'Scene': Scene,
            'Metadata': Metadata,
            'Geometry': Geometry}
