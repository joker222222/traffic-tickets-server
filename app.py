import warnings
warnings.filterwarnings("ignore", message="Using the in-memory storage for tracking rate limits")

from flask_cors import CORS
from flask import Flask
from config import Config
from routes.user_routes import user_bp

app = Flask(__name__)
CORS(app)

app.config.from_object(Config)

# Регистрация маршрутов
app.register_blueprint(user_bp)

if __name__ == '__main__':
  from waitress import serve
  serve(app,
      host="0.0.0.0",
      port=5000,
      threads=8,
      connection_limit=100,
      channel_timeout=60,
      backlog=128)
  # app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
