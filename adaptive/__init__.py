# Importing local modules and packages
from adaptive.models.entity_manager import EntityManager
from adaptive.blueprints.generic_blueprint import generic_blueprint
from adaptive.blueprints.teacher_blueprint import teacher_blueprint
from adaptive.blueprints.subject_blueprint import subject_blueprint
from adaptive.blueprints.student_blueprint import student_blueprint
from adaptive.blueprints.activity_blueprint import activity_blueprint

# Importing Flask's main class
from flask import Flask

# Importing the SQLAlchemy ORM
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine

# Importing libraries to load the environment variables
from dotenv import load_dotenv
from os import environ, getenv


def create_app():
    app = Flask(__name__, static_folder="assets", static_url_path="/assets")
    app.secret_key = "super secret key"

    # Getting the Groq API key (https://groq.com/) from an environment variable
    load_dotenv(dotenv_path=".env")
    environ.setdefault("GROQ_API_KEY", getenv("GROQ_API_KEY"))
    app.groq_api_key = getenv("GROQ_API_KEY")
    app.gmail_password = getenv("GMAIL_PASSWORD")
    app.gmail_address = getenv("GMAIL_ADDRESS")
    app.sender_address = getenv("SENDER_ADDRESS")
    app.carbon_copy_addresses = getenv("CARBON_COPY_ADDRESSES")

    # Defining the database connection (the database URL is hardcoded for brevity, which is not recommended)
    EntityManager.engine = create_engine("mysql+pymysql://root:root@localhost/adaptive")
    EntityManager.base.metadata.create_all(EntityManager.engine)
    EntityManager.session_maker = sessionmaker(bind=EntityManager.engine)
    # EntityManager.session = EntityManager.session_maker()
    EntityManager.session = scoped_session(EntityManager.session_maker)

    # Registering Blueprints
    app.register_blueprint(generic_blueprint)
    app.register_blueprint(teacher_blueprint)
    app.register_blueprint(subject_blueprint)
    app.register_blueprint(student_blueprint)
    app.register_blueprint(activity_blueprint)

    return app


# Exporting the app instance
app = create_app()
