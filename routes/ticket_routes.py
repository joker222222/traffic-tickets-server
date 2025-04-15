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

ticket_bp = Blueprint('ticket_router', __name__)

#* Получение билета
@ticket_bp.route('/ticket/<int:id_ticket>', methods=['GET'])
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
@ticket_bp.route('/ticket_count', methods=['GET'])
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
@ticket_bp.route('/ticket/check_answer/<int:questionId>', methods=['GET'])
def get_correct_ans(questionId):
    session = Session()
    try:
        question = session.query(Question).filter_by(id=questionId).first()  # Оптимизированный запрос
        return jsonify({"correct_ans": question.correct_answer, 'explanation': question.explanation}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Занесение статистики пользователя
@ticket_bp.route('/update_ticket_user_ans/<int:ticket>', methods=['POST'])
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
@ticket_bp.route('/get_ticket_user_ans', methods=['GET'])
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
@ticket_bp.route('/get_one_ticket_user_ans/<int:ticket_id>', methods=['GET'])
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

#* Добавление билета
@ticket_bp.route('/ticket_add', methods=['POST'])
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


