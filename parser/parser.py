from text_f import perem
import requests, json
import ast

def remove_newlines(text: str) -> str:
    return text.replace("\n", "")

def send_ticket_to_server(ticket_id, main_json_object):
  new_lines = []
  index_id = 1
  temp_correct_answers = ''
  # new_lines.append(f"'questions': [\n")
  new_lines.append(f"[\n")
  for object in main_json_object:
    new_lines.append("{" + "\n")
    img_h = object['image']
    if img_h.find('no_image') != -1:
      new_lines.append(f"'image': '/src/assets/no_image.png'," + "\n")
    else:
      index = img_h.find('./images/A_B/') + len('./images/A_B/')
      img_s = img_h[index:]
      new_lines.append(f"'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/{img_s}?raw=true'," + "\n")
    new_lines.append(f"'text': '{remove_newlines(object['question'])}'," + "\n")

    new_lines.append(f"'answer_options': [")
    for j in object['answers']:
      new_lines.append(f"'{remove_newlines(j['answer_text'])}',")
      if j['is_correct'] == True:
        temp_correct_answers = remove_newlines(j['answer_text'])
    new_lines.append(f"]," + '\n')
    new_lines.append(f"'correct_answer': '{remove_newlines(temp_correct_answers)}'," + "\n")
    new_lines.append(f"'explanation': '{remove_newlines(object['answer_tip'])}'," + "\n")
    new_lines.append("}," + "\n")
    index_id+=1
  new_lines.append(f"]")
  
  with open('1.txt', "w", encoding="utf-8") as f:
       f.writelines(new_lines)  # Сохранение как JSON

  with open("1.txt", "r", encoding="utf-8") as file:
      content = file.read()
      data = ast.literal_eval(content)

  send_message = {
      'id': ticket_id,
      'count': 20,
      'questions': data  # Отправляем JSON, а не файловый объект
  }

  # print(send_message)

  # Отправляем POST-запрос
  response = requests.post(url='http://localhost:5000/ticket_add', json=send_message)

  # Проверяем ответ сервера
  print(response.status_code)

# 'questions': [
#                 {
#                     'text': "текст вопроса",
#                     'image': 'Изо вопроса',
#                     'answer_options': ['1', '2', '3', '4'],
#                     'correct_answer': '1',
#                     'explanation': 1
#                 }
#             ]

for i in range(40):
   send_ticket_to_server(i+1, perem[i])
