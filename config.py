import os

class Config:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    

    SECRET_KEY = ('zhulikiettttta')
    JWT_SECRET = ('blog_platform_mega_super_style_shhhet')
    JWT_ALGORITHM = 'HS256'

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(current_dir, 'database', 'pdd.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER_AVATAR = os.path.join(current_dir, 'static', 'avatar')
    CORS_HEADERS = 'Content-Type'