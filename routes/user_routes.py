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

user_bp = Blueprint('user_router', __name__)


#! Главный раздел
#* Подраздел
#TODO: Дописать функцию
#? Вопрос по этой части


#! AuthController – управление регистрацией, авторизацией и выходом пользователей;

#* Авторизация
@user_bp.route('/sign-in', methods=['POST'])
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
@user_bp.route('/sign-up', methods=['POST'])
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
@user_bp.route('/profile', methods=['GET'])
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

#* Получение аватара
@user_bp.route('/avatar', methods=['GET'])
def get_photo():
    file_path = os.path.join(Config.current_dir, "static\\avatar\\empty.jpg")
    return send_file(file_path)

#* Проверка токена
@user_bp.route('/token_check', methods=['POST'])
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

#* Получение билета
@user_bp.route('/ticket/<int:id_ticket>', methods=['GET'])
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

#* Количество билетов
@user_bp.route('/ticket_count', methods=['GET'])
def get_ticket_count():
    session = Session()
    try:
        ticket_count = session.query(Ticket).count()  # Оптимизированный запрос
        return jsonify({"ticket_count": ticket_count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Получение правильного ответа
@user_bp.route('/ticket/check_answer/<int:questionId>', methods=['GET'])
def get_correct_ans(questionId):
    session = Session()
    try:
        question = session.query(Question).filter_by(id=questionId).first()  # Оптимизированный запрос
        return jsonify({"correct_ans": question.correct_answer, 'explanation': question.explanation}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


#! TestController – обработка тестирования, отправка ответов и получение результатов;

#* Занесение статистики пользователя
@user_bp.route('/update_ticket_user_ans/<int:ticket>', methods=['POST'])
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
            test_res.correct_questions = str(data['ans']).strip()
        session.commit()
        return jsonify({"correct_ans": data['ans']}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Получение статистики пользователя
@user_bp.route('/get_ticket_user_ans', methods=['GET'])
@token_required
def get_user_all_ticket_stats():
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
                    'percentages': 0
                })
            else:
                def calculate_correct_percentage(answers: list) -> float:
                    if not answers:
                        return 0.0  # Если список пуст, возвращаем 0%
                    
                    correct_count = sum(1 for ans in answers if ans["ans_correct"])
                    total_count = len(answers)
                    
                    return (correct_count / total_count) * 100
                
                corr_quest = res.correct_questions
                corr_quest = ast.literal_eval(corr_quest)
                percentage = calculate_correct_percentage(corr_quest)
                response.append({
                    'id': i+1,
                    'ans': res.correct_questions,
                    'percentages': int(percentage)
                })

        return jsonify({"ans": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Получение отдельного билета у пользователя
@user_bp.route('/get_one_ticket_user_ans/<int:ticket_id>', methods=['GET'])
@token_required
def get_user_one_ticket_stats(ticket_id):
    session = Session()
    try:
        token = request.headers.get('Authorization')
        token_data = decode_token(token)
        res = session.query(TestResult).filter_by(user_id=token_data['id'], ticket_id=ticket_id).first()
        if res is None:
            return jsonify({"error": 'Invalid ticket_id'}), 400
        else:
            corr_quest = ast.literal_eval(res.correct_questions)
        return jsonify({"message": corr_quest}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


#! QuestionController – управление базой вопросов (добавление, изменение, удаление);

#* Добавление билета
@user_bp.route('/ticket_add', methods=['POST'])
def add_ticket():
    session = Session()
    try:
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
                answer_options='>;'.join(i['answer_options']), 
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


#! NewsController – управление новостями платформы.

#* Добавление новости
@user_bp.route('/new/add_new', methods=['POST'])
def add_new():
    session = Session()
    try:
        data = request.json

        new_new = News(
            image=str(data['image']).strip(), 
            text=str(data['count']).strip()
        )
        session.add(new_new)
        session.flush()
        return jsonify({"message": "New successfully added"}), 200 
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Получение всех новостей (неавторизованного пользователя)
@user_bp.route('/get_all_news_unauth', methods=['GET'])
def get_all_news_unauth():
    session = Session()
    try:
        count_news = session.query(News).order_by(desc(News.id)).all()
        response = []
        for i in count_news:
            response.append({
                'img': i.image,
                'text': i.text,
                'likes': len(session.query(Like).filter_by(news_id=i.id, reaction='like').all()),
                'dislikes': len(session.query(Like).filter_by(news_id=i.id, reaction='dislike').all()),
                'userReaction': None,
                'showLoginMessage': False,
                'postId': i.id
            })
        return jsonify({"message": response}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Получение всех новостей (авторизованного пользователя)
@user_bp.route('/get_all_news_authorized', methods=['GET'])
@token_required
def get_all_news_authorized():
    session = Session()
    try:
        token = request.headers.get('Authorization')
        token_data = decode_token(token)
        count_news = session.query(News).order_by(desc(News.id)).all()
        response = []
        for i in count_news:
            react_user = session.query(Like).filter_by(news_id=i.id, user_id=token_data['id']).first()
            react_user = react_user.reaction if react_user else None
            response.append({
                'img': i.image,
                'text': i.text,
                'likes': len(session.query(Like).filter_by(news_id=i.id, reaction='like').all()),
                'dislikes': len(session.query(Like).filter_by(news_id=i.id, reaction='dislike').all()),
                'userReaction': str(react_user),
                'showLoginMessage': False,
                'postId': i.id
            })
        return jsonify({"message": response}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Изменение реакции под новостью (лайк, дизлайк, None)
@user_bp.route('/set_status_post', methods=['POST'])
@token_required
def set_status_post():
    session = Session()
    try:
        data = request.json
        token = request.headers.get('Authorization')
        token_data = decode_token(token)
        new = session.query(Like).filter_by(news_id=data['id'], user_id=token_data['id']).first()
        if new is None:
            new_status = Like(
                news_id=data['id'],
                user_id=token_data['id'],
                reaction=data['reaction']
            )
            session.add(new_status)
            session.flush()
        else:
            new.reaction = data['reaction']
        session.commit()    
        return jsonify({"message": 'Status changed'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


#! ExamController – реализация режима экзамена с временным ограничением;

#* Получение 20 случайных вопросов из таблицы вопросы (для экзамена)
@user_bp.route('/get_random_questions', methods=['GET'])
def get_random_questions():
    session = Session()
    try:
        subquery = (
            session.query(Question.id)
            .order_by(func.random())
            .limit(20)
            .subquery()
        )

        random_questions = (
            session.query(Question)
            .join(subquery, Question.id == subquery.c.id)
            .all()
        )
        response = []
        for (i, question) in enumerate(random_questions):
            response.append({
                    'img': question.image,
                    'questionId': i+1,
                    'id': question.id,
                    'question': question.text,
                    'answers': question.answer_options.split('>;')
                })
        return jsonify({"questions": response}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Получение id последнего экзамена
@user_bp.route('/examId', methods=['GET'])
@token_required
def examId():
    session = Session()
    try:
        token = request.headers.get('Authorization')
        token_data = decode_token(token)
        last_result_id = (
                session.query(ResultsExam)
                .filter_by(user_id=token_data['id'])
                .order_by(ResultsExam.id.desc())
                .first()
            )
        response = 0
        if (last_result_id):
            response = last_result_id.id + 1
        return jsonify({"message": response}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Занесение статистики пользователя (Экзамен)
@user_bp.route('/add_exam/<int:examId>', methods=['POST'])
@token_required
def add_exam(examId):
    session = Session()
    try:
        token = request.headers.get('Authorization')
        token_data = decode_token(token)
        data = request.json
        params = ['ans']
        if not all(param in data for param in params):
            return jsonify({"error": "Invalid data"}), 400 
        test_res = session.query(ResultsExam).filter_by(user_id=token_data['id'], id=examId).first()
        if test_res is None:
            new_test_res = ResultsExam(
                    user_id=token_data['id'], 
                    time_passage=data['timeLeft'])
            session.add(new_test_res)
            session.flush()
            for item in data['ans']:
                new_ans = ExamAnswers(
                    exam_id = new_test_res.id,
                    id_questions = item['ans_id'],
                    user_answer = item['ans_choice'],
                    correct_answer = item['ans_correct']
                )
                session.add(new_ans)

            session.commit()
        return jsonify({"message": 'Ok'}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Получение статистики пользователя (Экзамен)
@user_bp.route('/get_all_exam', methods=['GET'])
@token_required
def get_all_exam():
    session = Session()
    try:
        token = request.headers.get('Authorization')
        token_data = decode_token(token)

        count_ticket = session.query(ResultsExam).filter_by(user_id=token_data['id']).all()
        response = []
        for (index_global, tick) in enumerate(count_ticket):
            res = session.query(ExamAnswers).filter_by(exam_id=tick.id).all()
            if not res is None:
                corr_quest = []
                for (index, item) in enumerate(res):
                    corr_quest.append({
                        'ans_id': index,
                        'ans_correct': item.correct_answer,
                        'ans_choice': item.user_answer
                        })
                def calculate_correct_percentage(answers: list) -> float:
                    if not answers:
                        return 0.0 
                    
                    correct_count = sum(1 for ans in answers if ans["ans_correct"])
                    total_count = len(answers)
                    
                    return (correct_count / total_count) * 100
                
                percentage = calculate_correct_percentage(corr_quest)
                response.append({
                    'id': index_global+1,
                    'tickId': tick.id,
                    'ans': corr_quest,
                    'percentages': int(percentage),
                    'timeLeft': tick.time_passage,
                    'dateLeft': tick.date_passage
                })

        return jsonify({"ans": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Получение отдельного билета пройденного экзамена
@user_bp.route('/get_exam_one_ticket_user_ans/<int:exam_id>', methods=['GET'])
@token_required
def get_exam_one_ticket_user_ans(exam_id):
    session = Session()
    try:
        token = request.headers.get('Authorization')
        token_data = decode_token(token)
        res = session.query(ResultsExam).filter_by(user_id=token_data['id'], id=exam_id).first()
        corr_quest = []
        if not res is None:
            res_ans = session.query(ExamAnswers).filter_by(exam_id=res.id).all()
            if not res_ans is None:
                for (index, item) in enumerate(res_ans):
                    corr_quest.append({
                        'ans_id': index,
                        'ans_correct': item.correct_answer,
                        'ans_choice': item.user_answer
                        })

            # corr_quest = ast.literal_eval(res.correct_questions)
        return jsonify({"message": corr_quest}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


#! LearningController – доступ к теоретическим материалам и разбору ошибок;


#! ProfileController – редактирование профиля пользователей;


#! AnalyticsController – анализ статистики пользователей и тестов;

