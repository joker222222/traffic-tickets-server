import warnings
warnings.filterwarnings("ignore", message="Using the in-memory storage for tracking rate limits")

from flask_cors import CORS
from flask import Flask
from config import Config
from routes.user_routes import user_bp
from routes.admin_routes import admin_bp
from routes.exam_routes import exam_bp
from routes.marathon_routes import marathon_bp
from routes.ticket_routes import ticket_bp
from routes.news_routes import news_bp


app = Flask(__name__)
CORS(app)

app.config.from_object(Config)

array_router = [user_bp, admin_bp, exam_bp, marathon_bp, ticket_bp, news_bp]

# Регистрация маршрутов
for router in array_router:
  app.register_blueprint(router)

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
