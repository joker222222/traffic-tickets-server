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

marathon_bp = Blueprint('marathons_router', __name__)

#* Получение билетов для марафона
@marathon_bp.route('/get_marathon', methods=['GET'])
def get_marathon():
    session = Session()
    try:
        res = session.query(Question).all()
        response = []
        if not res is None:
            for (index, item) in enumerate(res):
                response.append({
                'img': item.image,
                'questionId': index+1,
                'id': item.id,
                'question': item.text,
                'answers': item.answer_options.split('>;')
            })

        return jsonify({"questions": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

