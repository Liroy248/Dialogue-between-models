from openai import OpenAI
import urllib.request
import json
from pydub import AudioSegment
import os
import assemblyai as aai
import winsound
import wave
import tempfile
import subprocess



client = OpenAI(api_key="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")
aai.settings.api_key = "7c2fad12590a42d6802f149b24be318b"

def normalizeTranscript(obj):
    arr = obj.words
    mess = ''
    for word in arr:
        mess += f'{word.text} '

    return f"{mess}\n"

abon_requests = [{"role": "system", "content": """
Ты абонент компании Triolan, и на данный момент ты не знаешь никаких заготовленных ответов, фантазируй, не расписуй свой ответ, говори кратко и по существу
"""}]

oper_requests = [{"role":"system", "content":"""
Ты оператор комании Triolan, проводишь опрос по узнаваемости бренда
Ты должен удостовериться что абонент на данный момент свободен и может пройти твой опрос
Далее узнать у абонента где они видели рекламу нашей компании, вот пример того какие результаты уже были:
В доме - Наклейки
В доме - Бумажный буклет
В доме - Таблички на подъездах
На улице - Билборд
В интернете - Ютуб
На улице - Авто сотрудника
На улице - Форма сотрудника
В интернете - Окружной ТГ канал
В интернете - ФБ
На улице - Бумажный буклет
                  
Постараться максимально классифицировать ответ абонента, в ином случае создать свою классификацию

Закончив опрос ответь абоненту следующее: "Спасибо за уделённое время, хорошего дня!"
                  
Ты начинаешь диалог
"""},]

analys_request = [{"role":"system", "content":"""
Ты должен обработать диалог между оператором и абонентом и дать 2 показателя используя только такие классификации:
Как абонент вспомнил где видел рекламму:
                    Вспомнили с подсказками
                    Не видели
                    Вспомнили сами
Где видел рекламму:
                    В доме - Наклейки
                    В доме - Бумажный буклет
                    В доме - Таблички на подъездах
                    На улице - Билборд
                    В интернете - Ютуб
                    На улице - Авто сотрудника
                    На улице - Форма сотрудника
                    В интернете - Окружной ТГ канал
                    В интернете - ФБ
                    На улице - Бумажный буклет
"""},{}]

abon_answers = []
oper_answers = []

dialog = ""

from pathlib import Path

path = Path("Dialogs")
for x in path.rglob("*"):
    print(x)
i=0
inputVar = int(input("1 - Для анализа диалога между моделями GPT\n"))
from elevenlabs.client import ElevenLabs
clientEL = ElevenLabs(
    api_key="0515e60b65e73f1672a6fb6bd95518f7"
)
if inputVar == 1:
    while True:
        oper_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=oper_requests,
            max_tokens=4096,
            temperature=.6
        )
        oper_answers.append(oper_response.choices[0].message.content)
        oper_requests.append({'role':'assistant','content':oper_answers[len(oper_answers)-1]})
        abon_requests.append({'role':"user","content":oper_answers[len(oper_answers)-1]})

        dialog+=f"Оператор\n{oper_response.choices[0].message.content}\n"
        operVoice = clientEL.generate(
                text=f"{oper_response.choices[0].message.content}",
                voice="Adam",
                model="eleven_multilingual_v2",
                output_format="mp3_44100_128"
                )
        with open(f'Voice acting/output{i}.mp3', 'wb') as f:
            for chunk in operVoice:
                f.write(chunk)
        i=i+1

        abon_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=abon_requests,
                max_tokens=4096,
                temperature=1
        )
        abon_answers.append(abon_response.choices[0].message.content)
        abon_requests.append({'role':'assistant','content':abon_answers[len(abon_answers)-1]})
        oper_requests.append({'role':'user','content':abon_answers[len(abon_answers)-1]})
        
        dialog+=f"{abon_response.choices[0].message.content}"
        abonVoice = clientEL.generate(
                text=f"Абонент\n{abon_response.choices[0].message.content}\n",
                voice="Rachel",
                model="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
        with open(f'Voice acting/output{i}.mp3', 'wb') as f:
            for chunk in abonVoice:
                f.write(chunk)

        i=i+1

        if oper_answers[len(oper_answers)-1] == "Спасибо за уделённое время, хорошего дня!":
            break
    path = Path("Voice acting")
    combined = AudioSegment.silent(duration=0)
    for x in path.rglob("*"):
        combined += AudioSegment.from_file(x)
    combined.export("combined_audio.mp3", format="mp3")
    file = open("txt.txt","w",encoding="utf-8")
    file.write(dialog)
    file.close()
else:
    config = aai.TranscriptionConfig(language_code="uk", audio_start_from=3000,dual_channel=True)
    transcriber = aai.Transcriber(config=config)
    for item in path.rglob("*"):
        normalyzeTranscriptText=''
        transcript = transcriber.transcribe(f"{item}")

        if transcript.status == aai.TranscriptStatus.error:
            print(transcript.error)
        else:
            for paragraph in transcript.get_paragraphs():
                normalyzeTranscriptText+=normalizeTranscript(paragraph)
        print(dialog,'\n\n')
        analys_request[1]={"role":"user","content":normalyzeTranscriptText}
        analys_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=analys_request,
            max_tokens=4096,
            temperature=1
        )
        
        file=open(f"Analys{i+20}.txt",'w',encoding="UTF-8")
        file.write(f"{normalyzeTranscriptText}\n********************************************\n{analys_response.choices[0].message.content}")
        file.close()
        i=i+1
    
        
winsound.MessageBeep(1)
            

