from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect

from config import Config
from models.database import Database
from routes.main import main_bp
from routes.auth import auth_bp
from routes.announcements import announcements_bp
from routes.tickets import tickets_bp
from routes.events import events_bp
from routes.verification import verification_bp
from routes.password_reset import password_reset_bp
from routes.profile import profile_bp
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    csrf.init_app(app)
    Database.init_app(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(announcements_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(verification_bp)
    app.register_blueprint(password_reset_bp)
    app.register_blueprint(profile_bp)
    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("error.html", code=500, message="Something went wrong on our side."), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

