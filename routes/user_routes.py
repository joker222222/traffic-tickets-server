from datetime import datetime, timedelta
from models import User, Role, Ticket, Question, TestResult, SupportChat, Like, News, TicketQuestion, Session
from flask import request, jsonify, abort, Blueprint, send_file
from utils.jwt_utils import token_required, generate_token, decode_token
import logging
from marshmallow import ValidationError
from schema.schemes import LoginSchema, KeyAddSchema, CheckVersionProgramScheme
from utils.time_zone import get_now_time, check_time
from utils.limiter import limiter
import time
import os
from config import Config
import json
from flask_cors import cross_origin

logging.basicConfig(filename='log/app.log', level=logging.INFO)

user_bp = Blueprint('user_router', __name__)

# AuthController – управление регистрацией, авторизацией и выходом пользователей;

# Авторизация
@user_bp.route('/sign-in', methods=['POST'])
@cross_origin()
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

# Регистрация
@user_bp.route('/sign-up', methods=['POST'])
@cross_origin()
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

# Профиль
@user_bp.route('/profile', methods=['GET'])
@cross_origin()
@token_required
def profile():
    session = Session()
    try:
        token = request.headers.get('Authorization')
        token_data = decode_token(token)

        user = session.query(User).filter_by(id=token_data['id']).first()
        if user is None:
            return jsonify({"error": "No found user"}), 400
        
        return jsonify({"name": user.name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# Получение аватара
@user_bp.route('/avatar', methods=['GET'])
@cross_origin()
def get_photo():
    file_path = os.path.join(Config.current_dir, "static\\avatar\\empty.jpg")
    return send_file(file_path)

# Проверка токена
@user_bp.route('/token_check', methods=['POST'])
@cross_origin()
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

# Получение билета
@user_bp.route('/ticket/<int:id_ticket>', methods=['GET'])
@cross_origin()
def get_ticket(id_ticket):
    session = Session()
    try:
        ticket = session.query(Ticket).filter_by(id=id_ticket).first()
        if not ticket:
            return jsonify({"error": "Ticket not found"}), 404
        connected = session.query(TicketQuestion).filter_by(ticket_id=id_ticket).all()
        answer = {
            'id': id_ticket,
            'questions': []
        }

        for i, item in enumerate(connected):
            question = session.query(Question).filter_by(id=item.question_id).first()
            if question:
                answer['questions'].append({
                    'img': question.image,
                    'questionId': i+1,
                    'id': question.id,
                    'question': question.text,
                    'answers': question.answer_options.split('>;'),
                    'explanation': 'None'
                })
                #     'explanation': question.explanation
                # 'correct_answer': question.correct_answer,

        return jsonify({"answer": answer}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# Добавление билета
@user_bp.route('/ticket_add', methods=['POST'])
@cross_origin()
def add_ticket():
    session = Session()
    try:
        # data = {
        #     'id': 2, # id билета
        #     'count': 20, # кол-во вопросов
        #     'questions': [
        #         {
        #         'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/1871b903ddd6b18d2bc45133234dd7fa.jpg?raw=true',
        #         'text': 'Сколько полос для движения имеет данная дорога?',
        #         'answer_options': ['Две','Четыре','Пять',],
        #         'correct_answer': 'Четыре',
        #         'explanation': 'Разделительная полоса делит дорогу на проезжие части. Данная дорога имеет две проезжие части, четыре полосы движения.(Пункт 1.2 ПДД)',
        #         }]
        # }
        data = request.json

        new_ticket = Ticket(
            id=int(str(data['id']).strip()), 
            question_count=int(str(data['count']).strip()), 
            time_limit=20
        )
        session.add(new_ticket)
        session.flush()  # Получаем ID нового билета

        for i in data['questions']:
            new_question = Question(
                text=i['text'],
                image=i['image'],
                answer_options='>;'.join(i['answer_options']),  # Если в БД `TEXT`
                correct_answer=i['correct_answer'],
                explanation=i['explanation']
            )
            session.add(new_question)
            session.flush()  # Получаем ID нового вопроса

            new_connection_ticket_question = TicketQuestion(
                ticket_id=new_ticket.id,
                question_id=new_question.id
            )
            session.add(new_connection_ticket_question)

        session.commit()
        return jsonify({"name": new_ticket.id}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()

# Количество билетов
@user_bp.route('/ticket_count', methods=['GET'])
@cross_origin()
def get_ticket_count():
    session = Session()
    try:
        ticket_count = session.query(Ticket).count()  # Оптимизированный запрос
        return jsonify({"ticket_count": ticket_count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# Получение правильного ответа
@user_bp.route('/ticket/check_answer/<int:questionId>', methods=['GET'])
@cross_origin()
def get_correct_ans(questionId):
    session = Session()
    try:
        question = session.query(Question).filter_by(id=questionId).first()  # Оптимизированный запрос
        return jsonify({"correct_ans": question.correct_answer, 'explanation': question.explanation}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# Занесение статистики пользователя
@user_bp.route('/update_ticket_user_ans/<int:ticket>', methods=['POST'])
@cross_origin()
@token_required
def update_user_stat(ticket):
    session = Session()
    try:
        token = request.headers.get('Authorization')
        token_data = decode_token(token)
        data = request.json
        params = ['ans']
        if not all(param in data for param in params):
            return jsonify({"error": "Invalid data"}), 400 
        test_res = session.query(TestResult).filter_by(user_id=token_data['id'], ticket_id=ticket).first()
        if test_res is None:
            new_test_res = TestResult(user_id=token_data['id'], 
                        ticket_id=ticket, 
                        correct_questions=str(data['ans']).strip())
            session.add(new_test_res)
        else:
            test_res.correct_questions = data['ans']
        session.commit()
        return jsonify({"correct_ans": data['ans']}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# Получение статистики пользователя
@user_bp.route('/get_ticket_user_ans', methods=['POST'])
@cross_origin()
@token_required
def update_user11_stat():
    session = Session()
    try:
        token = request.headers.get('Authorization')
        token_data = decode_token(token)

        count_ticket = session.query(Ticket).all()
        response = []

        for i, tick in enumerate(count_ticket):
            res = session.query(TestResult).filter_by(user_id=token_data['id'], ticket_id=tick.id).first()
            if res is None:
                response.append({
                    'id': i+1,
                    'ans': 'None',
                    'percentages': '0%'
                })
            else:
                Len = len(res.correct_questions)
                count = 0
                valid_json_string = json.replace("'", '"')
                data = json.loads(valid_json_string)
                print(data)
                # for i in res.correct_questions.json():
                #     print(i)
                    # if i.ans_correct == True:
                    #     count+=1
                # percentages_count = (count / Len) * 100
                response.append({
                    'id': i+1,
                    'ans': res.correct_questions,
                    'percentages': 0
                })

        return jsonify({"ans": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# TestController – обработка тестирования, отправка ответов и получение результатов;


# LearningController – доступ к теоретическим материалам и разбору ошибок;


# AnalyticsController – анализ статистики пользователей и тестов;


# ExamController – реализация режима экзамена с временным ограничением;


# ProfileController – редактирование профиля пользователей;


# QuestionController – управление базой вопросов (добавление, изменение, удаление);


# NewsController – управление новостями платформы.
# # Маршрут для проверки токена
# @user_bp.route('/token/check', methods=['POST'])
# @limiter.limit("5 per minute")
# @token_required
# def validation_token():
#     token = request.headers.get('Authorization')
    
#     # Раскодирование токена
#     token_data = decode_token(token)
    
#     # Проверка наличия end_time
#     if 'end_time_key' not in token_data:
#         return jsonify({"error": "Invalid token: no end_time found."}), 400

#     # Проверка времени действия токена
#     current_time = check_time(token_data['end_time_key'])
    
#     if not current_time:
#         return jsonify({"error": "Key expired."}), 401

#     # Возврат остатка времени в секундах
#     return jsonify({"message": f"Time remaining: {current_time.total_seconds()} seconds"}), 200


# @user_bp.route('/key/add', methods=['POST'])
# @limiter.limit("2 per minute")
# def key_add():
#     try:
#         data = KeyAddSchema().load(request.json)
#     except ValidationError as err:
#         return jsonify({"errors": 'Invalid message.'}), 400

#     # Проверка прав администратора
#     if data['admin'] != 'admin' or data['password'] != 'intokeybd':
#         abort(400, description="Page not found.")

#     # Получение списка ключей
#     keys_data = data['keys']
#     if not keys_data:
#         abort(400, description="No keys provided.")

#     keys_to_add = []
#     # Обработка каждого ключа из списка
#     for line in keys_data.splitlines():
#         try:
#             key, key_time = line.split()  # Разделение ключа и времени
#             keys_to_add.append(Keys(key=key, key_time=int(key_time)))  # Создание объекта Keys
#         except ValueError:
#             continue  # Пропустить строки с неверным форматом

#     # Добавление ключей в базу
#     if keys_to_add:
#         session.bulk_save_objects(keys_to_add)  # Использование bulk_save_objects для оптимизации
#         session.commit()
#         return jsonify({"message": f"{len(keys_to_add)} keys added successfully."}), 201
#     else:
#         return jsonify({"error": "No valid keys found in input."}), 400


# @user_bp.route('/check/version', methods=['POST'])
# @limiter.limit("10 per minute")
# def check_version():
#     try:
#         data = CheckVersionProgramScheme().load(request.json)
#     except ValidationError as err:
#         return jsonify({"errors": 'Invalid message.'}), 400
#     version_program = "0.0.2"  # Меняю версию тут
#     if str(data['version']) == str(version_program):
#         return jsonify({"message": "Access is allowed."}), 200
#     return jsonify({"error": "Access is denied."}), 400
