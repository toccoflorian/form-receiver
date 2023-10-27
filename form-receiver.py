from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv
import requests
from werkzeug.utils import escape
import json
import secrets
import hmac
import hashlib


def create_filename(type, given_name, family_name, date):
    return type + "___" + given_name + "-" + family_name.upper() + "___" + date[0] + "___" + date[1]


def create_file_tittle(type, given_name, family_name, date):
    return "\n\n\n" + given_name + " " + family_name.upper() + " le " + date[0] + " " + date[1] + "\n\n" + type + "\n\n\n"


def format_date(date):
    date_str = str(date).split(" ")[0].split("-")
    date_str_final = date_str[2] + "-" + date_str[1] + "-" + date_str[0]
    heure = str(date).split(" ")[1].split(".")[0]
    heure_str = heure.split(":")[0] + "h" + heure.split(":")[1]
    return [date_str_final, heure_str]


def send_data_by_email(data: str, filename: str):

    mail_user = 'formulaire@parlonspc.fr'
    api_url = os.getenv("MAILGUN_API_URL")
    api_key = os.getenv("MAILGUN_API_KEY")

    if mail_user is None or api_url is None or api_key is None:
        raise ValueError("Une variable d'environnement n'est pas définie.")

    return requests.post(
        api_url,
        auth=("api", api_key),
        data={"from": mail_user,
              "to": 't.florian181181@gmail.com;t.florian181181@gmail.com',
              "subject": filename,
              "text": data})


def format_data(data, date):
    data_str = create_file_tittle(
        data["cette-personne-veut"], data["given-name"], data["family-name"], date)
    for key in data:
        data_str += key + ":\t" + data[key] + "\n\n"

    return data_str


def save_data_manager(data):
    time = datetime.today()
    date = format_date(time)
    timestamp = int(time.timestamp())
    filename = create_filename(
        data["cette-personne-veut"], data["given-name"], data["family-name"], date)
    formated_data = format_data(data, date)
    save_data_on_json(data, filename, timestamp)
    return formated_data, filename


def sanitize_data(data):
    for i in data:
        old = data[i]
        if i == "given-name":
            data[i] = str(escape(old))[0].upper() + str(escape(old))[1:]
            continue
        if i == "family-name":
            str(escape(old)).upper()
            continue
        data[i] = str(escape(old))[0].upper() + str(escape(old))[1:]
    return data


def create_dir():
    os.mkdir("./fiches-client")
    f = open("./fiches-client/fiches.json", "w")
    f.write("{}")
    f.close()


def create_file():
    f = open("./fiches-client/fiches.json", "w")
    f.write("{}")
    f.close()


def save_data_on_json(data, filename, timestamp):
    decoupe = filename.split("___")
    client, date, heure, type = decoupe[1], decoupe[2], decoupe[3], decoupe[0]
    fiches = {
        timestamp: {
            "client": client,
            "date": date,
            "heure": heure,
            "type": type,
            "fiche": data,
            "status": False,
        }}

    if not os.path.isdir("./fiches-client"):
        create_dir()
    elif not os.path.isfile("./fiches-client/fiches.json"):
        create_file()

    with open("./fiches-client/fiches.json", "r") as file:
        fichier = file.read()
        if len(json.loads(fichier)) < 1:
            new_string = json.dumps(fiches)
        else:
            new_string = fichier[:-1] + ("," + json.dumps(fiches)[1:-1] + "}")

        file.close()

    with open("./fiches-client/fiches.json", "w") as file:
        file.write(new_string)


# recepteur formulaire
app = Flask(__name__)

CORS(app)

# receiver


@app.route('/', methods=['POST'])
def flask_receiver():

    data = request.form.to_dict()

    data = sanitize_data(data)

    formated_data, filename = save_data_manager(data)

    mail_response = send_data_by_email(formated_data, filename)

    status_code = mail_response.status_code

    return jsonify({"message": status_code})


def get_fiches_json_data():
    try:
        with open("./fiches-client/fiches.json", "r") as file:
            json_data = file.read()
            file.close()
            return json_data
    except:
        if not os.path.isdir("./fiches-client"):
            create_dir()
        elif not os.path.isfile("./fiches-client/fiches.json"):
            create_file()


def get_session_id_and_signature():
    session_id = secrets.token_hex(16)

    secret_key = os.getenv("SECRET_STRING").encode("utf-8")
    code_bytes = session_id.encode("utf-8")

    hasher = hmac.new(secret_key, code_bytes, hashlib.sha256)
    signature = hasher.hexdigest()

    with open("./session/session.json", "w") as session_file:
        session_file.write(json.dumps(session_id))
        session_file.close()

    return session_id, signature


def check_session_validity(data):
    decoupe = data.split(";")
    session_sended = ""
    signature_sended = ""
    for i in decoupe:
        if i.split("=")[0] == "session":
            session_sended = i.split("=")[1]
        elif i.split("=")[0].strip(" ") == "signature":
            signature_sended = i.split("=")[1]

    with open("./session/session.json", "r") as session_file:
        session_id = session_file.read()
        session_file.close()
    hasher = hmac.new(os.getenv("SECRET_STRING").encode(
        "utf-8"), session_sended.encode("utf-8"), hashlib.sha256)
    if session_sended == json.loads(session_id) and signature_sended == hasher.hexdigest():
        return True
    return False


# obtenir les fiches avec l'identifiant et le mot de passe puis les identifiants de session
@app.route('/get-fiches/', methods=["POST"])
def flask_sender():

    password = request.get_json()
    env_password = os.getenv("PASS")

    if password != env_password:
        pass
    else:
        session_id, signature = get_session_id_and_signature()
        data_to_send_objet = json.loads(get_fiches_json_data())
        data_to_send_objet['cookies'] = {
            "session": session_id,
            "signature": signature
        }
        data = json.dumps(data_to_send_objet)
        return jsonify(data)

    return jsonify("bad")


# obtenir les fiches avec les identifiants de session
@app.route('/getsession-fiches/', methods=['GET', "POST"])
def flask_sendersession():

    cookies = request.get_json()

    if check_session_validity(cookies):
        return jsonify(get_fiches_json_data())
    else:
        return jsonify("Des cookies de connexion sont presents mais incorrects, essayez de supprimer les cookies puis entrez le mot de passe.")


# change le status des fiches
@app.route('/set-fiche-status/', methods=["POST"])
def flask_set_fiche_status():

    fiche_id_to_change = request.get_json()

    json_fiches = get_fiches_json_data()
    fiches = json.loads(json_fiches)

    for fiche in fiches:
        # print(fiche)
        if fiche == fiche_id_to_change:
            fiches[fiche]["status"] = False if fiches[fiche]["status"] else True

    with open("./fiches-client/fiches.json", "w") as file:
        file.write(json.dumps(fiches))
        file.close()
    return jsonify("ok")


if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=False, port=6601)
    load_dotenv(".env")
