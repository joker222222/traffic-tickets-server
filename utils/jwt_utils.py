import jwt
from config import Config
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify
import pytz  # Для работы с временными зонами

# Создание токена для входа пользователя
def encode_token(payload):
    token = jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
    return token  # Возвращаем токен как есть (он уже в виде строки, не нужно декодировать)

# Декодирование токена
def decode_token(token):
    return jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM], options={"verify_exp": True})

# Утилита для проверки JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        try:
            decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated

# Функция для получения текущего времени в московской временной зоне
def get_now_time():
    utc_now = datetime.now(timezone.utc)  # Получаем текущее время в UTC
    moscow_offset = timezone(timedelta(hours=3))  # Московское время
    moscow_time = utc_now.astimezone(moscow_offset)  # Преобразуем в московское время
    return moscow_time

# Генерация JWT токена
def generate_token(user_id, user_email, end_time):
    """Генерация JWT токена с временем истечения."""
    expiration_time = get_now_time() + timedelta(hours=end_time)  # Время истечения токена
    payload = {
        "id": user_id,
        "identifier": user_email,
        "exp": expiration_time 
    }
    return encode_token(payload)

