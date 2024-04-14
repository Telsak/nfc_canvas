from authmagic import register_token, check_token, get_token_from_header
from canvasmagic import (
    get_course_assignments, get_student_info, get_course_info, 
    set_assignment_completion
)
from config import read_config, read_nfc_data, write_nfc_data
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from nfcmagic import check_nfcid, register_nfc
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
        
        if response["action"] == "mark_completed":
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

@app.route("/check/nfc/<nfc_id>", methods=['GET'])
def check_nfcid_route(nfc_id):
    """Checks if a NFC ID matches a registered user based on a valid token.

    This endpoint processes POST requests containing a JSON payload with a 
    "token" field and an "nfc_id". It first verifies the validity of the 
    provided token. If valid, it proceeds to check if the given NFC ID matches
    a registered user by calling `check_nfcid`.
    
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
    token = get_token_from_header()
    if token and check_token(token, app, bcrypt):
        status, username, details = check_nfcid(app, nfc_id)
        # status = user found true/false
        if status:
            return jsonify({
                "status": "success", 
                "data": {
                    "login_id": username,
                    "full_name": details["full_name"],
                    "canvas_id": details["canvas_id"]
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

@app.route("/check/labs/<course_id>", methods=['GET'])
def check_labs_route(course_id):
    token = get_token_from_header()
    if token and check_token(token, app, bcrypt):
        state, data = get_course_assignments(course_id, token)
        if state:
            return jsonify({
                    "status": "success", 
                    "data": data
                }), 200
        else:
            return jsonify({
            "status": "failed", 
            "data": "An error occured when processing your request."
        }), data
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

@app.route("/register/nfc", methods=["POST"])
def register_nfc_route():
    response = request.json
    token = get_token_from_header()
    if token and check_token(token, app, bcrypt):
        # logic for registering a nfcid (serial no. of mifare card)
        json_payload = (response["nfc_id"], response["login_id"], response["course_id"])
        # here I want a validation check on the body before route logic

        response, data = register_nfc(token, json_payload, app, config_lock)
        if response == "registered":
            return jsonify({
                    "status": "success", 
                    "message": "NFC card successfully registered."
                }), 200
        elif response == "updated":
            return jsonify({
                "status": "success", 
                "message": "NFC card successfully updated on user."
            }), 200
        elif response == "conflict":
            return jsonify({
                "status": "failed",
                "message": "This NFC id is already registered.",
                "current_association": {
                    "login_id": data[0],
                    "full_name": data[1],
                    "nfc_id": data[2]
                }
            }), 409
        elif response == "error":
            return jsonify({
                "status": "error", 
                "message": "Failed to save the NFC ID due to a server error. Please try again later."
            }), 500
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
