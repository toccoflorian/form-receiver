from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv
import requests
from werkzeug.utils import escape


def create_filename(type, given_name, family_name, date):
    return type + "-->" + given_name + "_" + family_name.upper() + "--" + date[0] + "_" + date[1]

def create_file_tittle(type, given_name, family_name, date):
    return "\n\n\n"  + given_name + " " + family_name.upper() + " le " + date[0] + " " + date[1] +"\n\n" + type +  "\n\n\n"

def format_date(date):
    date_str = str(date).split(" ")[0].split("-")
    date_str_final = date_str[2] + "-" + date_str[1] + "-" + date_str[0]
    heure = str(date).split(" ")[1].split(".")[0]
    heure_str = heure.split(":")[0] + "h" + heure.split(":")[1]
    return [date_str_final, heure_str]

def send_data_by_email(data, filename):

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

def save_data(data):
    date = format_date(datetime.today())
    filename = create_filename(data["cette-personne-veut"], data["given-name"], data["family-name"], date)
    formated_data = format_data(data, date)
    f = open(("./fiches_client/" + filename + ".txt"), "w")
    f.write(formated_data)
    f.close()
    print('saved')
    mail_response = send_data_by_email(formated_data, filename)
    if mail_response.status_code == 200:
        print("mail ok")
    return mail_response.status_code


app = Flask(__name__)


CORS(app)
#CORS(app, resources={r"/164.132.229.216": {"origins": "164.132.229.216"}})

@app.route('/', methods=['GET', 'POST'])

def index():
    data = request.form.to_dict()
    # Afficher les données reçues
    print(data)
    for i in data:
        old = data[i]
        data[i] = escape(old)
    print(data)
    status_code = save_data(data)
    return jsonify({"message": status_code})

app.run(host="127.0.0.1", debug=False, port=6600)
# if __name__ == "__main__":
