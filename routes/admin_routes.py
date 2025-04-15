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

admin_bp = Blueprint('admin_router', __name__)


#* Администратор получение всех пользователей
@admin_bp.route('/admin', methods=['GET'])
@token_required
def admin_get_user():
    session = Session()
    try:
        token_data = decode_token(request.headers.get('Authorization'))
        user = session.query(User).filter_by(id=token_data['id']).first()
        if user is None:
            return jsonify({"error": "No found user"}), 400
        user_role = session.query(Role).filter_by(id=user.role_id).first()
        if user_role.name != 'admin':
            return jsonify({"error": "No have admin"}), 400
        response = []
        users = session.query(User).filter(User.id != user.id).all()
        for us in users:
            role_us = session.query(Role).filter_by(id=us.role_id).first()
            response.append({
                'id': us.id,
                'name': us.name,
                'email': us.email,
                'avatar': us.avatar,
                'password': us.password,
                'role': role_us.name
            })

        return jsonify({"data": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
   
#* Администратор изменение роли пользователю
@admin_bp.route('/admin-change-role/<int:id_user>', methods=['PUT'])
@token_required
def admin_change_role(id_user):
    session = Session()
    try:
        token_data = decode_token(request.headers.get('Authorization'))

        user = session.query(User).filter_by(id=token_data['id']).first()
        if user is None:
            return jsonify({"error": "No found user"}), 400
        
        user_role = session.query(Role).filter_by(id=user.role_id).first()
        if user_role.name != 'admin':
            return jsonify({"error": "No have admin"}), 400
        
        user_get = session.query(User).filter_by(id=id_user).first()
        if not user_get:
            return jsonify({"error": "No found user"}), 400
        if user_get.id == user.id:
            return jsonify({"error": "No change role myself"}), 400

        if user_get.role_id == 1:
            user_get.role_id = 2
        elif user_get.role_id == 2:
            user_get.role_id = 1
        
        session.commit()
        return jsonify({"data": 'Ok'}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
