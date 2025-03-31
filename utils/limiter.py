from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Создаём экземпляр Limiter без привязки к приложению
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per hour"])