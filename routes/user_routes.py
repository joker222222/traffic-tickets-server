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
        data = {
            'id': 2,
            'count': 20,
            'questions': [
{
'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/1871b903ddd6b18d2bc45133234dd7fa.jpg?raw=true',
'text': 'Сколько полос для движения имеет данная дорога?',
'answer_options': ['Две','Четыре','Пять',],
'correct_answer': 'Четыре',
'explanation': 'Разделительная полоса делит дорогу на проезжие части. Данная дорога имеет две проезжие части, четыре полосы движения.(Пункт 1.2 ПДД)',
},
{
'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/f8b4d6d9f328835e3543d6ac0b5b992d.jpg?raw=true',
'text': 'Можно ли Вам въехать на мост первым?',
'answer_options': ['Можно','Можно, если Вы не затрудните движение встречному автомобилю','Нельзя',],
'correct_answer': 'Можно',
'explanation': 'Знак 2.7 «Преимущество перед встречным движением» предоставляет Вам право первым проехать через узкий участок дороги, т. е. через мост.(«Дорожные знаки», пункт 1.2 термин «Уступить дорогу»)',
},
{
'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/77fa304dc7de7bbe2eb0b0a0a1f5e0ed.jpg?raw=true',
'text': 'Разрешено ли Вам произвести остановку для посадки пассажира?',
'answer_options': ['Разрешено','Разрешено только по чётным числам месяца','Разрешено только по нечётным числам месяца','Запрещено',],
'correct_answer': 'Разрешено',
'explanation': 'Знак 3.29 «Стоянка запрещена по нечётным числам месяца» ограничивает только стоянку. Остановка в его зоне действия не запрещается в любой период времени.(«Дорожные знаки»)',
},
{
'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/0f751e9c5e75d0a7097691d052ed3a95.jpg?raw=true',
'text': 'Что запрещено в зоне действия этого знака?',
'answer_options': ['Движение любых транспортных средств','Движение всех транспортных средств со скоростью не более 20 км/ч','Движение механических транспортных средств',],
'correct_answer': 'Движение механических транспортных средств',
'explanation': 'Знак 5.33 «Пешеходная зона» обозначает место, с которого начинается территория (участок дороги), на которой разрешено движение только пешеходов и приравненных к ним лиц (это передвигающиеся в инвалидных колясках без двигателя, ведущие велосипед, мопед, мотоцикл, везущие санки, тележку, детскую и инвалидную коляску), а также велосипедистов и лицам, использующим для передвижения СИМ в случаях, установленных в пунктах 24.2, 24.3, 24.4 и 24.6 ПДД. Въезд в обозначенную зону и соответственно движение в ней любых механических транспортных средств запрещено.("Дорожные знаки", термин "Пешеход" п. 1.2 ПДД)',
},
{
'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/bbec994b533287b90e72eb935af6e333.jpg?raw=true',
'text': 'Разрешен ли Вам выезд на полосу с реверсивным движением, если реверсивный светофор выключен?',
'answer_options': ['Разрешен','Разрешен, если скорость автобуса менее 30 км/ч','Запрещен',],
'correct_answer': 'Запрещен',
'explanation': 'При выключенных сигналах реверсивного светофора, который расположен над полосой, обозначенной с обеих сторон разметкой 1.9, въезд на эту полосу запрещен.(Пункт 6.7 ПДД)',
},
{
'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/d67f11a6e67191503276e8e32a58f4f4.jpg?raw=true',
'text': 'Информационная световая секция в виде силуэта пешехода и стрелки с мигающим сигналом бело-лунного цвета, расположенная под светофором, информирует водителя о том, что:',
'answer_options': ['На пешеходном переходе, в направлении которого он поворачивает, включен сигнал светофора, разрешающий движение пешеходам','На пешеходном переходе, в направлении которого он поворачивает, включен сигнал светофора, запрещающий движение пешеходам','Он поворачивает в направлении пешеходного перехода',],
'correct_answer': 'На пешеходном переходе, в направлении которого он поворачивает, включен сигнал светофора, разрешающий движение пешеходам',
'explanation': 'Информационная световая секция в виде силуэта пешехода и стрелки с мигающим сигналом бело-лунного цвета, расположенная под светофором, информирует водителя о том, что на пешеходном переходе, в направлении которого он поворачивает, включен сигнал светофора, разрешающий движение пешеходам. Направление стрелки указывает на пешеходный переход, на котором включен сигнал светофора, разрешающий движение пешеходам (п. 6.4).',
},
{
'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/73c4c907dba18267314d10a8b09aea23.jpg?raw=true',
'text': 'Поднятая вверх рука водителя легкового автомобиля является сигналом, информирующим Вас о его намерении:',
'answer_options': ['Повернуть направо','Продолжить движение прямо','Снизить скорость, чтобы остановиться и уступить дорогу мотоциклу',],
'correct_answer': 'Снизить скорость, чтобы остановиться и уступить дорогу мотоциклу',
'explanation': 'У водителя не работает световая сигнализация, поэтому он вынужден подавать соответствующие сигналы рукой. Согласно знаку 2.4 «Уступите дорогу» мотоциклист имеет преимущество. Поднятая вверх рука информирует о намерении притормозить для того, чтобы уступить дорогу мотоциклисту.(«Дорожные знаки», пункт 8.1 ПДД).',
},
{
'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/328947fa3921f7c37a9d825b2e8b030b.jpg?raw=true',
'text': 'Двигаясь по левой полосе, водитель намерен перестроиться на правую. На каком из рисунков показана ситуация, в которой он обязан уступить дорогу?',
'answer_options': ['На левом','На правом','На обоих',],
'correct_answer': 'На обоих',
'explanation': 'На левом рисунке преимущество у автомобиля, двигающегося попутно по полосе без изменения направления движения, т.е. у «хозяина полосы». Водитель, двигающийся по левой полосе уступает.На правом рисунке одновременное перестроение. Водители руководствуются «правилом правой руки», т.е. у кого помеха справа, тот и уступает. Помеха справа у водителя, двигающего также по левой полосе. Он уступает дорогу и в этой ситуации.(Пункт 8.4 ПДД)',
},
{
'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/693a2649d53e8a112f2358389b9b20f7.jpg?raw=true',
'text': 'Можно ли Вам выполнить разворот в этом месте?',
'answer_options': ['Можно','Можно только при отсутствии приближающегося поезда','Нельзя',],
'correct_answer': 'Можно',
'explanation': 'Разворот запрещён на железнодорожном переезде, границами которого являются шлагбаумы, а при их отсутствии - знаки 1.3.1 «Однопутная железная дорога» или 1.3.2 «Многопутная железная дорога». В нашем случае железнодорожный переезд без шлагбаума. Вы можете совершить разворот по указанной траектории, так как совершаете его на безопасном удалении от железнодорожных путей.(Пункт 8.11 ПДД)',
},
{
'image': 'https://storage.yandexcloud.net/pddlife/no_picture.png',
'text': 'В каких случаях разрешается наезжать на прерывистые линии разметки, разделяющие проезжую часть на полосы движения?',
'answer_options': ['Только если на дороге нет других транспортных средств','Только при движении в темное время суток','Только при перестроении','Во всех перечисленных случаях',],
'correct_answer': 'Только при перестроении',
'explanation': 'Наезжать на прерывистые линии разметки разрешается лишь при перестроении.(Пункт 9.7 ПДД)',
},
{
'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/ddd733bef00665b6608b3e08d9008821.jpg?raw=true',
'text': 'Разрешено ли Вам обогнать мотоцикл?',
'answer_options': ['Разрешено','Разрешено, если водитель мотоцикла снизил скорость','Запрещено',],
'correct_answer': 'Запрещено',
'explanation': 'Перекресток равнозначный. На равнозначных перекрёстках обгон запрещён всех видов транспорта всеми транспортными средствами. Мотоциклист притормаживает, он уступает помехе справа. То же самое делаете и Вы. В противном случае Вы нарушите и правила обгона, и правила проезда перекрёстков.(Пункты 11.4, 13.11 ПДД).',
},
{
'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/a3c10883d8f389574cb255f4d33864b0.jpg?raw=true',
'text': 'Разрешается ли Вам остановиться в указанном месте?',
'answer_options': ['Разрешается','Разрешается, если автомобиль будет находиться не ближе 5 м от края пересекаемой проезжей части','Запрещается',],
'correct_answer': 'Разрешается, если автомобиль будет находиться не ближе 5 м от края пересекаемой проезжей части',
'explanation': 'На перекрёстке с круговым движением Вы можете совершить остановку и стоянку, но при этом расстояние между остановившимся транспортным средством и краем проезжей части должно быть не менее 5 м.(Пункты 12.4, 12.5 ПДД).',
},
{
'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/d2f620a80735b4205843f9b3d26cecc6.jpg?raw=true',
'text': 'Вы намерены повернуть налево. Кому Вы должны уступить дорогу?',
'answer_options': ['Только пешеходам','Только автобусу','Автобусу и пешеходам',],
'correct_answer': 'Автобусу и пешеходам',
'explanation': 'Перекрёсток регулируемый. Знаки приоритета «не работают». При повороте налево Вы уступаете автобусу, движущемуся прямо со встречного направления, и пешеходам, переходящим проезжую часть дороги, на которую Вы поворачиваете.(Пункты 13.1, 13.3, 13.4 ПДД).',
},
{
'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/effa4b8d198a74e7eeb2460bffca22dc.jpg?raw=true',
'text': 'В каком случае Вы имеете преимущество?',
'answer_options': ['Только при повороте направо','Только при повороте налево','В обоих перечисленных случаях',],
'correct_answer': 'В обоих перечисленных случаях',
'explanation': 'Перекресток равнозначный. Водители между собой руководствуются «правилом правой руки», т. е. у кого помеха справа, тот и уступает. У Вас преимущество и при повороте направо и при повороте налево, т. е. в обоих перечисленных случаях.(Пункт 13.11 ПДД).',
},
{
'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/ac0d572e2be79ff28310b579eba034eb.jpg?raw=true',
'text': 'Обязан ли водитель мотоцикла уступить Вам дорогу?',
'answer_options': ['Обязан','Не обязан',],
'correct_answer': 'Обязан',
'explanation': 'Мотоциклист выезжает на дорогу, обозначенную знаком 5.1 «Автомагистраль», которая является главной дорогой по отношению к примыкающей. На перекрёстке неравнозначных дорог преимущество имеют транспортные средства, движущиеся по главной дороге. Мотоциклист обязан уступить Вам дорогу.(Пункты 1.2, 13.9 ПДД).',
},
{
'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/07bad44c13de4e79e02eda779e92eab6.jpg?raw=true',
'text': 'Разрешается ли водителю выполнить объезд грузового автомобиля?',
'answer_options': ['Разрешается','Разрешается, если между шлагбаумом и остановившимся грузовым автомобилем расстояние более 5 м','Запрещается',],
'correct_answer': 'Запрещается',
'explanation': 'Водитель легкового автомобиля хочет объехать стоящий перед закрытым шлагбаумом грузовик. Правила, оговаривающие порядок проезда через железнодорожный переезд, такой маневр (с выездом на полосу встречного движения) запрещают.(Пункт 15.3 ПДД).',
},
{
'image': 'https://storage.yandexcloud.net/pddlife/no_picture.png',
'text': 'В каких из перечисленных случаев запрещена буксировка на гибкой сцепке?',
'answer_options': ['Только на горных дорогах','Только в гололедицу','Только в тёмное время суток и в условиях недостаточной видимости','Во всех перечисленных случаях',],
'correct_answer': 'Только в гололедицу',
'explanation': 'Запомните этот ответ. На экзамене часто отвечают, что только на горных дорогах. Видимо, ассоциируется опасность, связанная с высотой. Правилами запрещается буксировка на гибкой сцепке только в гололедицу.(Пункт 20.4 ПДД).',
},
{
'image': 'https://storage.yandexcloud.net/pddlife/no_picture.png',
'text': 'Запрещается эксплуатация мототранспортных средств (категории L), если остаточная глубина рисунка протектора шин (при отсутствии индикаторов износа) составляет не более:',
'answer_options': ['0,8 мм','1,0 мм','1,6 мм','2,0 мм',],
'correct_answer': '0,8 мм',
'explanation': 'Для мототранспортных средств, относящихся к ТС категорий L, остаточная глубина рисунка протектора шин (при отсутствии индикаторов износа), должна быть не более 0,8 мм(«Перечень неисправностей» п. 5.4)',
},
{
'image': 'https://storage.yandexcloud.net/pddlife/no_picture.png',
'text': 'Исключает ли антиблокировочная тормозная система возможность возникновения заноса или сноса при прохождении поворота?',
'answer_options': ['Полностью исключает возможность возникновения только заноса','Полностью исключает возможность возникновения только сноса','Не исключает возможность возникновения сноса или заноса',],
'correct_answer': 'Не исключает возможность возникновения сноса или заноса',
'explanation': 'Антиблокировочные системы (АБС) автомобилей представляют собой системы, оснащённые устройствами управления тормозами с обратной связью, которые предотвращают блокировку колёс во время торможения, тем самым сохраняя управляемость и курсовую устойчивость. Эта система имеет «большой плюс», но имеет и «минус». При ускоренном (не экстренном) нажатии на педаль тормоза на разнородном, даже твёрдом дорожном покрытии она может сработать. В момент ее срабатывания (от 1 до 2 сек.) водитель не может повлиять на процесс торможения. Чтобы появился навык управления автомобилем при срабатывании АБС, произведите несколько «контрольных» торможений на абсолютно свободном участке дороги или территории.При прохождении поворота на автомобиль действует центробежная сила. Антиблокировочная система в таких ситуациях не может повлиять на возможность возникновения сноса или заноса.',
},
{
'image': 'https://storage.yandexcloud.net/pddlife/no_picture.png',
'text': 'В каких случаях следует начинать сердечно-легочную реанимацию пострадавшего?',
'answer_options': ['При наличии болей в области сердца и затрудненного дыхания','При отсутствии у пострадавшего сознания, независимо от наличия дыхания','При отсутствии у пострадавшего сознания, дыхания и кровообращения',],
'correct_answer': 'При отсутствии у пострадавшего сознания, дыхания и кровообращения',
'explanation': 'В комментариях ответов по медицинским вопросам для лучшего запоминания правильного ответа используется прием «ключевых слов», которые выделены в тексте шрифтом. Обратите на это внимание.Правильный ответ - при отсутствии у пострадавшего сознания, дыхания и кровообращения.',
},
]
        }

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
