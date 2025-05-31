from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager

mongo = PyMongo()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure key
    app.config['MONGO_URI'] = 'mongodb://localhost:27017/attendance_db'
    
    mongo.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    
    from .routes import main
    app.register_blueprint(main)
    
    return app