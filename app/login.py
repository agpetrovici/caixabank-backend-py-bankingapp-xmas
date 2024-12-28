from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = "login.login"
login_manager.login_message = "Please, log in to access this page."
