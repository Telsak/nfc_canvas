def get_userinfo(app, nfc_id):
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
    for username, details in app.config['NFC_DATA'].items():
        if details["nfc_id"] == nfc_id:
            return True, (username, details)
    return False, (None, None)

def register_nfcid(token, json_payload, app, bcrypt, config_lock):
    # json_payload = (response["nfc_id"], response["user_id"], response["course_id"]) från main.py
    # check if the login_id already exists in the datastore
    # yes -> update the login_id with the new nfc_id if the nfc_id has changed
    # no -> do a canvas lookup on a course with the login_id to get the
    #       specific student_id and full name in canvas.
    # encrypt the student_id with cryptograhy.fernet (keep a key in a locked-down file)
    # save the nfc_id, full_name, f_student_id in nfc_users.json

    nfc_id, user_id, course_id = json_payload
    
    