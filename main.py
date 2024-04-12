from authmagic import register_token, check_token, get_token_from_header
from canvasmagic import (
    get_course_assignments, get_student_info, get_course_info, 
    set_assignment_completion
)
from config import read_config, read_nfc_data, write_nfc_data
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from nfcmagic import get_userinfo
from requests import post
from threading import RLock

app = Flask(__name__)
bcrypt = Bcrypt(app)
config_lock = RLock()

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
        return jsonify({"status": "forbidden", "data": "Invalid Token Provided"}), 401

@app.route("/check", methods=['POST'])
def check():
    """Checks if a NFC ID matches a registered user based on a valid token.

    This endpoint processes POST requests containing a JSON payload with a 
    "token" field and an "nfc_id". It first verifies the validity of the 
    provided token. If valid, it proceeds to check if the given NFC ID matches
    a registered user by calling `get_userinfo`.
    
    If a matching user is found, it returns a success status with the user's 
    username and full name. If no matching user is found, it still returns a 
    success status but with a message stating that no matching user was found.
    If the token provided is invalid, it returns a failure status.
    If the request is missing a "token" field, it returns a forbidden status.

    Returns:
        A Flask `jsonify` response object with a HTTP status code.  
        The HTTP status codes are 200 for successes, 401 for invalid token, 
        and 400 for missing token field.
    """    
    response = request.json
    token = get_token_from_header()
    if token and check_token(token, app, bcrypt):
        status, userinfo = get_userinfo(app, response["nfc_id"])
        # status = user found true/false
        if status:
            return jsonify({
                "status": "success", 
                "data": {
                    "username": userinfo[0], 
                    "full_name": userinfo[1]["full_name"]
                }
            }), 200
        else:
            return jsonify({
                "status": "success", 
                "message": "No matching user found."
            }), 200
    else:
        return jsonify({
            "status": "failed", 
            "data": "Invalid token provided"
        }), 401

@app.route("/register/token", methods=['POST'])
def register_token_route():
    """Handles the registration process by adding a new token.

    This endpoint processes POST requests with a "token" in the JSON payload.
    Tries to register the provided token by with the `register_token` function.

    - If the token is registered, it responds with a success status.
    - If the token is invalid or the registration fails, it responds with a 
      failure status and a 401 Unauthorized status code.
    - If the request JSON does not contain a "token" field, it responds with a 
      failure status and a 400 Bad Request status code.

    Returns:
        A Flask `jsonify` response object with a HTTP status code.
        The HTTP status code are 200 for success, 401 for an invalid token, 
        and 400 for a missing token field.
    """
    token = get_token_from_header()
    if token:
        response = register_token(token, app, bcrypt, config_lock)
        if response == "registered":
            return jsonify({
                    "status": "success", 
                    "message": "Token successfully registered."
                }), 200
        elif response == "updated":
            return jsonify({
                "status": "success", 
                "message": "Token already registered; last verified timestamp updated."
            }), 200
        else:
            return jsonify({
                "status": "failed", 
                "message": "Failed registration, token invalid or user profile could not be retrieved."
            }), 401
    else:
        return jsonify({
            "status": "failed", 
            "data": "Failed action, missing token field."
        }), 400

@app.route("/register/nfcid", methods=["POST"])
def register_nfcid_route():
    token = get_token_from_header()
    if token:
        # logic for registering a nfcid (serial no. of mifare card)
        # take the login_id, a course_id and the nfc_id
        # the course_id is so we potentially can look up the students info
        # in a course the teacher can see.
        # check if the login_id already exists in the datastore
        # yes -> update the login_id with the new nfc_id if the nfc_id has changed
        # no -> do a canvas lookup on a course with the login_id to get the
        #       specific student_id and full name in canvas.
        # encrypt the student_id with cryptograhy.fernet (keep a key in a locked-down file)
        # save the nfc_id, full_name, f_student_id in nfc_users.json

        response = register_nfcid(token, nfc_id, app, bcrypt, config_lock)
    
    else:
        return jsonify({
            "status": "failed", 
            "data": "Failed action, missing token field."
        }), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
