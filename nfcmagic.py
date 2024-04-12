from config import write_nfc_data
from canvasmagic import get_student_info

def check_nfcid(app, nfc_id):
    """Retrieves user information associated with a given NFC ID.

    Searches for an NFC ID match. If a matching NFC ID is found,
    it returns a tuple indicating success and containing the username and
    user details. If no match is found, it returns a tuple indicating failure
    and containing None values.

    Args:
        app: The Flask application instance with NFC data in its configuration.
        nfc_id: A string representing the NFC ID to search for.

    Returns:
        A tuple containing:
        - A boolean indicating whether a matching NFC ID was found.
        - A tuple containing the username and a dictionary of details for the 
          matching user if found; otherwise, (None, None).
    """
    for username, details in app.config["NFC_DATA"].items():
        if details["nfc_id"] == nfc_id:
            return True, username, details
    return False, None, None

def check_userid(app, user_id):
    for username, _ in app.config["NFC_DATA"].items():
        if username == user_id:
            return True
    return False

def register_nfc(token, json_payload, app, bcrypt, config_lock):
    # json_payload = (response["nfc_id"], response["user_id"], response["course_id"]) från main.py
    # encrypt the student_id with cryptograhy.fernet (keep a key in a locked-down file)

    nfc_id, user_id, course_id = json_payload
    state, username, details = check_nfcid(app, nfc_id)
    if state:
        return "conflict", (username, details["full_name"], nfc_id)
    else:
        # nfc is free - but doesthe login_id already exists in the datastore?
        state = check_userid(app, user_id)
        if state:
            # yes -> update the login_id with the new nfc_id if the nfc_id has changed
            response = "updated"
        else:
            # no -> canvas scrape for information
            username, full_name = get_student_info(token, course_id, user_id)
            app.config["NFC_DATA"][user_id] = {"full_name": full_name}
            response = "registered"
        app.config["NFC_DATA"][user_id]["nfc_id"] = nfc_id

        # save the nfc_id, full_name, f_student_id in nfc_users.json
        state, _ = write_nfc_data(app.config['NFC_DATA'], app.config['SETTINGS']['base']['nfc_file'])
        if state:
            return response, None
        else:
            return "error", None
