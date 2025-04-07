import os

class Config:
    current_dir = os.path.dirname(os.path.abspath(__file__))   #* Текущая директория
    
    database_name = 'pdd.db'                             #* Текущее название БД

    SECRET_KEY = ('secret_key974397843898934')                 #* Создание секретов для токена
    JWT_SECRET = ('77238328828238')
    JWT_ALGORITHM = 'HS256'

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(current_dir, 'database', database_name)}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER_AVATAR = os.path.join(current_dir, 'static') #* Папка для аватарок (файлов)
    CORS_HEADERS = 'Content-Type'