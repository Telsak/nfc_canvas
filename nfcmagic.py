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
    for login_id, details in app.config["NFC_DATA"].items():
        if details["nfc_id"] == nfc_id:
            return True, login_id, details
    return False, None, None

def check_userid(app, login_id):
    for username, _ in app.config["NFC_DATA"].items():
        if username == login_id:
            return True
    return False

def register_nfc(token, json_payload, app, config_lock):                                          
    nfc_id, login_id, course_id = json_payload
    check_nfcid_result, username, details = check_nfcid(app, nfc_id)
    if check_nfcid_result:
        return "conflict", (username, details["full_name"], nfc_id)
    else:
        # nfc is free - but doesthe login_id already exists in the datastore?
        check_userid_result = check_userid(app, login_id)
        if not check_userid_result:
            # no -> canvas scrape for information
            # todo: also get canvas student_id and encrypt the student_id with cryptograhy.fernet
            # (keep a key in a locked-down file or environment variable)
            canvas_id, full_name, _ = get_student_info(token, course_id, login_id)

            app.config["NFC_DATA"][login_id] = {"full_name": full_name, "canvas_id": canvas_id}
            response = "registered"
        else:
            # yes -> update the login_id with the new nfc_id if the nfc_id has changed
            response = "updated"
        # both options change this add or modify this key
        app.config["NFC_DATA"][login_id]["nfc_id"] = nfc_id

        # save the nfc_id, full_name, f_student_id in nfc_users.json
        write_nfc_data_result, _ = write_nfc_data(app.config['NFC_DATA'], app.config['SETTINGS']['base']['nfc_file'])
        if write_nfc_data_result:
            return response, None
        else:
            return "error", None
