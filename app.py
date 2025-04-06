import warnings
warnings.filterwarnings("ignore", message="Using the in-memory storage for tracking rate limits")

from flask_cors import CORS
from flask import Flask
from config import Config
from routes.user_routes import user_bp
from utils.limiter import limiter

app = Flask(__name__)
CORS(app)

# limiter.init_app(app)

app.config.from_object(Config)

# Регистрация маршрутов
app.register_blueprint(user_bp)

if __name__ == '__main__':
  app.run(host="0.0.0.0", port=5000, debug=True)
