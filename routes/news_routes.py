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

news_bp = Blueprint('news_router', __name__)

#* Добавление новости
@news_bp.route('/new/add_new', methods=['POST'])
@token_required
def add_new():
    session = Session()
    try:
        data = request.json
        token_data = decode_token(request.headers.get('Authorization'))

        user = session.query(User).filter_by(id=token_data['id']).first()
        role = session.query(Role).filter_by(id=user.role_id).first()
        if (role.name != 'admin'):
            return jsonify({"error": 'No have admin'}), 500

        new_new = News(
            image=str(data['image']).strip(), 
            text=str(data['text']).strip()
        )
        session.add(new_new)
        session.commit()
        session.flush()
        return jsonify({"message": "New successfully added"}), 200 
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Удаление новости
@news_bp.route('/new/remove_new/<int:postId>', methods=['POST'])
@token_required
def remove_new(postId):
    session = Session()
    try:
        token_data = decode_token(request.headers.get('Authorization'))

        user = session.query(User).filter_by(id=token_data['id']).first()
        role = session.query(Role).filter_by(id=user.role_id).first()
        if (role.name != 'admin'):
            return jsonify({"error": 'No have admin'}), 500
        
        new  = session.query(News).filter_by(id=postId).first()
        if not new:
            return jsonify({"error": 'No post'}), 500
        
        session.delete(new)

        reactions = session.query(Like).filter_by(id=postId).all()
        if reactions:
            for item in reactions:
                session.delete(item)

        session.commit()
        session.flush()
        return jsonify({"message": "New successfully added"}), 200 
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

#* Получение всех новостей (неавторизованного пользователя)
@news_bp.route('/get_all_news_unauth', methods=['GET'])
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
@news_bp.route('/get_all_news_authorized', methods=['GET'])
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
@news_bp.route('/set_status_post', methods=['POST'])
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
