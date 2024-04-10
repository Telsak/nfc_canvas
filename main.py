from requests import post
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from canvasmagic import (
    get_course_assignments, get_student_info, get_course_info, 
    set_assignment_completion
)
from config import read_config, read_nfc_data, write_nfc_data
from authmagic import register_token, check_token
from threading import Lock

app = Flask(__name__)
bcrypt = Bcrypt(app)
config_lock = Lock()

app.config['SETTINGS'] = read_config()
app.config['NFC_DATA'] = read_nfc_data(app.config['SETTINGS']['base']['nfc_file'])

def log_webhook(msg='Null'):
    url = app.config['SETTINGS']['base']['logging']['WEBHOOK']
    post(url, json={"username": 'autograde: NFC_API-Grade', "content": msg})

@app.route("/nfc", methods=['POST'])
def nfc():
    response = request.json
    token = response["token"]

    # initial fix, due to weird error with reading the token from file
    if token == app.config['SETTINGS']['base']['canvas']['TOKEN']:
        nfc_users = app.config['NFC_DATA']
        data = response["data"]
        
        if response["action"] == "register":
            full_name = get_student_info(token, response["payload"][1], response["payload"][0])[1]
            payload = {
                "login_id": response["payload"][0],
                "name": full_name
            }
            app.config['NFC_DATA'][data] = payload
            if write_nfc_data(app.config['NFC_DATA'], app.config['SETTINGS']['base']['nfc_file']):
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
                    msg=f'{nfc_users[response["data"]]["name"]} : User clear lab {data["assignment"]["name"]}, course {course_name}'
                )
                return jsonify({"status": "mark_completed_success", "data": assignment}), 200
            else:
                return jsonify({"status": "failed", "data": "Failed to mark Lab Complete"})
        else:
            return jsonify({"status": "forbidden", "data": "Invalid Action"}), 400
    else:
        return jsonify({"status": "forbidden", "data": "Invalid Token Provided"}), 403

@app.route("/check", methods=['POST'])
def check():
    '''
    if response["action"] == "check":
                if data in nfc_users:
                    return jsonify({"status": "check_success", "data": nfc_users[data]}), 200
                else:
                    return jsonify({"status": "success", "data": "Unknown ID"}), 200
    '''
    response = request.json




@app.route("/register", methods=['POST'])
def register():
    """Handles the registration process by adding a new token.

    This endpoint processes POST requests with a "token" in the JSON payload.
    Tries to register the provided token by with the `register_token` function.

    - If the token is registered, it responds with a success status.
    - If the token is invalid or the registration fails, it responds with a 
      failure status and a 401 Unauthorized status code.
    - If the request JSON does not contain a "token" field, it responds with a 
      failure status and a 400 Bad Request status code.

    Returns:
        A Flask `jsonify` response object with two keys: "status" and "data". The "status" key
        indicates the outcome ("register_success" or "failed"), and the "data" key provides
        a message about the registration attempt. The HTTP status code reflects the outcome: 200 for
        success, 401 for an invalid token, and 400 for a missing token field.
    """
    response = request.json
    if "token" in response:
        if check_token(response, app, bcrypt):
            return jsonify({    "status": "failed", "data": "Failed registration, token invalid."}), 401
        else:
            if register_token(response, app, bcrypt, config_lock):
                return jsonify({"status": "register_success", "data": "Successful registration, token added."}), 200
            else:
                return jsonify({"status": "failed", "data": "Failed registration, token invalid."}), 401
    else:
        return jsonify({"status": "failed", "data": "Failed registration, missing token field."}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
