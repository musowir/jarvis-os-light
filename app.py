#!/usr/bin/env python3
import os
from flask import Flask, render_template
from config import config_environments
from database import init_db, close_db
from core.daemon import start_ollama, init_signals

# Blueprints
from blueprints.auth.routes import auth_bp
from blueprints.chat.routes import chat_bp
from blueprints.settings.routes import settings_bp

app = Flask(__name__)

# 1. Environment Config Injection
env_state = os.environ.get("FLASK_ENV", "default")
app.config.from_object(config_environments[env_state])

# 2. Database Connection Teardown Handler Registration
app.teardown_appcontext(close_db)

app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(settings_bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        init_db(app) # Build safe tables using configuration context paths
        
    init_signals()
    start_ollama()
    app.run(host='0.0.0.0', port=8080, threaded=True)
