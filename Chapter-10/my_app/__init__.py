import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration


ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

ALLOWED_LANGUAGES = {
    'en': 'English',
    'fr': 'French',
}

RECEPIENTS = ['some_receiver@gmail.com']

sentry_sdk.init(
    dsn="https://1234:5678@fake-sentry-server/1",
    integrations=[FlaskIntegration()]
)

db = SQLAlchemy()

def create_app(alt_config={}):
    app = Flask(
        __name__,
        template_folder=alt_config.get('TEMPLATE_FOLDER', 'templates')
    )

    app.config['UPLOAD_FOLDER'] = os.path.realpath('.') + '/my_app/static/uploads'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
    app.config['WTF_CSRF_SECRET_KEY'] = 'random key for form'
    app.config['LOG_FILE'] = 'application.log'

    app.config.update(alt_config)

    if not app.debug:
        import logging
        from logging import FileHandler, Formatter
        from logging.handlers import SMTPHandler
        file_handler = FileHandler(app.config['LOG_FILE'])
        app.logger.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        mail_handler = SMTPHandler(
            ("smtp.gmail.com", 587), 'sender@gmail.com', RECEPIENTS,
            'Error occurred in your application',
            ('some_email@gmail.com', 'some_gmail_password'), secure=())
        mail_handler.setLevel(logging.ERROR)
        # app.logger.addHandler(mail_handler)
        for handler in [file_handler, mail_handler]:
            handler.setFormatter(Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
            ))

    app.secret_key = 'some_random_key'

    return app

def create_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()

    return db


def get_locale():
    return g.get('current_lang', 'en')


app = create_app()
babel = Babel(app)
babel.init_app(app, locale_selector=get_locale)

from my_app.catalog.views import catalog
app.register_blueprint(catalog)

db = create_db(app)
