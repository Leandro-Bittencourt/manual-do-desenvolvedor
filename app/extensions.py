from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = "auth.entrar"
login_manager.login_message = "Entre na sua conta para continuar."
login_manager.login_message_category = "aviso"
