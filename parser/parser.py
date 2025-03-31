from text_f import main_json_object
# {
#         img: 'https://storage.yandexcloud.net/pddlife/abm/n14_2.jpg',
#         questionId: 1,
#         question: 'Какой знак запрещает движение?',
#         answers: [
#           {
#             answerText:'Остановившись непосредственно перед пешеходным переходом, чтобы уступить дорогу пешеходу',
#             isCorrect: false,
#             isChoice: false,
#           },
#           {
#             answerText:'Остановившись на проезжей части из-за технической неисправности транспортного средства',
#             isCorrect: true,
#             isChoice: false,
#           },
#           {
#             answerText: 'В обоих перечисленных случаях',
#             isCorrect: false,
#             isChoice: false,
#           },
#         ],
#         correctAnswer: 'Остановившись на проезжей части из-за технической неисправности транспортного средства',
#         helpAnswer: '«Вынужденная остановка» - прекращение движения транспортного средства, связанное с его технической неисправностью, опасностью, создаваемой перевозимым грузом, состоянием водителя (пассажира) или появления препятствия на дороге.(Пункт 1.2 ПДД, термин «Вынужденная остановка»)',
#       },


# 'questions': [
#                 {
#                     'text': "текст вопроса",
#                     'image': 'Изо вопроса',
#                     'answer_options': ['1', '2', '3', '4'],
#                     'correct_answer': '1',
#                     'explanation': 1
#                 },
#                 {
#                     'text': "текст вопроса2",
#                     'image': 'Изо вопроса2',
#                     'answer_options': ['1', '2', '3', '4'],
#                     'correct_answer': '3',
#                     'explanation': 1
#                 }
#             ]

new_lines = []
index_id = 1
temp_correct_answers = ''
new_lines.append(f"'questions': [\n")
for i in main_json_object:
  new_lines.append("{" + "\n")
  img_h = i['image']
  if img_h.find('no_image') != -1:
    new_lines.append(f"'image': 'https://storage.yandexcloud.net/pddlife/no_picture.png'," + "\n")
  else:
    index = img_h.find('./images/A_B/') + len('./images/A_B/')
    img_s = img_h[index:]
    new_lines.append(f"'image': 'https://github.com/etspring/pdd_russia/blob/master/images/A_B/{img_s}?raw=true'," + "\n")
  # new_lines.append(f"questionId: {index_id}," + "\n")
  new_lines.append(f"'text': '{i['question']}'," + "\n")

  new_lines.append(f"'answer_options': [")
  for j in i['answers']:
    new_lines.append(f"'{j['answer_text']}',")
    if j['is_correct'] == True:
      temp_correct_answers = j['answer_text']
  new_lines.append(f"]," + '\n')
  new_lines.append(f"'correct_answer': '{temp_correct_answers}'," + "\n")
  new_lines.append(f"'explanation': '{i['answer_tip']}'," + "\n")
  new_lines.append("}," + "\n")
  index_id+=1
new_lines.append(f"]")
with open('parser/1.txt', "w", encoding="utf-8") as f:
    f.writelines(new_lines)