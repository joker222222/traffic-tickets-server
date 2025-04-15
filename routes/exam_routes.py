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

exam_bp = Blueprint('exam_router', __name__)


#* Получение 20 случайных вопросов из таблицы вопросы (для экзамена)
@exam_bp.route('/get_random_questions', methods=['GET'])
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
@exam_bp.route('/examId', methods=['GET'])
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
@exam_bp.route('/add_exam/<int:examId>', methods=['POST'])
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
@exam_bp.route('/get_all_exam', methods=['GET'])
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

                locale.setlocale(locale.LC_TIME, 'Russian_Russia.1251')
                formatted_date = tick.date_passage.strftime("%d %B %Y")

                response.append({
                    'id': index_global+1,
                    'tickId': tick.id,
                    'ans': corr_quest,
                    'percentages': int(percentage),
                    'timeLeft': tick.time_passage,
                    'dateLeft': formatted_date
                })

        return jsonify({"ans": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Получение отдельного билета пройденного экзамена
@exam_bp.route('/get_exam_one_ticket_user_ans/<int:exam_id>', methods=['GET'])
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

