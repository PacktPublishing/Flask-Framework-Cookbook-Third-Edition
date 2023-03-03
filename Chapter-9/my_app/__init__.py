import os
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel


ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

ALLOWED_LANGUAGES = {
    'en': 'English',
    'fr': 'French',
}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.realpath('.') + '/my_app/static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['WTF_CSRF_SECRET_KEY'] = 'random key for form'
db = SQLAlchemy(app)


def get_locale():
    return g.get('current_lang', 'en')


babel = Babel(app)
babel.init_app(app, locale_selector=get_locale)

app.secret_key = 'some_random_key'

from my_app.catalog.views import catalog
app.register_blueprint(catalog)

with app.app_context():
    db.create_all()
