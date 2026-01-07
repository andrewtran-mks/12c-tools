import os
from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # Default config
    app.config.from_object("app.config.Config")

    # Instance config (per-machine overrides)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.from_pyfile("config.py", silent=True)

    # Test overrides
    if test_config:
        app.config.update(test_config)

    # Blueprints
    from app.views.main import bp as main_bp
    from app.views.inventory import bp as inventory_bp
    from app.views.rma import bp as rma_bp
    from app.views.ivs import bp as ivs_bp
    from app.views.station_tools import bp as station_tools_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(rma_bp)
    app.register_blueprint(ivs_bp)
    app.register_blueprint(station_tools_bp)

    # Ensure upload dir if configured
    uploads = app.config.get("UPLOAD_FOLDER")
    if uploads:
        os.makedirs(uploads, exist_ok=True)

    return app

def _apply_env_overrides(app: Flask) -> None:
    """
    Allow Azure App Service Configuration -> Application settings
    to override config values.
    """
    env_map = {
        "SECRET_KEY": "SECRET_KEY",
        "UPLOAD_FOLDER": "UPLOAD_FOLDER",
        "AZURE_CONNECTION_STRING": "AZURE_CONNECTION_STRING",
        "DB_PATH": "DB_PATH", 
        "IVS_DB_PATH": "IVS_DB_PATH",
        "RMA_FOLDER_TEMPLATE": "RMA_FOLDER_TEMPLATE",
        "FAILURE_ANALYSIS_FOLDER": "FAILURE_ANALYSIS_FOLDER",
        "ORIGINAL_TEST_FOLDER": "ORIGINAL_TEST_FOLDER",
    }

    for config_key, env_key in env_map.items():
        val = os.getenv(env_key)
        if val is not None and val != "":
            app.config[config_key] = val



