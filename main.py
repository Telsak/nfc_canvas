import json
from requests import post
from flask import Flask, request, jsonify
from canvasmagic import (
    check_canvas_token, get_course_assignments, get_student_info,
    get_course_info, set_assignment_completion
)

app = Flask(__name__)
NFC_DATA_FILE = 'nfc_data.json'

def read_config():
    with open('config.json', 'r') as file:
        return json.load(file)

def read_nfc_data(file_path=NFC_DATA_FILE):
    """Reads NFC data from a JSON file.

    Args:
        file_path: A string path to the JSON file to be read.

    Returns:
        A tuple containing:
        - A boolean indicating the success status of the operation.
        - A dictionary with the contents read from the file, or an empty dict
          if an error occurs.
        - A string message indicating the result of the operation.
    """
    try:
        with open(file_path, 'r') as nfc_file:
            return json.load(nfc_file)
    except FileNotFoundError:
        return dict()
    except json.JSONDecodeError as e:
        return dict()

def write_nfc_data(nfc_data, file_path=NFC_DATA_FILE):
    """Writes NFC data to a JSON file.

    Args:
        nfc_data: A dictionary containing NFC data to be written to the file.
        file_path: A string path to the JSON file to be written.

    Returns:
        A tuple containing:
        - A boolean indicating the success status of the write operation.
        - A string message indicating the result of the operation.
    """
    try:
        with open(file_path, 'w') as file:
            json.dump(nfc_data, file, indent=2)
            return True
    except IOError as e:
        return False

app.config['SETTINGS'] = read_config()

def log_webhook(msg='Null'):
    url = app.config['SETTINGS']['base']['logging']['WEBHOOK']
    post(url, json={"username": 'autograde: NFC_API-Grade', "content": msg})

app.config['BASE'] = 'https://hv.instructure.com/api/v1/'
app.config['NFC_DATA'] = read_nfc_data()

@app.route("/nfc", methods=['POST'])
def nfc():
    response = request.json
    token = response["token"]

    if check_canvas_token(token):
        nfc_users = app.config['NFC_DATA']
        data = response["data"]
        if response["action"] == "check":
            if data in nfc_users:
                return jsonify({"status": "check_success", "data": nfc_users[data]}), 200
            else:
                return jsonify({"status": "success", "data": "Unknown ID"}), 200
        elif response["action"] == "register":
            full_name = get_student_info(token, response["payload"][1], response["payload"][0])[1]
            payload = {
                "login_id": response["payload"][0],
                "name": full_name
            }
            app.config['NFC_DATA'][data] = payload
            if write_nfc_data(app.config['NFC_DATA']):
                return jsonify({"status": "register_success", "data": nfc_users[data]}), 200
            else:
                return jsonify({"status": "register_failed", "data": nfc_users[data]}), 500
        elif response["action"] == "get_labs":
            course_id = response["data"]
            assignments = get_course_assignments(course_id, token)
            return jsonify({"status": "query_success", "data": assignments}), 200
        elif response["action"] == "mark_completed":
            data = response["payload"]
            course_id = data["course"]
            student_id = get_student_info(token, course_id, nfc_users[response["data"]]["login_id"])[0]
            assignment = (data["assignment"]["id"], str(data["assignment"]["points"]))
            canvas_response = set_assignment_completion(token, course_id, assignment, student_id)
            if canvas_response[0] == True:
                course_name = get_course_info(token, course_id)["name"]
                log_webhook(
                    msg=f'{nfc_users[response["data"]]["name"]} : User clear lab {assignment}, course {course_name}'
                )
                return jsonify({"status": "mark_completed_success", "data": assignment}), 200
            else:
                return jsonify({"status": "failed", "data": "Failed to mark Lab Complete"})
        else:
            return jsonify({"status": "forbidden", "data": "Invalid Action"}), 400
    else:
        return jsonify({"status": "forbidden", "data": "Invalid Token Provided"}), 403

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')