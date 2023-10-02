from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv
import requests
from werkzeug.utils import escape
import json


def create_filename(type, given_name, family_name, date):
    return type + "___" + given_name + "-" + family_name.upper() + "___" + date[0] + "___" + date[1]

def create_file_tittle(type, given_name, family_name, date):
    return "\n\n\n"  + given_name + " " + family_name.upper() + " le " + date[0] + " " + date[1] +"\n\n" + type +  "\n\n\n"

def format_date(date):
    date_str = str(date).split(" ")[0].split("-")
    date_str_final = date_str[2] + "-" + date_str[1] + "-" + date_str[0]
    heure = str(date).split(" ")[1].split(".")[0]
    heure_str = heure.split(":")[0] + "h" + heure.split(":")[1]
    return [date_str_final, heure_str]

def send_data_by_email(data:str, filename:str):

    load_dotenv()
    mail_user = 'ParlonsPC@mail.com'
    api_url = os.getenv("MAILGUN_API_URL")
    api_key = os.getenv("MAILGUN_API_KEY")

    if mail_user is None or api_url is None or api_key is None:
        raise ValueError("Une variable d'environnement n'est pas définie.")

    return requests.post(
        api_url,
        auth=("api", api_key),
        data={"from": mail_user,
              "to": 't.florian181181@gmail.com',
              "subject": filename,
              "text": data})

def format_data(data, date):
    data_str = create_file_tittle(data["cette-personne-veut"], data["given-name"], data["family-name"], date)
    for key in data:
        data_str += key + ":\t" + data[key] + "\n\n"
        
    return data_str

def save_data_manager(data):
    date = format_date(datetime.today())
    filename = create_filename(data["cette-personne-veut"], data["given-name"], data["family-name"], date)
    formated_data = format_data(data, date)
    save_data_on_json(data, filename)
    return formated_data, filename

def sanitize_data(data):
    for i in data:
        old = data[i]
        data[i] = str(escape(old))
    return data

def create_dir():
    os.mkdir("./fiches_client")
    f=open("./fiches_client/fiches.json", "w")
    f.write("[]")
    f.close()

def create_file():
    f=open("./fiches_client/fiches.json", "w")
    f.write("[]")
    f.close()

def save_data_on_json(data, filename):
    decoupe = filename.split("___")
    client, date, heure, type = decoupe[1], decoupe[2], decoupe[3], decoupe[0]
    fiches = {
        "client": client,
        "date": date,
        "heure": heure,
        "type": type,
        "fiche": data
    }

    if not os.path.isdir("./fiches_client"):
        create_dir()
    elif not os.path.isfile("./fiches_client/fiches.json"):
        create_file()
        

    with open("./fiches_client/fiches.json", "r") as file:
        fichier = file.read()
        if len(json.loads(fichier)) < 1:
            new_string = json.dumps([fiches])
        else:
            new_string = fichier[:-1] + ("," + json.dumps(fiches) + "]")

        file.close()

    with open("./fiches_client/fiches.json", "w") as file:
        file.write(new_string)

# Flask App
app = Flask(__name__)

CORS(app)
#CORS(app, resources={r"/164.132.229.216": {"origins": "164.132.229.216"}})

@app.route('/', methods=['GET', 'POST'])

def index():

    data = request.form.to_dict()

    data = sanitize_data(data)

    formated_data, filename = save_data_manager(data)

    mail_response = send_data_by_email(formated_data, filename)

    status_code = mail_response.status_code

    if status_code == 200:
        print("mail ok")

    return jsonify({"message": status_code})

    
    # return jsonify({"message": 200})

app.run(host="127.0.0.1", debug=False, port=6600)
# if __name__ == "__main__":

# salut