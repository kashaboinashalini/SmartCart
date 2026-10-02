import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask

BASE = Path(__file__).resolve().parent.parent
load_dotenv(BASE / '.env')

def create_app():
    from .db import close_db, init_db
    from .routes import api

    app = Flask(__name__, static_folder='static', template_folder='templates')
    secret_key = os.getenv('SECRET_KEY')
    production = os.getenv('APP_ENV') == 'production' or bool(
        os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_ENVIRONMENT_NAME')
    )
    if production and not secret_key:
        raise RuntimeError('Set SECRET_KEY in the Railway service variables before deployment.')
    app.config['SECRET_KEY'] = secret_key or 'change-this-secret-in-production'
    app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = production
    init_db()
    app.teardown_appcontext(close_db)
    app.register_blueprint(api, url_prefix='/api')

    @app.get('/')
    def index():
        from flask import render_template
        return render_template('index.html')

    @app.get('/<path:path>')
    def spa(path):
        from flask import render_template
        return render_template('index.html')

    return app
