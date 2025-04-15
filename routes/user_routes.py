from datetime import datetime, timedelta
from models import User, Role, Ticket, Question, TestResult, SupportChat, Like, News, TicketQuestion, ResultsExam, ExamAnswers, Session
from flask import request, jsonify, abort, Blueprint, send_file
from utils.jwt_utils import token_required, generate_token, decode_token
import os
from config import Config
import ast
from sqlalchemy.orm import aliased
from sqlalchemy.sql import func
from sqlalchemy import desc
import locale

user_bp = Blueprint('user_router', __name__)


#! Главный раздел
#* Подраздел
#TODO: Дописать функцию
#? Вопрос по этой части


#! AuthController – управление регистрацией, авторизацией и выходом пользователей;

#* Авторизация
@user_bp.route('/user/sign-in', methods=['POST'])
def login():
    session = Session()
    try:
        data = request.json
        params = ['email', 'password']
        if not all(param in data for param in params):
            return jsonify({"error": "Invalid data"}), 400 

        user = session.query(User).filter_by(email=data['email']).first()
        if user is None:
            return jsonify({"error": "No registration"}), 209
        
        if str(user.password).strip() != str(data['password']).strip():
            return jsonify({"error": "Incorrect password"}), 210 

        token = generate_token(user.id, user.email, 60)
        return jsonify({"message": "Login successful", "token": token}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Регистрация
@user_bp.route('/user/sign-up', methods=['POST'])
def signup():
    session = Session()
    try:
        data = request.json
        params = ['name', 'email', 'password']
        if not all(param in data for param in params):
            return jsonify({"error": "Invalid data"}), 400

        user = session.query(User).filter_by(email=data['email']).first()
        if not (user is None):
            return jsonify({"error": "User already exists"}), 400 

        new_user = User(name=str(data['name']).strip(), 
                        email=str(data['email']).strip(), 
                        password=str(data['password']).strip(), 
                        role_id=1)
        session.add(new_user)
        session.commit()  

        return jsonify({"message": "User has been created"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Профиль
@user_bp.route('/user/profile', methods=['GET'])
@token_required
def profile():
    session = Session()
    try:
        token = request.headers.get('Authorization')
        token_data = decode_token(token)

        user = session.query(User).filter_by(id=token_data['id']).first()
        if user is None:
            return jsonify({"error": "No found user"}), 400
        response = {
            'name': user.name,
            'email': user.email,
            'password': user.password,
            'avatar': user.avatar
        }
        return jsonify({"data": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Изменение профиля 
@user_bp.route('/user/profile-change', methods=['PUT'])
@token_required
def profile_change():
    session = Session()
    try:
        token = request.headers.get('Authorization')
        token_data = decode_token(token)

        data = request.json

        user = session.query(User).filter_by(id=token_data['id']).first()
        if user is None:
            return jsonify({"error": "No found user"}), 400
        
        user.name = data['name']
        user.email = data['email']
        user.avatar = data['avatar']
        user.password = data['password']

        session.commit()
        return jsonify({"data": 'Ok'}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


#* Получение аватара
@user_bp.route('/user/avatar', methods=['GET'])
def get_photo():
    file_path = os.path.join(Config.current_dir, "static\\avatar\\empty.jpg")
    return send_file(file_path)

#* Проверка токена
@user_bp.route('/user/token_check', methods=['POST'])
@token_required
def token_check():
    session = Session()
    try:
        token = request.headers.get('Authorization')
        token_data = decode_token(token)
        user = session.query(User).filter_by(id=token_data['id']).first()
        if user is None:
            return jsonify({"error": "No found user"}), 400

        return jsonify({"message": 'Access'}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


